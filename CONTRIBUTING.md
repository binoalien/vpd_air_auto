# Contributing

Thank you for considering a contribution to VPD Air Auto.

## Development setup

```bash
python -m pip install -r requirements_dev.txt
```

## Required checks

Run these before opening a pull request:

```bash
ruff check .
pylint custom_components/vpd_air_auto tests
pytest --cov=custom_components.vpd_air_auto --cov-report=term-missing
```

## Pull requests

Please include:

- a clear description of the change
- tests for behavior changes
- documentation updates when user-visible behavior changes

## Release notes

User-visible changes should be added to `CHANGELOG.md`.
