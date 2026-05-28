# VPD Air Auto

## Overview

**VPD Air Auto** is a Home Assistant custom integration for HACS.
It automatically creates derived climate sensors for Home Assistant devices that expose **both** temperature and relative humidity.

It is designed for indoor climate monitoring, greenhouse/grow-room operation, and general environmental monitoring.

## Derived sensors

The integration can generate the following derived sensors per eligible device:

| Sensor | Unit | Description |
| --- | --- | --- |
| VPDair | kPa | Vapor pressure deficit calculated from air temperature |
| VPDleaf | kPa | Vapor pressure deficit calculated from estimated leaf temperature |
| Absolute Humidity | g/m³ | Water vapor mass per cubic meter of air |
| Dew Point | °C | Temperature at which condensation starts |

Notes:
- **VPDleaf** uses a configurable leaf temperature offset.
- **Dew Point** uses the Home Assistant `temperature` device class.
- **Absolute Humidity** uses the Home Assistant `absolute_humidity` device class.

## 2.0.0 feature summary

The 2.0.0 release line introduces a finalized policy-based architecture:

- V2 policy model with hierarchical scopes.
- **Global Defaults** for integration-wide behavior.
- **Area Policies** for area-level overrides.
- **Device Policies** for device-level overrides.
- **Source Overrides** for manually selecting source entities per device.
- Deterministic policy priority: **Device > Area > Global**.
- Robust migration from legacy V1 flat options to V2 storage.
- Non-destructive entity lifecycle behavior (safe add/remove decisions).
- Diagnostics 2.0 with policy and source decision visibility.
- Automatic duplicate protection against equivalent pre-existing entities.
- Stable manual source overrides when selected entities are temporarily `unknown`/`unavailable` and still metadata-valid.

## Installation

### HACS (custom repository)

1. Open **HACS**.
2. Open **Integrations**.
3. Add this repository as a **Custom repository** with category **Integration**.
4. Install **VPD Air Auto**.
5. Restart Home Assistant.
6. Add the integration via **Settings → Devices & services**.

### Manual installation

Copy the integration folder into your Home Assistant configuration directory:

```text
custom_components/vpd_air_auto
```

Then restart Home Assistant and add **VPD Air Auto** via **Settings → Devices & services**.

## Compatibility

- Current release line: **2.0.0**.
- Minimum Home Assistant version is declared in `hacs.json`.
- Minimum HACS version is declared in `hacs.json`.
- YAML configuration is **not** supported.
- One integration instance only.

## Configuration

The integration is configured entirely through the Home Assistant UI (V2 Options Flow).

### Global defaults

Global defaults configure baseline behavior:

- topology rescan interval
- enable/disable each derived sensor kind globally
- global VPDleaf offset
- global sensor names and icons

### Area policies

Area policies provide per-area overrides:

- override enable flags and leaf offset for a selected Home Assistant area
- selected via an **Area selector**
- unspecified values inherit from Global Defaults

### Device policies

Device policies provide per-device overrides:

- override enable flags and leaf offset for a selected Home Assistant device
- selected via a **Device selector**
- unspecified values inherit from Area/Global
- device policy always wins over area/global

### Source overrides

Source overrides allow manual source mapping per target device:

- target selected via a **Device selector**
- optional manual temperature source entity
- optional manual humidity source entity
- partial override is supported:
  - temperature only
  - humidity only
  - both
- manual override remains selected when entity state is temporarily `unknown`/`unavailable` but metadata is still valid
- invalid manual override automatically falls back to auto-selection

## Policy priority

```text
Device Policy > Area Policy > Global Defaults
```

## Diagnostics and troubleshooting

Diagnostics 2.0 includes:

- repository policy data snapshots
- effective per-device policy values
- area context visibility
- source selection metadata
- per-device entity plans (enabled / blocked / creatable)

This helps validate policy and source behavior without changing runtime data.

## Development

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
