"""Tests for VPD Air Auto config and options flows."""

from __future__ import annotations

from copy import deepcopy

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vpd_air_auto.config_flow import VpdAirAutoOptionsFlow
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
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


def _valid_user_input() -> dict[str, object]:
    return {
        CONF_SCAN_INTERVAL: 900,
        CONF_ENABLE_AIR: True,
        CONF_ENABLE_LEAF: True,
        CONF_ENABLE_ABSOLUTE_HUMIDITY: True,
        CONF_ENABLE_DEW_POINT: True,
        CONF_ICON: "mdi:water-opacity",
        CONF_DISPLAY_NAME: "Air VPD",
        CONF_LEAF_ICON: "mdi:leaf",
        CONF_LEAF_DISPLAY_NAME: "Leaf VPD",
        CONF_LEAF_OFFSET: -2.5,
        CONF_ABSOLUTE_HUMIDITY_ICON: "mdi:water",
        CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: "Absolute Humidity",
        CONF_DEW_POINT_ICON: "mdi:thermometer-water",
        CONF_DEW_POINT_DISPLAY_NAME: "Dew Point",
    }


async def test_user_flow_shows_form_with_defaults(hass: HomeAssistant) -> None:
    """Test user flow shows form with defaults."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result.get("type") is data_entry_flow.FlowResultType.FORM
    assert result.get("step_id") == "user"
    schema = result.get("data_schema")
    assert schema is not None
    assert schema({}) == {
        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        CONF_ENABLE_AIR: DEFAULT_ENABLE_AIR,
        CONF_ENABLE_LEAF: DEFAULT_ENABLE_LEAF,
        CONF_ENABLE_ABSOLUTE_HUMIDITY: DEFAULT_ENABLE_ABSOLUTE_HUMIDITY,
        CONF_ENABLE_DEW_POINT: DEFAULT_ENABLE_DEW_POINT,
        CONF_ICON: DEFAULT_ICON,
        CONF_DISPLAY_NAME: DEFAULT_DISPLAY_NAME,
        CONF_LEAF_ICON: DEFAULT_LEAF_ICON,
        CONF_LEAF_DISPLAY_NAME: DEFAULT_LEAF_DISPLAY_NAME,
        CONF_LEAF_OFFSET: DEFAULT_LEAF_OFFSET,
        CONF_ABSOLUTE_HUMIDITY_ICON: DEFAULT_ABSOLUTE_HUMIDITY_ICON,
        CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
        CONF_DEW_POINT_ICON: DEFAULT_DEW_POINT_ICON,
        CONF_DEW_POINT_DISPLAY_NAME: DEFAULT_DEW_POINT_DISPLAY_NAME,
    }


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """Test user flow creates entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=_valid_user_input(),
    )

    assert result.get("type") is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result.get("title") == DEFAULT_NAME
    assert result.get("data") == _valid_user_input()


async def test_user_flow_aborts_for_second_instance(hass: HomeAssistant) -> None:
    """Test user flow aborts for second instance."""
    entry = MockConfigEntry(domain=DOMAIN, data=_valid_user_input())
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result.get("type") is data_entry_flow.FlowResultType.ABORT
    assert result.get("reason") == "single_instance_allowed"


async def test_user_flow_returns_errors_for_invalid_fields(hass: HomeAssistant) -> None:
    """Test user flow returns errors for invalid fields."""
    user_input = _valid_user_input()
    user_input[CONF_DISPLAY_NAME] = "   "
    user_input[CONF_LEAF_OFFSET] = 50

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=user_input,
    )

    assert result.get("type") is data_entry_flow.FlowResultType.FORM
    assert result.get("errors") == {
        CONF_DISPLAY_NAME: "invalid_display_name",
        CONF_LEAF_OFFSET: "invalid_leaf_offset",
    }


async def test_options_flow_returns_form_with_entry_values(hass: HomeAssistant) -> None:
    """Test options flow returns form with entry values."""
    entry = MockConfigEntry(domain=DOMAIN, data=_valid_user_input())
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result.get("type") is data_entry_flow.FlowResultType.FORM
    assert result.get("step_id") == "init"
    assert result.get("menu_options") == ["global_defaults", "area_policies", "device_policies"]


