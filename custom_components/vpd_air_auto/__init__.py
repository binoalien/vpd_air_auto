"""Set up the VPD Air Auto integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import VpdAirCoordinator
from .options import resolve_options

type VpdAirConfigEntry = ConfigEntry[VpdAirCoordinator]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)  # pylint: disable=invalid-name


async def async_setup(_hass: HomeAssistant, _config: ConfigType) -> bool:
    """Set up the integration from YAML."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: VpdAirConfigEntry) -> bool:
    """Set up VPD Air Auto from a config entry."""
    options = resolve_options(entry)

    coordinator = VpdAirCoordinator(
        hass=hass,
        config_entry=entry,
        options=options,
    )
    entry.runtime_data = coordinator

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VpdAirConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.async_shutdown()
    return unload_ok
