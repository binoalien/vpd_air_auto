"""Tests for VPD Air Auto setup and unload."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vpd_air_auto import (
    async_setup,
    async_migrate_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.vpd_air_auto.const import DOMAIN, PLATFORMS


async def test_async_setup_returns_true(hass: HomeAssistant) -> None:
    """Test async setup returns true."""
    assert await async_setup(hass, {}) is True


async def test_async_setup_entry_creates_coordinator_and_forwards_platforms(
    hass: HomeAssistant,
) -> None:
    """Test async setup entry creates coordinator and forwards platforms."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    coordinator = AsyncMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()

    with (
        patch(
            "custom_components.vpd_air_auto.resolve_options",
            return_value="resolved-options",
        ) as mock_resolve,
        patch(
            "custom_components.vpd_air_auto.VpdAirCoordinator",
            return_value=coordinator,
        ) as mock_coordinator,
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            AsyncMock(),
        ) as mock_forward,
    ):
        assert await async_setup_entry(hass, entry) is True

    mock_resolve.assert_called_once_with(entry)
    mock_coordinator.assert_called_once_with(
        hass=hass,
        config_entry=entry,
        options="resolved-options",
    )
    coordinator.async_config_entry_first_refresh.assert_awaited_once()
    mock_forward.assert_awaited_once_with(entry, PLATFORMS)
    assert entry.runtime_data is coordinator


async def test_async_unload_entry_shuts_down_runtime_data_when_platforms_unload(
    hass: HomeAssistant,
) -> None:
    """Test async unload entry shuts down runtime data when platforms unload."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    runtime_data = AsyncMock()
    runtime_data.async_shutdown = AsyncMock()
    entry.runtime_data = runtime_data

    with patch.object(
        hass.config_entries, "async_unload_platforms", AsyncMock(return_value=True)
    ) as mock_unload:
        assert await async_unload_entry(hass, entry) is True

    mock_unload.assert_awaited_once_with(entry, PLATFORMS)
    runtime_data.async_shutdown.assert_awaited_once()


async def test_async_unload_entry_does_not_shutdown_when_platform_unload_fails(
    hass: HomeAssistant,
) -> None:
    """Test async unload entry does not shutdown when platform unload fails."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    runtime_data = AsyncMock()
    runtime_data.async_shutdown = AsyncMock()
    entry.runtime_data = runtime_data

    with patch.object(
        hass.config_entries, "async_unload_platforms", AsyncMock(return_value=False)
    ) as mock_unload:
        assert await async_unload_entry(hass, entry) is False

    mock_unload.assert_awaited_once_with(entry, PLATFORMS)
    runtime_data.async_shutdown.assert_not_awaited()


async def test_async_migrate_entry_delegates_to_migrations_module(
    hass: HomeAssistant,
) -> None:
    """Test init migration wrapper delegates to migration module."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    with patch(
        "custom_components.vpd_air_auto.migrate_entry",
        AsyncMock(return_value=True),
    ) as mock_migrate:
        assert await async_migrate_entry(hass, entry) is True

    mock_migrate.assert_awaited_once_with(hass, entry)
