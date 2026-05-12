# EcoPlug — Home Assistant integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integration for **EcoPlug protocol** Wi-Fi outlets, sold under several brand names:

- **WiOn** (50049, 50050, 50055, etc.)
- **Workchoice** (e.g. RC-032W)
- **Woods**
- **KAB**

These are all the same ESP8266-based outlet running stock EcoPlug firmware. The integration does
**local LAN discovery and control** over UDP — no cloud, no broker, the Eco Plug / WiOn phone app
is only needed once for initial Wi-Fi onboarding.

> **If your plug uses the Smart Life / Tuya app instead, this is not the right integration.** Use
> Home Assistant's first-class Tuya integration for those.

## What's new in this fork

The original [`gbealmer/pyecoplug`](https://github.com/gbealmer/pyecoplug) integration hasn't been
updated in years and doesn't load on modern HA. This fork:

- ✅ Modernized for **Home Assistant 2024+ / Python 3.12+** (`SwitchEntity` instead of the long-removed
  `SwitchDevice`, dropped dead `ATTR_HIDDEN` / `EVENT_TIME_CHANGED` imports)
- ✅ Added required **`version` and `iot_class`** to `manifest.json` (HA refuses custom integrations
  without these)
- ✅ **MAC-based fallback naming** — if the plug has no name set in the WiOn app, it now appears as
  `EcoPlug AA:BB:CC` instead of an empty `switch.` entity that collides with other unnamed plugs
- ✅ **`DeviceInfo`** so each plug shows up properly under Devices & Services
- ✅ **`hacs.json`** for HACS custom-repository install
- ✅ Improved logging — discovery and add/remove are now visible at INFO

## Installation

### Via HACS (recommended)

1. HACS → ⋮ → Custom repositories → add `https://github.com/itskevinb/hass-ecoplug` as type **Integration**
2. Search HACS for "EcoPlug" → Download
3. Restart Home Assistant
4. Add to `configuration.yaml`:
   ```yaml
   switch:
     - platform: ecoplug
       scan_interval: 10
   ```
5. Restart Home Assistant again. Plugs on the LAN are auto-discovered as switches.

### Manual

1. Copy `custom_components/ecoplug/` into your HA `/config/custom_components/`
2. Add the `switch:` block above to `configuration.yaml`
3. Restart HA

## Network requirements

- The plugs and the Home Assistant host **must be on the same broadcast domain** (same VLAN/subnet).
  Discovery is UDP broadcast to `255.255.255.255:5888`. UDP broadcasts don't cross VLANs.
- The HA host listens on UDP `8900` for discovery responses.
- If your plugs are on an IoT VLAN and HA isn't on that VLAN, you'll need either: (a) HA running a
  NIC on the IoT VLAN, or (b) some other way to bridge the broadcasts (e.g. UDM Pro "DHCP Relay" or
  custom UDP forwarders).

## Limitations (unchanged from upstream)

- No energy monitoring, even on plugs that have the chip.
- No HA UI config flow yet — switch is declared in YAML.
- Discovery requires LAN broadcast (see Network requirements above).

## Acknowledgments

- Upstream library [`philburr/pyecoplug`](https://github.com/philburr/pyecoplug) — reverse-engineered
  the EcoPlug protocol.
- [`gbealmer/pyecoplug`](https://github.com/gbealmer/pyecoplug) — original HA `custom_component`
  wrapper that this fork builds on.
