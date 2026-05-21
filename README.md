# VPD Air Auto

VPD Air Auto is a Home Assistant custom integration for HACS. It discovers devices that provide both temperature and relative humidity sources and creates derived helper sensors.

Derived sensors:

| Sensor | Unit | Device class |
| --- | --- | --- |
| VPDair | kPa | none |
| VPDleaf | kPa | none |
| Absolute Humidity | g/m³ | `absolute_humidity` |
| Dew Point | °C | `temperature` |

## Features

- Single config entry architecture.
- Automatic topology discovery (temperature + humidity pairs).
- Scoped V2 policy model: **Device > Area > Global**.
- Global defaults for enable flags, naming/icons, and VPDleaf offset.
- Area and device behavior policies (enable flags + leaf offset).
- Optional per-device source overrides for temperature/humidity entity IDs.
- Duplicate detection to avoid creating helpers that already exist.
- Diagnostics payloads for policy/effective-policy/entity-plan troubleshooting.
- Backend translations in English and German.

## Installation

### HACS
1. Open HACS.
2. Open **Integrations**.
3. Add this repository as a custom repository with category **Integration**.
4. Install **VPD Air Auto**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration** and add **VPD Air Auto**.

### Manual
Copy this folder into your Home Assistant configuration directory:

```text
custom_components/vpd_air_auto
```

Then restart Home Assistant and add **VPD Air Auto** from **Settings → Devices & services**.

## Configuration and Options (V2)

All configuration is handled in the Home Assistant UI (no YAML).

Options flow menu:
- Global Defaults
- Area Policies
- Device Policies
- Source Overrides

### Global Defaults
- Topology rescan interval
- Enable/disable each derived sensor kind
- Global names/icons for each derived sensor kind
- Global VPDleaf temperature offset

### Area Policies
Per-area overrides for:
- enable/disable each derived sensor kind
- leaf temperature offset

### Device Policies
Per-device overrides for:
- enable/disable each derived sensor kind
- leaf temperature offset

### Source Overrides (optional)
Per-device manual source overrides:
- `temperature_entity_id`
- `humidity_entity_id`

When an override is set, the selected source is used for that device during discovery/snapshot building.

## Diagnostics

Config entry diagnostics include:
- resolved options
- tracked source entities
- discovered topology and snapshots
- stored policy repository data (global/area/device/source overrides)
- effective resolved policy per device
- entity planning per device (`enabled_kinds`, `blocked_sensor_kinds`, `creatable_kinds`)

Device diagnostics include device-specific topology, snapshot, effective policy, and entity-plan information.

## Development

Runtime code:

```text
custom_components/vpd_air_auto/
```

Tests:

```text
tests/
```

Install development dependencies:

```bash
python -m pip install -r requirements_dev.txt
```

Run checks:

```bash
ruff check .
pylint custom_components/vpd_air_auto tests
pytest --cov=custom_components.vpd_air_auto --cov-report=term-missing
```

## License

See [`LICENSE`](LICENSE).
