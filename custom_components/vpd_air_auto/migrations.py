"""Config entry migrations for VPD Air Auto."""

from __future__ import annotations

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

ENTRY_VERSION_V2 = 2


def _build_v2_entry_data(data: dict[str, Any]) -> dict[str, Any]:
    """Transform V1 flat entry data into V2 nested policy data."""
    return {
        CONF_SCAN_INTERVAL: data.get(CONF_SCAN_INTERVAL),
        "global_policy": {
            CONF_ENABLE_AIR: data.get(CONF_ENABLE_AIR),
            CONF_ENABLE_LEAF: data.get(CONF_ENABLE_LEAF),
            CONF_ENABLE_ABSOLUTE_HUMIDITY: data.get(CONF_ENABLE_ABSOLUTE_HUMIDITY),
            CONF_ENABLE_DEW_POINT: data.get(CONF_ENABLE_DEW_POINT),
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
    """Migrate old config entry formats to V2 policy structure."""
    if entry.version >= ENTRY_VERSION_V2:
        return True

    if entry.version == 1:
        hass.config_entries.async_update_entry(
            entry,
            data=_build_v2_entry_data(dict(entry.data)),
            version=ENTRY_VERSION_V2,
        )
        return True

    return False
