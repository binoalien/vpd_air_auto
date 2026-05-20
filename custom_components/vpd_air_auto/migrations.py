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
    DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
    DEFAULT_ABSOLUTE_HUMIDITY_ICON,
    DEFAULT_DEW_POINT_DISPLAY_NAME,
    DEFAULT_DEW_POINT_ICON,
    DEFAULT_DISPLAY_NAME,
    DEFAULT_ENABLE_ABSOLUTE_HUMIDITY,
    DEFAULT_ENABLE_AIR,
    DEFAULT_ENABLE_DEW_POINT,
    DEFAULT_ENABLE_LEAF,
    DEFAULT_ICON,
    DEFAULT_LEAF_DISPLAY_NAME,
    DEFAULT_LEAF_ICON,
    DEFAULT_LEAF_OFFSET,
)

V2_ENTRY_VERSION = 2


def _effective_value(entry: ConfigEntry, key: str, default: Any) -> Any:
    """Resolve a V1 setting from options/data with default fallback."""
    return entry.options.get(key, entry.data.get(key, default))


def _as_bool_or_default(value: Any, default: bool) -> bool:
    """Return bool values unchanged, fallback to default otherwise."""
    return value if isinstance(value, bool) else default


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate V1 flat config fields into V2 nested policy structure."""
    if entry.version >= V2_ENTRY_VERSION:
        return True

    global_policy = {
        CONF_ENABLE_AIR: _as_bool_or_default(
            _effective_value(entry, CONF_ENABLE_AIR, DEFAULT_ENABLE_AIR),
            DEFAULT_ENABLE_AIR,
        ),
        CONF_ENABLE_LEAF: _as_bool_or_default(
            _effective_value(entry, CONF_ENABLE_LEAF, DEFAULT_ENABLE_LEAF),
            DEFAULT_ENABLE_LEAF,
        ),
        CONF_ENABLE_ABSOLUTE_HUMIDITY: _as_bool_or_default(
            _effective_value(
                entry,
                CONF_ENABLE_ABSOLUTE_HUMIDITY,
                DEFAULT_ENABLE_ABSOLUTE_HUMIDITY,
            ),
            DEFAULT_ENABLE_ABSOLUTE_HUMIDITY,
        ),
        CONF_ENABLE_DEW_POINT: _as_bool_or_default(
            _effective_value(entry, CONF_ENABLE_DEW_POINT, DEFAULT_ENABLE_DEW_POINT),
            DEFAULT_ENABLE_DEW_POINT,
        ),
        CONF_LEAF_OFFSET: float(
            _effective_value(entry, CONF_LEAF_OFFSET, DEFAULT_LEAF_OFFSET)
        ),
        CONF_ICON: str(_effective_value(entry, CONF_ICON, DEFAULT_ICON)),
        CONF_DISPLAY_NAME: str(
            _effective_value(entry, CONF_DISPLAY_NAME, DEFAULT_DISPLAY_NAME)
        ),
        CONF_LEAF_ICON: str(_effective_value(entry, CONF_LEAF_ICON, DEFAULT_LEAF_ICON)),
        CONF_LEAF_DISPLAY_NAME: str(
            _effective_value(entry, CONF_LEAF_DISPLAY_NAME, DEFAULT_LEAF_DISPLAY_NAME)
        ),
        CONF_ABSOLUTE_HUMIDITY_ICON: str(
            _effective_value(
                entry,
                CONF_ABSOLUTE_HUMIDITY_ICON,
                DEFAULT_ABSOLUTE_HUMIDITY_ICON,
            )
        ),
        CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: str(
            _effective_value(
                entry,
                CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
                DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
            )
        ),
        CONF_DEW_POINT_ICON: str(
            _effective_value(entry, CONF_DEW_POINT_ICON, DEFAULT_DEW_POINT_ICON)
        ),
        CONF_DEW_POINT_DISPLAY_NAME: str(
            _effective_value(
                entry,
                CONF_DEW_POINT_DISPLAY_NAME,
                DEFAULT_DEW_POINT_DISPLAY_NAME,
            )
        ),
    }

    migrated_options = dict(entry.options)
    migrated_options["global_policy"] = global_policy
    migrated_options.setdefault("area_policies", {})
    migrated_options.setdefault("device_policies", {})
    migrated_options.setdefault("source_overrides", {})

    hass.config_entries.async_update_entry(
        entry,
        options=migrated_options,
        version=V2_ENTRY_VERSION,
    )
    return True
