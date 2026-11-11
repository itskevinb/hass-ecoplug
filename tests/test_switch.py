"""Re-discovery swaps the fresh EcoPlug into the existing entity."""
import sys
import types
from unittest.mock import MagicMock

# Minimal Home Assistant stubs so switch.py imports without HA installed.
for mod in ("homeassistant", "homeassistant.components", "homeassistant.components.switch",
            "homeassistant.const", "homeassistant.core", "homeassistant.helpers",
            "homeassistant.helpers.device_registry", "homeassistant.helpers.entity_platform"):
    sys.modules.setdefault(mod, types.ModuleType(mod))
sys.modules["homeassistant.components.switch"].SwitchEntity = type("SwitchEntity", (), {})
sys.modules["homeassistant.const"].EVENT_HOMEASSISTANT_STOP = "stop"
sys.modules["homeassistant.core"].HomeAssistant = object
sys.modules["homeassistant.core"].callback = lambda f: f
sys.modules["homeassistant.helpers.device_registry"].DeviceInfo = dict
sys.modules["homeassistant.helpers.entity_platform"].AddEntitiesCallback = object

sys.path.insert(0, "custom_components")
from ecoplug import switch  # noqa: E402


def _plug(ip):
    plug = MagicMock()
    plug.name = "amp"
    plug.plug_data = (b"mac", ip.encode(), 80)
    plug.is_on.return_value = True
    return plug


def test_rediscovered_plug_replaces_stale_one(monkeypatch):
    captured = {}

    class FakeDiscovery:
        def __init__(self, on_add, on_remove):
            captured["on_add"], captured["on_remove"] = on_add, on_remove

        def start(self):
            pass

    monkeypatch.setattr(switch, "EcoDiscovery", FakeDiscovery)
    added = []
    hass = MagicMock()
    switch.setup_platform(hass, {}, lambda ents, _update: added.extend(ents))

    old, new = _plug("10.10.10.174"), _plug("10.10.10.200")
    captured["on_add"](old)
    entity = added[0]
    entity.schedule_update_ha_state = MagicMock()
    captured["on_remove"](old)
    captured["on_add"](new)

    assert len(added) == 1
    assert entity._plug is new
    entity.update()
    new.is_on.assert_called()
    assert entity._attr_available is True
