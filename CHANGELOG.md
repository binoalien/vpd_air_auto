# Changelog

All notable changes to VPD Air Auto are documented in this file.

## Unreleased

### Added

- Expanded diagnostics payloads with policy repository data, effective per-device policy metadata, and per-device entity-plan details including blocked sensor kinds.
- Added diagnostics fields for device-level effective policy and entity-plan details.

### Changed

- Updated README for V2 scoped policy architecture, options-flow menus, and source-override behavior.
- Extended backend translations (English/German) for scoped options-flow steps and validation messages.

### Removed

- Removed obsolete V1-only documentation language in favor of V2 scoped configuration terminology.

## 1.5.13

### Changed

- Fix pylint errors in test_sensor.py.
