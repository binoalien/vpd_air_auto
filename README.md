# VPD Air Auto

VPD Air Auto is a Home Assistant custom integration for HACS. It discovers devices that expose both temperature and relative-humidity sources and creates derived climate helper sensors.

Derived sensors:

| Sensor kind | Default name | Unit |
| --- | --- | --- |
| air | VPDair | kPa |
| leaf | VPDleaf | kPa |
| absolute_humidity | Absolute Humidity | g/m³ |
| dew_point | Dew Point | °C |

## V2 highlights

- Single config entry with scoped policy layers:
  - Global defaults
  - Area policy overrides
  - Device policy overrides
- Strict precedence: **Device > Area > Global**.
- Optional per-device source overrides for temperature/humidity entity selection.
- Duplicate detection to avoid creating sensors already provided by other integrations.
- Diagnostics payloads for topology, policy resolution, and entity planning.

## Setup

Install through HACS (recommended) or copy `custom_components/vpd_air_auto` manually into your Home Assistant config directory, restart Home Assistant, then add **VPD Air Auto** from **Settings → Devices & services**.

## Configuration model

Configuration is UI-only (no YAML).

### Global defaults

From Options → **Global defaults**:
- topology rescan interval
- enable/disable each derived sensor kind
- global names/icons for each kind
- global VPD leaf offset

### Area policies

From Options → **Area policies**:
- add/edit/delete area overrides
- override sensor kind enablement
- override leaf offset

### Device policies

From Options → **Device policies**:
- add/edit/delete device overrides
- override sensor kind enablement
- override leaf offset

### Source overrides

From Options → **Source overrides**:
- add/edit/delete per-device manual source selection
- optional `temperature_entity_id`
- optional `humidity_entity_id`

## Diagnostics

Integration and device diagnostics include:
- discovered topology and snapshots
- blocked/creatable/enabled sensor kinds
- policy repository content
- effective per-device policy and source attribution

## Development

```bash
python -m pip install -r requirements_dev.txt
ruff check .
pylint custom_components/vpd_air_auto tests
pytest --cov=custom_components.vpd_air_auto --cov-report=term-missing
```

## License

See [`LICENSE`](LICENSE).
