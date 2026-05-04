# VPD Air Auto

VPD Air Auto is a Home Assistant custom integration for HACS. It automatically creates derived climate sensors for each Home Assistant device that exposes both a temperature sensor and a relative humidity sensor.

Derived sensors:

| Sensor | Unit | Device class |
| --- | --- | --- |
| VPDair | kPa | none |
| VPDleaf | kPa | none |
| Absolute Humidity | g/m³ | `absolute_humidity` |
| Dew Point | °C | `temperature` |

## Features

- UI setup through Home Assistant config flow.
- Global options for enabling or disabling each derived sensor type.
- Global display names and icons for every derived sensor type.
- Configurable VPDleaf temperature offset.
- Automatic device discovery based on existing temperature and humidity sensors.
- Duplicate protection when a device already exposes equivalent sensors.
- Diagnostics support for troubleshooting.
- English and German backend translations.

## HACS installation

1. Open HACS.
2. Open **Integrations**.
3. Add this repository as a custom repository with category **Integration**.
4. Install **VPD Air Auto**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration** and add **VPD Air Auto**.

## Manual installation

Copy this folder into your Home Assistant configuration directory:

```text
custom_components/vpd_air_auto
```

Then restart Home Assistant and add **VPD Air Auto** from **Settings → Devices & services**.

## Configuration

The integration is configured entirely through the Home Assistant UI. YAML configuration is not supported.

Available global options:

- Topology rescan interval
- Enable/disable VPDair sensors
- Enable/disable VPDleaf sensors
- Enable/disable Absolute Humidity sensors
- Enable/disable Dew Point sensors
- VPDair display name and icon
- VPDleaf display name and icon
- Absolute Humidity display name and icon
- Dew Point display name and icon
- VPDleaf temperature offset in °C

## Compatibility

The minimum supported Home Assistant version is declared in `hacs.json`.

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

This now includes `homeassistant` itself so the repository can be used directly inside the included devcontainer or a local virtual environment.

Run checks:

```bash
ruff check .
pylint custom_components/vpd_air_auto tests
pytest --cov=custom_components.vpd_air_auto --cov-report=term-missing
```

Run Hassfest in CI through the included GitHub workflow.

## License

See [`LICENSE`](LICENSE).
