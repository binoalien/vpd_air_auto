# Development container

This project includes a VS Code devcontainer inspired by the Home Assistant integration blueprint and the custom-component cookiecutter approach. The entry file is `.devcontainer.json` in the repository root, while helper scripts live under `.devcontainer/`.

## What it provides

- A dedicated Python development container for the repository
- Local installation of the development and test dependencies from `requirements_dev.txt`
- A local Home Assistant instance using `.devcontainer/config/configuration.yaml`
- VS Code tasks to run Home Assistant, validate the configuration, and switch Home Assistant versions
- Optional debugpy-based debugging on port `5678`

## How to use it

1. Open the repository in VS Code.
2. Choose **Reopen in Container**.
3. Once the container has finished building, run one of the tasks from **Terminal → Run Task**.

## Configuration directory

The Home Assistant config directory used for the devcontainer is `.devcontainer/config/`.
A symlink named `custom_components` is created there automatically and points back to the repository `custom_components/` folder.

This keeps the repository ready for HACS while still allowing Home Assistant to load the local custom integration during development.


## Troubleshooting

If `Reopen in Container` fails during `apt-get update` with a `NO_PUBKEY` error for `dl.yarnpkg.com`, the Dockerfile already removes the inherited Yarn APT source before package installation. If you opened an older container definition first, rebuild with **Dev Containers: Rebuild Without Cache**.


## Python and Home Assistant versioning

This devcontainer targets Python 3.14 and installs Home Assistant 2026.4.2 by default.
If you change the Home Assistant version, keep it aligned with the Python requirement declared on PyPI.
