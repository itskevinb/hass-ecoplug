"""Switch platform for EcoPlug-protocol Wi-Fi outlets.

Modernized for Home Assistant 2024+ / Python 3.12+:
  - Uses SwitchEntity (SwitchDevice was removed in HA 0.110)
  - Drops dead imports (ATTR_HIDDEN, EVENT_TIME_CHANGED, ToggleEntity, etc.)
  - Provides DeviceInfo so the plug shows up under Devices & Services
  - Derives a stable name+unique_id from the MAC when the plug has no
    user-assigned name (i.e. it was never named in the WiOn / Eco Plug app)
  - Refactored to use entity attribute style (self._attr_*) — current HA idiom
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from pyecoplug import EcoDiscovery, EcoPlug

DOMAIN = "ecoplug"
MANUFACTURER = "EcoPlug (Wion/Workchoice/Woods/KAB)"
_LOGGER = logging.getLogger(__name__)


def _identify(plug: EcoPlug) -> tuple[str, str, str | None]:
    """Return (display_name, unique_id, mac_hex_or_None) for a discovered plug.

    The plug's name (data[3]) is whatever was entered in the WiOn / Eco Plug
    phone app. If it was never named there, the field is empty bytes — and
    every plug ends up colliding on the same empty unique_id. Fall back to
    the MAC stored at plug_data[-3] (same field pyecoplug treats as the MAC
    in its dedup map).
    """
    raw_name = (plug.name or "").strip()

    mac_hex: str | None = None
    try:
        mac_field = plug.plug_data[-3]
        if isinstance(mac_field, bytes):
            mac_hex = mac_field.hex().upper()
        elif isinstance(mac_field, str):
            mac_hex = mac_field.encode("utf-8", "ignore").hex().upper()
    except Exception:  # pragma: no cover - defensive
        pass

    if raw_name:
        display = raw_name
        uid = f"ecoplug_{raw_name}"
        return display, uid, mac_hex

    # Unnamed plug — derive from MAC. Format last 6 hex chars with colons for
    # the display name so it's still readable.
    if mac_hex:
        short = mac_hex[-6:]
        pretty = ":".join(short[i : i + 2] for i in range(0, 6, 2))
        return f"EcoPlug {pretty}", f"ecoplug_{mac_hex.lower()}", mac_hex

    return "EcoPlug (unnamed)", "ecoplug_unnamed", mac_hex


def setup_platform(
    hass: HomeAssistant,
    config: dict,
    add_entities: AddEntitiesCallback,
    discovery_info: Any | None = None,
) -> None:
    """Set up the EcoPlug switch platform via LAN discovery."""
    _LOGGER.info("EcoPlug platform setup; starting LAN discovery")
    entities: dict[str, EcoPlugSwitch] = {}

    def on_add(plug: EcoPlug) -> None:
        display, uid, mac_hex = _identify(plug)
        if uid in entities:
            return
        switch = EcoPlugSwitch(plug, display, uid, mac_hex)
        entities[uid] = switch
        try:
            add_entities([switch], True)
            _LOGGER.info("EcoPlug added: %s (uid=%s)", display, uid)
        except Exception:  # pragma: no cover - defensive
            _LOGGER.exception("EcoPlug add_entities failed for %s", display)

    def on_remove(plug: EcoPlug) -> None:
        _, uid, _ = _identify(plug)
        if uid in entities:
            _LOGGER.info("EcoPlug stale, marking unavailable: uid=%s", uid)
            entities[uid].mark_unavailable()
            # Don't delete from dict — keep slot so re-discovery doesn't dup.

    discovery = EcoDiscovery(on_add, on_remove)
    discovery.start()

    @callback
    def _stop(event):
        discovery.stop()

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, _stop)


class EcoPlugSwitch(SwitchEntity):
    """A single EcoPlug-protocol outlet exposed as a HA switch."""

    _attr_should_poll = True

    def __init__(
        self,
        plug: EcoPlug,
        display_name: str,
        unique_id: str,
        mac_hex: str | None,
    ) -> None:
        self._plug = plug
        self._attr_name = display_name
        self._attr_unique_id = unique_id
        self._attr_available = True
        self._mac_hex = mac_hex

        try:
            self._attr_is_on = bool(self._plug.is_on())
        except Exception:
            self._attr_is_on = False

        # Build DeviceInfo so each plug appears in Devices & Services.
        identifier = mac_hex or unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=display_name,
            manufacturer=MANUFACTURER,
            model="EcoPlug Wi-Fi Outlet",
        )

    def update(self) -> None:
        try:
            self._attr_is_on = bool(self._plug.is_on())
            self._attr_available = True
        except Exception as err:
            _LOGGER.debug("EcoPlug %s update failed: %s", self._attr_unique_id, err)
            self._attr_available = False

    def turn_on(self, **kwargs: Any) -> None:
        self._plug.turn_on()
        self._attr_is_on = True

    def turn_off(self, **kwargs: Any) -> None:
        self._plug.turn_off()
        self._attr_is_on = False

    def mark_unavailable(self) -> None:
        """Called by the discovery loop when a plug stops responding."""
        self._attr_available = False
        self.schedule_update_ha_state()
