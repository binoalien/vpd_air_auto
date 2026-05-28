# Changelog

All notable changes to VPD Air Auto are documented in this file.

## 2.0.0 (unreleased)

### Added

- V2 policy architecture with explicit Global Defaults, Area Policies and Device Policies.
- Source Override support for manual temperature/humidity source binding per target device.
- Dew Point and Absolute Humidity derived sensor support in the V2 options and policy model.
- Diagnostics 2.0 payload sections for policy repository state, effective device policy resolution and per-device entity planning.
- Translation coverage for menu-based V2 Options Flow editing across global, area, device and source-override scopes.

### Changed

- Finalized option-flow UX as a menu-based V2 model (`global_defaults`, `area_policies`, `device_policies`, `source_overrides`).
- Hardened policy and options parsing against malformed stored values while preserving valid data where possible.
- Finalized source-selection semantics so valid manual overrides remain stable through temporary `unknown` / `unavailable` states.
- Finalized deterministic policy precedence: **Device Policy > Area Policy > Global Defaults**.
- Finalized non-destructive entity lifecycle behavior to prevent unnecessary entity churn when policy/source states fluctuate.
- Expanded release documentation for 2.0.0 installation, compatibility, configuration and policy behavior.

### Fixed

- Improved duplicate-protection behavior to avoid creating equivalent derived sensors when matching sensors already exist on a device.
- Improved migration handling from legacy V1 flat options to V2 policy structures.
- Improved diagnostics clarity for blocked entity creation reasons and source/policy decision traces.

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
