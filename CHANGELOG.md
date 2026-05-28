# Changelog

All notable changes to VPD Air Auto are documented in this file.

## 2.0.0

### Added

- Release-readiness QA tests for English/German translation key parity.
- Translation QA checks for required release-critical errors/aborts used by config/options flows.
- Release metadata consistency checks covering `manifest.json` version and required HACS metadata presence.
- Release-gate workflow QA checks for required CI and Hassfest triggers/commands.

### Changed

- Finalized README documentation for the 2.0.0 user experience: derived sensors, V2 policy model, source overrides, compatibility, installation, and policy priority.
- Documented migration and lifecycle expectations for ConfigEntry schema v2, stable unique IDs, and non-destructive registry handling.
- Finalized troubleshooting guidance for Diagnostics 2.0 (`source_selection`, policy sources, entity plan, and not-created reasons).
- Finalized English and German translation wording consistency for Area Policies, Device Policies, and Source Overrides.
- Before tagging `v2.0.0`, verify the latest `main` branch shows CI success and Hassfest success.

### Fixed

- Closed translation coverage gaps for source override validation (`invalid_scope_id`, invalid source entity IDs, and missing source override input).
- Aligned source override field labels in edit/add flows to consistently describe source entities.

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
