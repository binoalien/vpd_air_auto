"""Diagnostics support for VPD Air Auto."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from . import VpdAirConfigEntry

_TO_REDACT: set[str] = set()


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: VpdAirConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return async_redact_data(
        {
            "entry": {
                "entry_id": entry.entry_id,
                "title": entry.title,
                "version": entry.version,
                "minor_version": entry.minor_version,
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            "coordinator": coordinator.diagnostics_payload(),
        },
        _TO_REDACT,
    )


async def async_get_device_diagnostics(
    hass: HomeAssistant,
    entry: VpdAirConfigEntry,
    device: DeviceEntry,
) -> dict[str, Any]:
    """Return diagnostics for one device."""
    coordinator = entry.runtime_data
    payload = coordinator.device_diagnostics_payload(device.id)
    return async_redact_data(
        {
            "entry_id": entry.entry_id,
            "device": {
                "id": device.id,
                "name": device.name_by_user or device.name,
            },
            "topology": payload["topology"],
            "snapshot": payload["snapshot"],
            "creatable_kinds": payload["creatable_kinds"],
        },
        _TO_REDACT,
    )
