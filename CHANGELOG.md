# Changelog

All notable changes to VPD Air Auto are documented in this file.

## 2.0.0 (unreleased)

### Added

- Add release-readiness QA tests for translation parity, required translation error keys, and release metadata consistency.

### Changed

- Finalize README documentation for the 2.0.0 V2 policy model, derived sensors, compatibility, installation, and configuration guidance.
- Finalize English and German translations for source override validation errors and consistent Area/Device/Source Override wording.
- Expand 2.0.0 release notes to summarize hardening outcomes across policy resolution, migrations, diagnostics, source override behavior, and non-destructive entity lifecycle behavior.

### Fixed

- Close translation coverage gaps for source override validation messages (`invalid_scope_id`, invalid source entity IDs, and missing source override input).


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
