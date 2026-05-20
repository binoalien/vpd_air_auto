"""Config-entry migrations for VPD Air Auto."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntry
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


def _is_v2_payload(data: Mapping[str, Any]) -> bool:
    """Return whether entry data already follows V2 nesting."""
    return "global_policy" in data


def _coerce_bool(value: Any, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _migrate_v1_to_v2(data: Mapping[str, Any]) -> dict[str, Any]:
    """Map flat V1 entry data to the V2 policy-backed structure."""
    return {
        CONF_SCAN_INTERVAL: data.get(CONF_SCAN_INTERVAL),
        "global_policy": {
            CONF_ENABLE_AIR: _coerce_bool(data.get(CONF_ENABLE_AIR), True),
            CONF_ENABLE_LEAF: _coerce_bool(data.get(CONF_ENABLE_LEAF), True),
            CONF_ENABLE_ABSOLUTE_HUMIDITY: _coerce_bool(
                data.get(CONF_ENABLE_ABSOLUTE_HUMIDITY),
                True,
            ),
            CONF_ENABLE_DEW_POINT: _coerce_bool(data.get(CONF_ENABLE_DEW_POINT), True),
            CONF_LEAF_OFFSET: data.get(CONF_LEAF_OFFSET),
            CONF_ICON: data.get(CONF_ICON),
            CONF_DISPLAY_NAME: data.get(CONF_DISPLAY_NAME),
            CONF_LEAF_ICON: data.get(CONF_LEAF_ICON),
            CONF_LEAF_DISPLAY_NAME: data.get(CONF_LEAF_DISPLAY_NAME),
            CONF_ABSOLUTE_HUMIDITY_ICON: data.get(CONF_ABSOLUTE_HUMIDITY_ICON),
            CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: data.get(
                CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME
            ),
            CONF_DEW_POINT_ICON: data.get(CONF_DEW_POINT_ICON),
            CONF_DEW_POINT_DISPLAY_NAME: data.get(CONF_DEW_POINT_DISPLAY_NAME),
        },
        "area_policies": {},
        "device_policies": {},
        "source_overrides": {},
    }


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry data schemas to current V2 shape."""
    if _is_v2_payload(entry.data):
        return True

    migrated_data = _migrate_v1_to_v2(entry.data)
    hass.config_entries.async_update_entry(entry, data=migrated_data)
    return True
