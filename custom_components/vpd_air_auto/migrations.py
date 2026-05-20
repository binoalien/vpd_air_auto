"""Config entry migrations for VPD Air Auto."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
    CONF_ABSOLUTE_HUMIDITY_ICON,
    CONF_DEW_POINT_DISPLAY_NAME,
    CONF_DEW_POINT_ICON,
    CONF_DISPLAY_NAME,
    CONF_ENABLE_ABSOLUTE_HUMIDITY,
    CONF_ENABLE_AIR,
    CONF_ENABLE_DEW_POINT,
    CONF_ENABLE_LEAF,
    CONF_ICON,
    CONF_LEAF_DISPLAY_NAME,
    CONF_LEAF_ICON,
    CONF_LEAF_OFFSET,
    CONF_SCAN_INTERVAL,
)


def _entry_policy_data(entry: ConfigEntry) -> dict[str, Any]:
    """Build V2 policy mapping from legacy flat config entry values."""
    if isinstance(entry.data.get("global_policy"), Mapping):
        return dict(entry.data)

    raw = entry.options if entry.options else entry.data

    global_policy = {
        CONF_ENABLE_AIR: raw.get(CONF_ENABLE_AIR),
        CONF_ENABLE_LEAF: raw.get(CONF_ENABLE_LEAF),
        CONF_ENABLE_ABSOLUTE_HUMIDITY: raw.get(CONF_ENABLE_ABSOLUTE_HUMIDITY),
        CONF_ENABLE_DEW_POINT: raw.get(CONF_ENABLE_DEW_POINT),
        CONF_LEAF_OFFSET: raw.get(CONF_LEAF_OFFSET),
        CONF_ICON: raw.get(CONF_ICON),
        CONF_DISPLAY_NAME: raw.get(CONF_DISPLAY_NAME),
        CONF_LEAF_ICON: raw.get(CONF_LEAF_ICON),
        CONF_LEAF_DISPLAY_NAME: raw.get(CONF_LEAF_DISPLAY_NAME),
        CONF_ABSOLUTE_HUMIDITY_ICON: raw.get(CONF_ABSOLUTE_HUMIDITY_ICON),
        CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: raw.get(CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME),
        CONF_DEW_POINT_ICON: raw.get(CONF_DEW_POINT_ICON),
        CONF_DEW_POINT_DISPLAY_NAME: raw.get(CONF_DEW_POINT_DISPLAY_NAME),
    }

    return {
        CONF_NAME: entry.data.get(CONF_NAME),
        CONF_SCAN_INTERVAL: raw.get(CONF_SCAN_INTERVAL),
        "global_policy": {key: value for key, value in global_policy.items() if value is not None},
        "area_policies": {},
        "device_policies": {},
        "source_overrides": {},
    }


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate V1 flat config entries to the V2 policy dictionary shape."""
    hass.config_entries.async_update_entry(entry, data=_entry_policy_data(entry))
    return True
