"""Tests for config entry migrations."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vpd_air_auto.const import (
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
    DOMAIN,
)
from custom_components.vpd_air_auto.migrations import async_migrate_entry


async def test_async_migrate_entry_v1_to_v2_maps_flat_fields(
    hass: HomeAssistant,
) -> None:
    """Test V1 config entry data is migrated to nested V2 policy structure."""
    old_data = {
        CONF_SCAN_INTERVAL: 120,
        CONF_ENABLE_AIR: False,
        CONF_ENABLE_LEAF: True,
        CONF_ENABLE_ABSOLUTE_HUMIDITY: False,
        CONF_ENABLE_DEW_POINT: True,
        CONF_ICON: "mdi:test",
        CONF_DISPLAY_NAME: "Air",
        CONF_LEAF_ICON: "mdi:leaf-outline",
        CONF_LEAF_DISPLAY_NAME: "Leaf",
        CONF_LEAF_OFFSET: -1.5,
        CONF_ABSOLUTE_HUMIDITY_ICON: "mdi:water-outline",
        CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: "Abs",
        CONF_DEW_POINT_ICON: "mdi:thermometer",
        CONF_DEW_POINT_DISPLAY_NAME: "Dew",
    }
    entry = MockConfigEntry(domain=DOMAIN, data=old_data, version=1)
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True
    assert entry.version == 2
    assert entry.data == {
        CONF_SCAN_INTERVAL: 120,
        "global_policy": {
            CONF_ENABLE_AIR: False,
            CONF_ENABLE_LEAF: True,
            CONF_ENABLE_ABSOLUTE_HUMIDITY: False,
            CONF_ENABLE_DEW_POINT: True,
            CONF_LEAF_OFFSET: -1.5,
            CONF_ICON: "mdi:test",
            CONF_DISPLAY_NAME: "Air",
            CONF_LEAF_ICON: "mdi:leaf-outline",
            CONF_LEAF_DISPLAY_NAME: "Leaf",
            CONF_ABSOLUTE_HUMIDITY_ICON: "mdi:water-outline",
            CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: "Abs",
            CONF_DEW_POINT_ICON: "mdi:thermometer",
            CONF_DEW_POINT_DISPLAY_NAME: "Dew",
        },
        "area_policies": {},
        "device_policies": {},
        "source_overrides": {},
    }


async def test_async_migrate_entry_noop_when_already_v2(hass: HomeAssistant) -> None:
    """Test migration is a no-op for already migrated entries."""
    data = {
        CONF_SCAN_INTERVAL: 300,
        "global_policy": {},
        "area_policies": {},
        "device_policies": {},
        "source_overrides": {},
    }
    entry = MockConfigEntry(domain=DOMAIN, data=data, version=2)
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True
    assert entry.version == 2
    assert entry.data == data


async def test_async_migrate_entry_unsupported_version_returns_false(
    hass: HomeAssistant,
) -> None:
    """Test migration fails for unknown old versions."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, version=0)
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is False
    assert entry.version == 0
