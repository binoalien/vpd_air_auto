"""Tests for config-entry migrations."""

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


async def test_async_migrate_entry_maps_v1_flat_data_to_v2_policy_shape(
    hass: HomeAssistant,
) -> None:
    """Test V1 flat entry data is migrated to nested V2 policy structure."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SCAN_INTERVAL: 123,
            CONF_ENABLE_AIR: False,
            CONF_ENABLE_LEAF: True,
            CONF_ENABLE_ABSOLUTE_HUMIDITY: False,
            CONF_ENABLE_DEW_POINT: True,
            CONF_ICON: "mdi:alpha-a",
            CONF_DISPLAY_NAME: "Air",
            CONF_LEAF_ICON: "mdi:leaf-maple",
            CONF_LEAF_DISPLAY_NAME: "Leaf",
            CONF_LEAF_OFFSET: -1.5,
            CONF_ABSOLUTE_HUMIDITY_ICON: "mdi:water-check",
            CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: "AH",
            CONF_DEW_POINT_ICON: "mdi:thermometer",
            CONF_DEW_POINT_DISPLAY_NAME: "Dew",
        },
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.data == {
        CONF_SCAN_INTERVAL: 123,
        "global_policy": {
            CONF_ENABLE_AIR: False,
            CONF_ENABLE_LEAF: True,
            CONF_ENABLE_ABSOLUTE_HUMIDITY: False,
            CONF_ENABLE_DEW_POINT: True,
            CONF_LEAF_OFFSET: -1.5,
            CONF_ICON: "mdi:alpha-a",
            CONF_DISPLAY_NAME: "Air",
            CONF_LEAF_ICON: "mdi:leaf-maple",
            CONF_LEAF_DISPLAY_NAME: "Leaf",
            CONF_ABSOLUTE_HUMIDITY_ICON: "mdi:water-check",
            CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: "AH",
            CONF_DEW_POINT_ICON: "mdi:thermometer",
            CONF_DEW_POINT_DISPLAY_NAME: "Dew",
        },
        "area_policies": {},
        "device_policies": {},
        "source_overrides": {},
    }


async def test_async_migrate_entry_is_noop_for_existing_v2_entry(
    hass: HomeAssistant,
) -> None:
    """Test migration is skipped when entry is already in V2 shape."""
    data = {
        CONF_SCAN_INTERVAL: 300,
        "global_policy": {CONF_ENABLE_AIR: True},
        "area_policies": {"area_1": {CONF_ENABLE_LEAF: False}},
        "device_policies": {},
        "source_overrides": {},
    }
    entry = MockConfigEntry(domain=DOMAIN, data=data)
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True
    assert entry.data == data
