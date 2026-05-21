# Changelog

All notable changes to VPD Air Auto are documented in this file.

## 2.0.0 (unreleased)

### Changed

- Finalize V2 documentation and options-flow translations for menu-based Global/Area/Device policy editing and source overrides.
- Extend diagnostics payloads with repository policy data, effective per-device policy values including source metadata, area context, and per-device entity plans (enabled/blocked/creatable kinds).
- Remove obsolete V1-oriented docs descriptions in favor of V2 architecture behavior.


## 1.5.13

### Changed

- Fix pylint errors in test_sensor.py.

## 1.5.12

### Changed

- Bump integration version to `1.5.12`.

## 1.5.11

### Changed

- Clean up and normalize this changelog structure by removing duplicated headings and keeping entries in consistent order.

## 1.5.5

### Fixed

- Fixed the VS Code devcontainer build by removing the inherited Yarn APT repository before `apt-get update`, preventing `NO_PUBKEY 62D54FD4003F6525` failures.

## 1.5.2

### Added

- Add a VS Code devcontainer with dedicated Home Assistant tasks, debug support and local configuration.
- Add `.devcontainer/README.md`, `.vscode/tasks.json` and `.vscode/launch.json`.
- Add `homeassistant` and `debugpy` to `requirements_dev.txt` for local development.

### Changed

- Keep the HACS standalone repository layout from 1.5.1 while improving the developer experience.

## 1.5.1

### Changed

- Align repository layout with HACS custom integration expectations.
- Keep runtime code under `custom_components/vpd_air_auto/`.
- Keep tests directly under `tests/` for standalone custom-repository development.
- Add HACS-oriented root metadata, GitHub workflows and contribution files.
- Remove Core-repository assumptions such as `strings.json` usage.
- Keep backend translations under `custom_components/vpd_air_auto/translations/`.

## 1.5.0

### Changed

- Initial standalone HACS repository template.

## 1.4.x

### Added

- Dew Point derived sensor.
- Absolute Humidity derived sensor.
- VPDleaf support with configurable leaf temperature offset.
- Global sensor display-name and icon options.
- Duplicate detection for existing device sensors.
- Diagnostics support.
- Test coverage for calculations, config flow, coordinator, diagnostics, options and sensors.
