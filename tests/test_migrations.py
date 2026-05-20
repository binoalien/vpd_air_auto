"""Tests for config entry migrations."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vpd_air_auto.const import (
    CONF_DEW_POINT_DISPLAY_NAME,
    CONF_ENABLE_AIR,
    CONF_ENABLE_LEAF,
    CONF_LEAF_OFFSET,
    DOMAIN,
)
from custom_components.vpd_air_auto.migrations import V2_ENTRY_VERSION, async_migrate_entry


async def test_async_migrate_entry_maps_v1_values_to_v2_global_policy(
    hass: HomeAssistant,
) -> None:
    """V1 flat values are migrated into options.global_policy."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data={CONF_ENABLE_AIR: False, CONF_LEAF_OFFSET: -1.1},
        options={CONF_ENABLE_LEAF: False, CONF_DEW_POINT_DISPLAY_NAME: "DP Custom"},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.version == V2_ENTRY_VERSION
    assert entry.options["global_policy"][CONF_ENABLE_AIR] is False
    assert entry.options["global_policy"][CONF_ENABLE_LEAF] is False
    assert entry.options["global_policy"][CONF_LEAF_OFFSET] == -1.1
    assert (
        entry.options["global_policy"][CONF_DEW_POINT_DISPLAY_NAME] == "DP Custom"
    )
    assert entry.options["area_policies"] == {}
    assert entry.options["device_policies"] == {}
    assert entry.options["source_overrides"] == {}


async def test_async_migrate_entry_skips_when_already_v2(hass: HomeAssistant) -> None:
    """Migration is a no-op for entries already at V2 version."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=V2_ENTRY_VERSION,
        options={"global_policy": {CONF_ENABLE_AIR: True}},
    )
    entry.add_to_hass(hass)

    before_options = dict(entry.options)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.version == V2_ENTRY_VERSION
    assert entry.options == before_options
