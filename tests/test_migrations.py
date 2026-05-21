"""Tests for config entry migrations."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vpd_air_auto.const import (
    CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
    CONF_DEW_POINT_DISPLAY_NAME,
    CONF_ENABLE_AIR,
    CONF_ENABLE_DEW_POINT,
    CONF_ENABLE_LEAF,
    CONF_LEAF_OFFSET,
    CONF_SCAN_INTERVAL,
    DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
    DEFAULT_ENABLE_AIR,
    DEFAULT_ENABLE_DEW_POINT,
    DEFAULT_LEAF_OFFSET,
    DOMAIN,
)
from custom_components.vpd_air_auto.migrations import (
    V2_ENTRY_VERSION,
    async_migrate_entry,
)


async def test_async_migrate_entry_maps_v1_values_to_v2_global_policy(
    hass: HomeAssistant,
) -> None:
    """V1 flat values are migrated into options.global_policy."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data={CONF_ENABLE_AIR: False, CONF_LEAF_OFFSET: -1.1},
        options={
            CONF_ENABLE_LEAF: False,
            CONF_DEW_POINT_DISPLAY_NAME: "DP Custom",
            CONF_SCAN_INTERVAL: 123,
        },
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.version == V2_ENTRY_VERSION
    assert "global_policy" in entry.options
    assert entry.options["global_policy"][CONF_ENABLE_AIR] is False
    assert entry.options["global_policy"][CONF_ENABLE_LEAF] is False
    assert entry.options["global_policy"][CONF_LEAF_OFFSET] == -1.1
    assert entry.options["global_policy"][CONF_DEW_POINT_DISPLAY_NAME] == "DP Custom"
    assert entry.options["area_policies"] == {}
    assert entry.options["device_policies"] == {}
    assert entry.options["source_overrides"] == {}
    assert entry.options[CONF_ENABLE_LEAF] is False
    assert entry.options[CONF_SCAN_INTERVAL] == 123


async def test_async_migrate_entry_options_override_data(hass: HomeAssistant) -> None:
    """When both data and options define a key, options must win."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data={CONF_ENABLE_AIR: True, CONF_LEAF_OFFSET: -4.0},
        options={CONF_ENABLE_AIR: False, CONF_LEAF_OFFSET: -1.0},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.options["global_policy"][CONF_ENABLE_AIR] is False
    assert entry.options["global_policy"][CONF_LEAF_OFFSET] == -1.0


async def test_async_migrate_entry_uses_defaults_for_missing_fields(
    hass: HomeAssistant,
) -> None:
    """Missing V1 fields fall back to integration defaults."""
    entry = MockConfigEntry(domain=DOMAIN, version=1, data={}, options={})
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.options["global_policy"][CONF_ENABLE_AIR] is DEFAULT_ENABLE_AIR
    assert (
        entry.options["global_policy"][CONF_ENABLE_DEW_POINT]
        is DEFAULT_ENABLE_DEW_POINT
    )
    assert entry.options["global_policy"][CONF_LEAF_OFFSET] == DEFAULT_LEAF_OFFSET
    assert (
        entry.options["global_policy"][CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME]
        == DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME
    )


async def test_async_migrate_entry_non_bool_strings_do_not_become_true(
    hass: HomeAssistant,
) -> None:
    """String values like 'false' should not be coerced with bool(...)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data={CONF_ENABLE_AIR: "false", CONF_ENABLE_DEW_POINT: "false"},
        options={},
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.options["global_policy"][CONF_ENABLE_AIR] is DEFAULT_ENABLE_AIR
    assert (
        entry.options["global_policy"][CONF_ENABLE_DEW_POINT]
        is DEFAULT_ENABLE_DEW_POINT
    )


async def test_async_migrate_entry_skips_when_already_v2(hass: HomeAssistant) -> None:
    """Migration is a no-op for entries already at V2 version."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=V2_ENTRY_VERSION,
        data={"existing": "data"},
        options={"global_policy": {CONF_ENABLE_AIR: True}},
    )
    entry.add_to_hass(hass)

    before_data = dict(entry.data)
    before_options = dict(entry.options)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.version == V2_ENTRY_VERSION
    assert entry.data == before_data
    assert entry.options == before_options


async def test_async_migrate_entry_skips_future_versions(hass: HomeAssistant) -> None:
    """Future versions are not downgraded or mutated by migration."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=3,
        data={"existing": "data"},
        options={"existing": "option"},
    )
    entry.add_to_hass(hass)

    before_data = dict(entry.data)
    before_options = dict(entry.options)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.version == 3
    assert entry.data == before_data
    assert entry.options == before_options


def test_migration_target_version_constant_is_v2() -> None:
    """Migration target version constant remains aligned with V2 release."""
    assert V2_ENTRY_VERSION == 2
