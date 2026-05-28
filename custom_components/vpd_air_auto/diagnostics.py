"""Diagnostics support for VPD Air Auto."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from . import VpdAirConfigEntry

_TO_REDACT: set[str] = set()


async def async_get_config_entry_diagnostics(
    _hass: HomeAssistant,
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
    _hass: HomeAssistant,
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
            "area_id": payload["area_id"],
            "area_name": payload["area_name"],
            "creatable_kinds": payload["creatable_kinds"],
            "blocked_sensor_kinds": payload["blocked_sensor_kinds"],
            "enabled_kinds": payload["enabled_kinds"],
            "effective_policy": payload["effective_policy"],
            "entity_plan": payload["entity_plan"],
            "policy_field_sources": payload["policy_field_sources"],
            "source_selection": payload["source_selection"],
            "source_tracking": payload["source_tracking"],
        },
        _TO_REDACT,
    )
