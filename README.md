# VPD Air Auto

## Overview

VPD Air Auto is a Home Assistant custom integration for HACS. It automatically creates derived climate sensors for devices that expose both temperature and relative humidity. It is designed for indoor climate monitoring, greenhouse automation, grow-room management, and general environmental monitoring.

## Derived sensors

When a compatible device is discovered, VPD Air Auto can create the following derived sensors:

| Sensor | Unit | Description |
| --- | --- | --- |
| VPDair | kPa | Vapor pressure deficit using air temperature |
| VPDleaf | kPa | Vapor pressure deficit using estimated leaf temperature |
| Absolute Humidity | g/m³ | Water vapor mass per air volume |
| Dew Point | °C | Temperature where condensation would begin |

Notes:

- **VPDleaf** uses a configurable leaf temperature offset.
- **Dew Point** is exposed with the Home Assistant `temperature` device class.
- **Absolute Humidity** is exposed with the Home Assistant `absolute_humidity` device class.

## 2.0.0 feature summary

The 2.0.0 release line finalizes the V2 architecture:

- V2 policy model with explicit scope-based behavior.
- **Global Defaults** for baseline behavior and display values.
- **Area Policies** for area-scoped overrides.
- **Device Policies** for per-device overrides.
- **Source Overrides** for manual temperature/humidity source selection per device.
- Deterministic policy priority: **Device > Area > Global**.
- Robust migration from V1 flat options into the V2 options structure.
- Non-destructive entity lifecycle behavior.
- Diagnostics 2.0 with policy/source/entity-plan visibility.
- Automatic duplicate protection when equivalent sensors already exist.
- Stable manual source override selection during temporary `unknown`/`unavailable` source states when metadata remains valid.

## Installation

## HACS (recommended)

1. Open **HACS** in Home Assistant.
2. Open **Integrations**.
3. Add this repository as a **custom repository** with category **Integration**.
4. Install **VPD Air Auto**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services** and add **VPD Air Auto**.

## Manual installation

1. Copy this repository's integration folder into your Home Assistant configuration directory:

   ```text
   custom_components/vpd_air_auto
   ```

2. Restart Home Assistant.
3. Go to **Settings → Devices & services** and add **VPD Air Auto**.

## Compatibility

- Current release line: **2.0.0**.
- Minimum supported Home Assistant and HACS versions are declared in [`hacs.json`](hacs.json).
- No YAML configuration is supported.
- Only one integration instance is allowed.

At the time of this release line, `hacs.json` declares:

- Home Assistant `2026.4.0`
- HACS `2.0.0`

## Configuration

VPD Air Auto is configured through the Home Assistant UI (V2 Options Flow).

### Global defaults

Global defaults define integration-wide baseline behavior:

- Topology rescan interval
- Global enable/disable flags for each derived sensor kind
- Global VPDleaf offset
- Global names and icons for each derived sensor kind

### Area policies

Area policies allow per-area overrides:

- Override enable flags and VPDleaf offset per Home Assistant area
- Area is selected using an Area selector
- Unspecified values inherit from Global Defaults

### Device policies

Device policies allow per-device overrides:

- Override enable flags and VPDleaf offset per Home Assistant device
- Device is selected using a Device selector
- Unspecified values inherit from Area Policy and then Global Defaults
- Device policy wins over Area and Global

### Source overrides

Source overrides define manual input source entities for a specific target device:

- Target is selected using a Device selector
- Optional temperature source entity
- Optional humidity source entity
- Partial override is supported:
  - temperature only
  - humidity only
  - both
- If a manual override source is temporarily `unknown`/`unavailable`, the override remains selected when metadata is still valid
- Invalid manual override input automatically falls back to integration auto-selection

## Policy priority

```text
Device Policy > Area Policy > Global Defaults
```

## Development container

This repository ships with a VS Code devcontainer inspired by the Home Assistant custom-component cookiecutter template. It includes a dedicated development container, a local Home Assistant instance on port `9123`, debugpy attach support, and VS Code tasks for starting Home Assistant and switching versions. See [`.devcontainer/README.md`](.devcontainer/README.md).

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
