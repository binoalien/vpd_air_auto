# VPD Air Auto

VPD Air Auto is a Home Assistant custom integration for HACS. It discovers devices that expose both a temperature and humidity source entity and creates derived helper sensors per device.

Derived sensors:

| Sensor kind | Default name | Unit |
| --- | --- | --- |
| air | VPDair | kPa |
| leaf | VPDleaf | kPa |
| absolute_humidity | Absolute Humidity | g/m³ |
| dew_point | Dew Point | °C |

## V2 highlights

- Single config entry architecture (one integration instance).
- Declarative sensor-kind runtime.
- Scoped policy model with **Device > Area > Global** priority.
- Source override support per device (`temperature_entity_id` / `humidity_entity_id`).
- Diagnostics payloads with topology, snapshots, effective policy and entity planning.

## Configuration model

The integration remains UI-only (no YAML).

### Global defaults

In **Options → Global defaults**:
- topology rescan interval
- global enable/disable toggles for each sensor kind
- global display names and icons
- global leaf offset

### Area policies

In **Options → Area policies**:
- add/edit/delete area-specific behavior overrides
- override enable toggles and leaf offset for all devices in an area

### Device policies

In **Options → Device policies**:
- add/edit/delete device-specific behavior overrides
- highest priority behavior scope

### Source overrides

In **Options → Source overrides**:
- add/edit/delete per-device source overrides
- optionally force temperature and/or humidity source entity IDs

## Diagnostics

Config entry diagnostics include:
- resolved options
- tracked source entities
- discovered topology and current snapshots
- policy repository view (global/area/device/source overrides)
- effective policy per device including source metadata
- entity plan per device (`enabled_kinds`, `blocked_sensor_kinds`, `creatable_kinds`)

Device diagnostics include the same data scoped to one Home Assistant device.

## Installation & development

### HACS
1. Add repository as custom integration in HACS.
2. Install **VPD Air Auto**.
3. Restart Home Assistant.
4. Add the integration from **Settings → Devices & services**.

### Manual
Copy `custom_components/vpd_air_auto` into your Home Assistant config and restart.

### Local checks
```bash
ruff check .
pylint custom_components/vpd_air_auto tests
pytest --cov=custom_components.vpd_air_auto --cov-report=term-missing
```

## License

See [`LICENSE`](LICENSE).
