# VPD Air Auto

## Overview

VPD Air Auto is a Home Assistant custom integration distributed through HACS. It automatically creates derived climate sensors for devices that expose both temperature and relative humidity. The integration is designed for indoor climate monitoring, greenhouse and grow-room automation, and general environmental monitoring use cases.

## Derived sensors

VPD Air Auto can create the following derived sensors for each eligible device:

| Sensor | Unit | Description |
| --- | --- | --- |
| VPDair | kPa | Vapor pressure deficit using air temperature |
| VPDleaf | kPa | Vapor pressure deficit using estimated leaf temperature |
| Absolute Humidity | g/m³ | Water vapor mass per air volume |
| Dew Point | °C | Temperature where condensation would begin |

Notes:

- **VPDleaf** uses a configurable leaf temperature offset.
- **Dew Point** sensors use Home Assistant's `temperature` device class.
- **Absolute Humidity** sensors use Home Assistant's `absolute_humidity` device class.

## 2.0.0 feature summary

The 2.0.0 release line finalizes the V2 architecture:

- V2 policy model with hierarchical policy scopes.
- **Global Defaults** for baseline behavior.
- **Area Policies** for area-level overrides.
- **Device Policies** for device-level overrides.
- **Source Overrides** for manual source-entity selection per device.
- Deterministic policy priority: **Device > Area > Global**.
- Robust migration from V1 flat options to the V2 structure.
- Non-destructive entity lifecycle behavior (no destructive churn during topology/policy changes).
- Diagnostics 2.0 with expanded troubleshooting context.
- Automatic duplicate protection when equivalent sensors already exist.
- Stable manual source overrides when overridden entities are temporarily `unknown` or `unavailable` (as long as entity metadata remains valid).

## Installation

### HACS (custom repository)

1. Open HACS.
2. Open **Integrations**.
3. Add this repository as a **custom repository** with category **Integration**.
4. Install **VPD Air Auto**.
5. Restart Home Assistant.
6. Add the integration from **Settings → Devices & services**.

### Manual installation

Copy this repository's integration folder into your Home Assistant config directory:

```text
custom_components/vpd_air_auto
```

Restart Home Assistant, then add **VPD Air Auto** from **Settings → Devices & services**.

## Compatibility

- Current release line: **2.0.0**.
- Minimum supported Home Assistant version is declared in `hacs.json`.
- Minimum supported HACS version is declared in `hacs.json`.
- YAML configuration is not supported.
- Only one integration instance is supported.

At the time of 2.0.0, the repository metadata currently declares Home Assistant `2026.4.0` and HACS `2.0.0` in `hacs.json`.

## Configuration

Configuration is UI-only (Options Flow, V2 menu).

### Global defaults

Use **Global defaults** to configure:

- Topology rescan interval.
- Global enable/disable flags for derived sensor kinds.
- Global VPDleaf temperature offset.
- Global names and icons for derived sensors.

### Area policies

Use **Area policies** to:

- Override enable flags and leaf offset for a selected Home Assistant area.
- Select the target via the Area selector.
- Leave unspecified values inherited from Global defaults.

### Device policies

Use **Device policies** to:

- Override enable flags and leaf offset for a selected Home Assistant device.
- Select the target via the Device selector.
- Inherit unspecified values from Area policy (if present) and then Global defaults.
- Apply the highest policy priority among all scopes.

### Source overrides

Use **Source overrides** to choose manual source entities for a target device:

- Target device is selected through a Device selector.
- `temperature_entity_id` is optional.
- `humidity_entity_id` is optional.
- Partial override is supported:
  - temperature only
  - humidity only
  - both
- If a manual override entity is temporarily `unknown` or `unavailable`, it remains selected when entity metadata is still valid.
- If a manual override becomes invalid, source selection falls back to automatic discovery.

## Policy priority

```text
Device Policy > Area Policy > Global Defaults
```

## Development container

This repository includes a VS Code devcontainer setup inspired by the Home Assistant custom-component cookiecutter template. See [`.devcontainer/README.md`](.devcontainer/README.md) for details.

## Development

Runtime code:

```text
custom_components/vpd_air_auto/
```

Tests:

```text
tests/
```

Install dependencies:

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
