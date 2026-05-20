"""Tests for V1 -> V2 config entry migrations."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vpd_air_auto.const import (
    CONF_DISPLAY_NAME,
    CONF_ENABLE_AIR,
    CONF_ENABLE_LEAF,
    CONF_LEAF_OFFSET,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)
from custom_components.vpd_air_auto.migrations import async_migrate_entry


async def test_async_migrate_entry_maps_v1_flat_values_into_v2_policy_structure(
    hass: HomeAssistant,
) -> None:
    """Test legacy flat values are moved into the nested V2 policy structure."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"scan_interval": 777},
        options={
            CONF_SCAN_INTERVAL: 900,
            CONF_ENABLE_AIR: False,
            CONF_ENABLE_LEAF: True,
            CONF_DISPLAY_NAME: "Legacy Air",
            CONF_LEAF_OFFSET: -1.25,
        },
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.data[CONF_SCAN_INTERVAL] == 900
    assert entry.data["area_policies"] == {}
    assert entry.data["device_policies"] == {}
    assert entry.data["source_overrides"] == {}
    assert entry.data["global_policy"][CONF_ENABLE_AIR] is False
    assert entry.data["global_policy"][CONF_ENABLE_LEAF] is True
    assert entry.data["global_policy"][CONF_DISPLAY_NAME] == "Legacy Air"
    assert entry.data["global_policy"][CONF_LEAF_OFFSET] == -1.25


async def test_async_migrate_entry_keeps_existing_v2_data_shape(
    hass: HomeAssistant,
) -> None:
    """Test migration is idempotent when entry already has nested V2 policy data."""
    data = {
        CONF_SCAN_INTERVAL: 300,
        "global_policy": {CONF_ENABLE_AIR: True},
        "area_policies": {"area-1": {CONF_ENABLE_LEAF: False}},
        "device_policies": {},
        "source_overrides": {},
    }
    entry = MockConfigEntry(domain=DOMAIN, data=data)
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True
    assert entry.data == data