async def test_options_flow_updates_entry_options(hass: HomeAssistant) -> None:
    """Test options flow updates entry options."""
    entry = MockConfigEntry(domain=DOMAIN, data=_valid_user_input())
    entry.add_to_hass(hass)

    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    global_result = await hass.config_entries.options.async_configure(init_result["flow_id"], user_input={"next_step_id": "global_defaults"})
    user_input = deepcopy(_valid_user_input())
    user_input[CONF_ENABLE_LEAF] = False
    user_input[CONF_DISPLAY_NAME] = "VPD Air"
    user_input[CONF_LEAF_OFFSET] = -1.2

    result = await hass.config_entries.options.async_configure(
        global_result["flow_id"], user_input=user_input
    )
    await hass.async_block_till_done()

    assert result.get("type") is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result.get("data") == user_input
    assert entry.options == user_input


async def test_options_flow_returns_errors_for_invalid_fields(
    hass: HomeAssistant,
) -> None:
    """Test options flow returns errors for invalid fields."""
    entry = MockConfigEntry(domain=DOMAIN, data=_valid_user_input())
    entry.add_to_hass(hass)

    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    global_result = await hass.config_entries.options.async_configure(init_result["flow_id"], user_input={"next_step_id": "global_defaults"})
    user_input = deepcopy(_valid_user_input())
    user_input[CONF_ICON] = "  "
    user_input[CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME] = ""
    user_input[CONF_DEW_POINT_DISPLAY_NAME] = "  "

    result = await hass.config_entries.options.async_configure(
        global_result["flow_id"], user_input=user_input
    )

    assert result.get("type") is data_entry_flow.FlowResultType.FORM
    assert result.get("errors") == {
        CONF_ICON: "invalid_icon",
        CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: "invalid_absolute_humidity_display_name",
        CONF_DEW_POINT_DISPLAY_NAME: "invalid_dew_point_display_name",
    }


def test_async_get_options_flow_returns_handler() -> None:
    """Test async get options flow returns handler."""
    flow = VpdAirAutoOptionsFlow()

    assert isinstance(flow, VpdAirAutoOptionsFlow)


async def test_options_flow_area_policy_add_and_delete(hass: HomeAssistant) -> None:
    """Test adding and deleting area scoped behavior policies."""
    entry = MockConfigEntry(domain=DOMAIN, data=_valid_user_input())
    entry.add_to_hass(hass)

    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    area_menu = await hass.config_entries.options.async_configure(init_result["flow_id"], user_input={"next_step_id": "area_policies"})
    edit_form = await hass.config_entries.options.async_configure(area_menu["flow_id"], user_input={"scope_id": "area.living_room", "action": "add_edit"})
    save_result = await hass.config_entries.options.async_configure(edit_form["flow_id"], user_input={
        CONF_ENABLE_AIR: True,
        CONF_ENABLE_LEAF: None,
        CONF_ENABLE_ABSOLUTE_HUMIDITY: False,
        CONF_ENABLE_DEW_POINT: None,
        CONF_LEAF_OFFSET: -1.5,
    })
    await hass.async_block_till_done()
    assert save_result.get("type") is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert entry.options["area_policies"]["area.living_room"][CONF_ENABLE_ABSOLUTE_HUMIDITY] is False

    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    area_menu = await hass.config_entries.options.async_configure(init_result["flow_id"], user_input={"next_step_id": "area_policies"})
    delete_result = await hass.config_entries.options.async_configure(area_menu["flow_id"], user_input={"scope_id": "area.living_room", "action": "delete"})
    await hass.async_block_till_done()
    assert delete_result.get("type") is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert "area.living_room" not in entry.options["area_policies"]


async def test_options_flow_device_policy_add(hass: HomeAssistant) -> None:
    """Test adding device scoped behavior policies."""
    entry = MockConfigEntry(domain=DOMAIN, data=_valid_user_input())
    entry.add_to_hass(hass)

    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    device_menu = await hass.config_entries.options.async_configure(init_result["flow_id"], user_input={"next_step_id": "device_policies"})
    edit_form = await hass.config_entries.options.async_configure(device_menu["flow_id"], user_input={"scope_id": "device-1", "action": "add_edit"})
    save_result = await hass.config_entries.options.async_configure(edit_form["flow_id"], user_input={
        CONF_ENABLE_AIR: None,
        CONF_ENABLE_LEAF: True,
        CONF_ENABLE_ABSOLUTE_HUMIDITY: None,
        CONF_ENABLE_DEW_POINT: False,
        CONF_LEAF_OFFSET: None,
    })
    await hass.async_block_till_done()
    assert save_result.get("type") is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert entry.options["device_policies"]["device-1"][CONF_ENABLE_DEW_POINT] is False
