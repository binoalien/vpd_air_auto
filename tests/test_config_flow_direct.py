"""Lightweight direct unit tests for config flow user step logic."""

from __future__ import annotations

from unittest.mock import Mock

from homeassistant.config_entries import ConfigEntry
from homeassistant.data_entry_flow import FlowResultType

from custom_components.vpd_air_auto.config_flow import VpdAirAutoConfigFlow
from custom_components.vpd_air_auto.const import DEFAULT_NAME

from .test_config_flow import _valid_user_input


async def test_direct_async_step_user_aborts_for_existing_entry() -> None:
    """Test direct async step user aborts for existing entry."""
    flow = VpdAirAutoConfigFlow()
    flow._async_current_entries = lambda include_ignore=None: [Mock(spec=ConfigEntry)]

    result = await flow.async_step_user()

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "single_instance_allowed"


async def test_direct_async_step_user_shows_form_with_defaults() -> None:
    """Test direct async step user shows form with defaults."""
    flow = VpdAirAutoConfigFlow()
    flow._async_current_entries = lambda include_ignore=None: []

    result = await flow.async_step_user()

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"


async def test_direct_async_step_user_creates_entry_for_valid_input() -> None:
    """Test direct async step user creates entry for valid input."""
    flow = VpdAirAutoConfigFlow()
    flow._async_current_entries = lambda include_ignore=None: []

    result = await flow.async_step_user(_valid_user_input())

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == DEFAULT_NAME


async def test_direct_async_step_user_returns_form_for_invalid_input() -> None:
    """Test direct async step user returns form for invalid input."""
    flow = VpdAirAutoConfigFlow()
    flow._async_current_entries = lambda include_ignore=None: []
    invalid = _valid_user_input()
    invalid["display_name"] = "   "

    result = await flow.async_step_user(invalid)

    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {"display_name": "invalid_display_name"}
