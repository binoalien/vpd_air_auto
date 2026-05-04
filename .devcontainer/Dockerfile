FROM mcr.microsoft.com/devcontainers/python:3.14-bookworm

# The base devcontainers Python image can include an APT source for Yarn.
# If that repository key is missing or stale, `apt-get update` fails with
# a NO_PUBKEY error during "Reopen in Container". Yarn is not required for
# this Home Assistant custom component, so remove that source before APT
# operations to keep the container build deterministic.
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn*.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libffi-dev \
        libjpeg-dev \
        libssl-dev \
        zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
