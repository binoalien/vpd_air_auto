# VPD Air Auto

## Overview

**VPD Air Auto** is a Home Assistant custom integration for HACS.

It automatically creates derived climate sensors for each Home Assistant device that exposes both:

- a temperature sensor, and
- a relative humidity sensor.

The integration is designed for indoor climate control, greenhouse environments, grow rooms, and general environmental monitoring.

## Derived sensors

VPD Air Auto can generate the following derived sensors:

| Sensor | Unit | Description |
| --- | --- | --- |
| VPDair | kPa | Vapor pressure deficit using air temperature |
| VPDleaf | kPa | Vapor pressure deficit using estimated leaf temperature |
| Absolute Humidity | g/m³ | Water vapor mass per air volume |
| Dew Point | °C | Temperature where condensation would begin |

Notes:

- **VPDleaf** uses a configurable leaf temperature offset.
- **Dew Point** uses Home Assistant's `temperature` device class.
- **Absolute Humidity** uses Home Assistant's `absolute_humidity` device class.

## 2.0.0 feature summary

Version 2.0.0 finalizes the V2 architecture and user workflows:

- V2 policy model for structured behavior control.
- **Global Defaults** for baseline behavior.
- **Area Policies** for per-area overrides.
- **Device Policies** for per-device overrides.
- **Source Overrides** for manual temperature/humidity source selection.
- Deterministic policy priority: **Device > Area > Global**.
- Robust migration from legacy V1 flat options to V2 structures.
- Non-destructive entity lifecycle behavior.
- Diagnostics 2.0 for improved troubleshooting visibility.
- Automatic duplicate protection for already-existing equivalent sensors.
- Stable manual source overrides during temporary `unknown` / `unavailable` states.

## Installation

### HACS custom repository

1. Open **HACS**.
2. Open **Integrations**.
3. Add this repository as a **custom repository** with category **Integration**.
4. Install **VPD Air Auto**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services** and add **VPD Air Auto**.

### Manual installation

Copy this folder into your Home Assistant configuration directory:

```text
custom_components/vpd_air_auto
```

Then restart Home Assistant and add **VPD Air Auto** from **Settings → Devices & services**.

## Compatibility

- Current release line: **2.0.0**.
- Minimum supported Home Assistant version is declared in `hacs.json`.
- Minimum supported HACS version is declared in `hacs.json`.
- No YAML configuration is supported.
- One integration instance only.

At the time of this release line, `hacs.json` declares Home Assistant `2026.4.0` and HACS `2.0.0`.

## Configuration

VPD Air Auto is configured through the Home Assistant UI (Options Flow).

### Global defaults

Configure integration-wide defaults:

- topology rescan interval
- enable/disable derived sensor kinds globally
- global VPDleaf offset
- global names/icons

### Area policies

Create area-level overrides:

- override enable flags and leaf offset per Home Assistant area
- selected through an Area selector
- unspecified values inherit from global defaults

### Device policies

Create device-level overrides:

- override enable flags and leaf offset per Home Assistant device
- selected through a Device selector
- unspecified values inherit from Area/Global values
- device policy wins over Area and Global

### Source overrides

Create optional manual source mappings:

- target selected through a Device selector
- optional temperature source entity
- optional humidity source entity
- partial override is allowed:
  - temperature only
  - humidity only
  - both
- if a manual override is temporarily `unknown` / `unavailable`, it remains selected when metadata is valid
- invalid manual override metadata falls back to automatic selection

## Policy priority

```text
Device Policy > Area Policy > Global Defaults
```

## Development container

This repository ships with a VS Code devcontainer inspired by the Home Assistant custom-component cookiecutter template. It provides a dedicated development container, a local Home Assistant instance on port `9123`, a debugpy attachment option, and VS Code tasks for starting Home Assistant and switching versions. See [`.devcontainer/README.md`](.devcontainer/README.md) for details.

## Development

This repository is structured as a standalone HACS custom integration repository.

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

Run Hassfest in CI through the included GitHub workflow.

## License

See [`LICENSE`](LICENSE).
