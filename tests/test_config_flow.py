"""Tests for VPD Air Auto config and options flows."""

from __future__ import annotations

from copy import deepcopy

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vpd_air_auto.config_flow import (
    VpdAirAutoConfigFlow,
    VpdAirAutoOptionsFlow,
)
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
from custom_components.vpd_air_auto.migrations import V2_ENTRY_VERSION


def test_config_flow_entry_version_is_v2() -> None:
    """New config entries must be created with version 2."""
    assert VpdAirAutoConfigFlow.VERSION == V2_ENTRY_VERSION == 2


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
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=_valid_user_input(),
        options={
            "device_policies": {"devx": {CONF_ENABLE_AIR: True}},
            "global_policy": {CONF_ENABLE_AIR: True},
            "source_overrides": {
                "devx": {"temperature_entity_id": "sensor.x"}
            },
            "future_key": "keep",
        },
    )
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
    """Test options flow opens with menu."""
    entry = MockConfigEntry(domain=DOMAIN, data=_valid_user_input())
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result.get("type") is data_entry_flow.FlowResultType.MENU
    assert result.get("step_id") == "init"
    assert result.get("menu_options") == [
        "global_defaults",
        "area_policies",
        "device_policies",
        "source_overrides",
    ]


async def test_source_override_menu_adds_edits_and_deletes(
    hass: HomeAssistant,
) -> None:
    """Test source override CRUD flow and preservation of unrelated options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=_valid_user_input(),
        options={
            "area_policies": {"a1": {CONF_ENABLE_AIR: False}},
            "device_policies": {"d1": {CONF_ENABLE_LEAF: True}},
            "global_policy": {CONF_ENABLE_AIR: True},
            "source_overrides": {"d1": {"temperature_entity_id": "sensor.t1"}},
            "future_key": {"keep": True},
        },
    )
    entry.add_to_hass(hass)
    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "source_overrides"}
    )
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "source_override_add"}
    )
    add_result = await hass.config_entries.options.async_configure(
        init_result["flow_id"],
        user_input={
            "scope_id": "d2",
            "temperature_entity_id": "sensor.t2",
            "humidity_entity_id": "sensor.h2",
        },
    )
    assert add_result["data"]["source_overrides"]["d2"] == {
        "temperature_entity_id": "sensor.t2",
        "humidity_entity_id": "sensor.h2",
    }
    assert add_result["data"]["future_key"] == entry.options["future_key"]

    edit_flow = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        edit_flow["flow_id"], user_input={"next_step_id": "source_overrides"}
    )
    await hass.config_entries.options.async_configure(
        edit_flow["flow_id"], user_input={"next_step_id": "source_override_edit"}
    )
    await hass.config_entries.options.async_configure(
        edit_flow["flow_id"], user_input={"scope_id": "d1"}
    )
    edit_result = await hass.config_entries.options.async_configure(
        edit_flow["flow_id"],
        user_input={
            "temperature_entity_id": "sensor.t3",
            "humidity_entity_id": "sensor.h3",
        },
    )
    assert (
        edit_result["data"]["source_overrides"]["d1"]["temperature_entity_id"]
        == "sensor.t3"
    )

    delete_flow = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        delete_flow["flow_id"], user_input={"next_step_id": "source_overrides"}
    )
    await hass.config_entries.options.async_configure(
        delete_flow["flow_id"], user_input={"next_step_id": "source_override_delete"}
    )
    delete_result = await hass.config_entries.options.async_configure(
        delete_flow["flow_id"], user_input={"scope_id": "d1"}
    )
    assert "d1" not in delete_result["data"]["source_overrides"]


async def test_source_override_validation_errors(hass: HomeAssistant) -> None:
    """Test source override validation for scope, empty values, and invalid domains."""
    entry = MockConfigEntry(domain=DOMAIN, data=_valid_user_input())
    entry.add_to_hass(hass)
    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "source_overrides"}
    )
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "source_override_add"}
    )
    invalid_scope = await hass.config_entries.options.async_configure(
        init_result["flow_id"],
        user_input={
            "scope_id": "  ",
            "temperature_entity_id": "",
            "humidity_entity_id": "",
        },
    )
    assert invalid_scope["errors"]["scope_id"] == "invalid_scope_id"
    assert invalid_scope["errors"]["base"] == "missing_source_override"

    invalid_domain = await hass.config_entries.options.async_configure(
        init_result["flow_id"],
        user_input={
            "scope_id": "d1",
            "temperature_entity_id": "climate.x",
            "humidity_entity_id": "switch.y",
        },
    )
    assert (
        invalid_domain["errors"]["temperature_entity_id"]
        == "invalid_temperature_entity"
    )
    assert invalid_domain["errors"]["humidity_entity_id"] == "invalid_humidity_entity"


async def test_options_flow_updates_entry_options(hass: HomeAssistant) -> None:
    """Test options flow updates entry options."""
    entry = MockConfigEntry(domain=DOMAIN, data=_valid_user_input())
    entry.add_to_hass(hass)

    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "global_defaults"}
    )
    user_input = deepcopy(_valid_user_input())
    user_input[CONF_ENABLE_LEAF] = False
    user_input[CONF_DISPLAY_NAME] = "VPD Air"
    user_input[CONF_LEAF_OFFSET] = -1.2

    result = await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input=user_input
    )
    await hass.async_block_till_done()

    assert result.get("type") is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result.get("data")[CONF_ENABLE_LEAF] is False
    assert result.get("data")["global_policy"][CONF_ENABLE_LEAF] is False
    assert entry.options[CONF_ENABLE_LEAF] is False


async def test_options_flow_returns_errors_for_invalid_fields(
    hass: HomeAssistant,
) -> None:
    """Test options flow returns errors for invalid fields."""
    entry = MockConfigEntry(domain=DOMAIN, data=_valid_user_input())
    entry.add_to_hass(hass)

    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "global_defaults"}
    )
    user_input = deepcopy(_valid_user_input())
    user_input[CONF_ICON] = "  "
    user_input[CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME] = ""
    user_input[CONF_DEW_POINT_DISPLAY_NAME] = "  "

    result = await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input=user_input
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


async def test_options_flow_adds_area_policy(hass: HomeAssistant) -> None:
    """Test options flow can add area scoped override."""
    entry = MockConfigEntry(domain=DOMAIN, data=_valid_user_input())
    entry.add_to_hass(hass)

    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "area_policies"}
    )
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "area_policy_add"}
    )
    result = await hass.config_entries.options.async_configure(
        init_result["flow_id"],
        user_input={
            "scope_id": "living_room",
            CONF_ENABLE_AIR: False,
            CONF_ENABLE_LEAF: True,
            CONF_ENABLE_ABSOLUTE_HUMIDITY: True,
            CONF_ENABLE_DEW_POINT: False,
            CONF_LEAF_OFFSET: -1.5,
        },
    )
    assert result.get("type") is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["area_policies"]["living_room"][CONF_ENABLE_AIR] is False
    assert result["data"]["device_policies"] == entry.options["device_policies"]
    assert "global_policy" in result["data"]
    assert result["data"]["source_overrides"] == entry.options["source_overrides"]


async def test_options_flow_edits_and_deletes_device_policy(
    hass: HomeAssistant,
) -> None:
    """Test options flow can edit and delete device scoped override."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=_valid_user_input(),
        options={
            "area_policies": {"area_z": {CONF_ENABLE_DEW_POINT: True}},
            "source_overrides": {"device_1": {"humidity_entity_id": "sensor.h1"}},
            "global_policy": {CONF_ENABLE_LEAF: True},
            "future_key": {"z": 2},
            "device_policies": {
                "device_1": {
                    CONF_ENABLE_AIR: True,
                    CONF_ENABLE_LEAF: True,
                    CONF_ENABLE_ABSOLUTE_HUMIDITY: True,
                    CONF_ENABLE_DEW_POINT: True,
                    CONF_LEAF_OFFSET: -2.0,
                }
            }
        },
    )
    entry.add_to_hass(hass)

    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "device_policies"}
    )
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "device_policy_edit"}
    )
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"scope_id": "device_1"}
    )
    edit_result = await hass.config_entries.options.async_configure(
        init_result["flow_id"],
        user_input={
            CONF_ENABLE_AIR: False,
            CONF_ENABLE_LEAF: False,
            CONF_ENABLE_ABSOLUTE_HUMIDITY: True,
            CONF_ENABLE_DEW_POINT: False,
            CONF_LEAF_OFFSET: -0.5,
        },
    )
    assert edit_result.get("type") is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert edit_result["data"]["device_policies"]["device_1"][CONF_ENABLE_LEAF] is False
    assert edit_result["data"]["area_policies"] == entry.options["area_policies"]
    assert edit_result["data"]["source_overrides"] == entry.options["source_overrides"]
    assert "global_policy" in edit_result["data"]
    assert edit_result["data"]["global_policy"][CONF_ENABLE_LEAF] is True
    assert edit_result["data"]["future_key"] == entry.options["future_key"]

    delete_init = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        delete_init["flow_id"], user_input={"next_step_id": "device_policies"}
    )
    await hass.config_entries.options.async_configure(
        delete_init["flow_id"], user_input={"next_step_id": "device_policy_delete"}
    )
    delete_result = await hass.config_entries.options.async_configure(
        delete_init["flow_id"], user_input={"scope_id": "device_1"}
    )
    assert delete_result.get("type") is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert delete_result["data"]["device_policies"] == {}
    assert delete_result["data"]["area_policies"] == entry.options["area_policies"]
    assert delete_result["data"]["source_overrides"] == entry.options[
        "source_overrides"
    ]
    assert "global_policy" in delete_result["data"]
    assert delete_result["data"]["global_policy"][CONF_ENABLE_LEAF] is True
    assert delete_result["data"]["future_key"] == entry.options["future_key"]


async def test_global_defaults_preserves_scoped_maps_from_entry_data(
    hass: HomeAssistant,
) -> None:
    """Test global defaults save preserves scoped maps from entry.data fallback."""
    data = _valid_user_input()
    data["area_policies"] = {"a1": {CONF_ENABLE_AIR: False, CONF_LEAF_OFFSET: -1.0}}
    data["device_policies"] = {"d1": {CONF_ENABLE_LEAF: False, CONF_LEAF_OFFSET: -2.0}}
    data["source_overrides"] = {"d1": {"temperature_entity_id": "sensor.t"}}
    entry = MockConfigEntry(domain=DOMAIN, data=data)
    entry.add_to_hass(hass)

    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        init_result["flow_id"],
        user_input={"next_step_id": "global_defaults"},
    )
    updated = deepcopy(_valid_user_input())
    updated[CONF_DISPLAY_NAME] = "Updated"
    result = await hass.config_entries.options.async_configure(
        init_result["flow_id"],
        user_input=updated,
    )

    assert result.get("type") is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["area_policies"] == data["area_policies"]
    assert result["data"]["device_policies"] == data["device_policies"]
    assert result["data"]["source_overrides"] == data["source_overrides"]


async def test_area_edit_delete_reads_policies_from_entry_data(
    hass: HomeAssistant,
) -> None:
    """Test area edit/delete sees policies stored only in entry.data."""
    data = _valid_user_input()
    data["area_policies"] = {
        "living_room": {CONF_ENABLE_AIR: False, CONF_LEAF_OFFSET: -1.2}
    }
    entry = MockConfigEntry(domain=DOMAIN, data=data, options={})
    entry.add_to_hass(hass)

    edit_flow = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        edit_flow["flow_id"], user_input={"next_step_id": "area_policies"}
    )
    edit_form = await hass.config_entries.options.async_configure(
        edit_flow["flow_id"], user_input={"next_step_id": "area_policy_edit"}
    )

    delete_flow = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        delete_flow["flow_id"], user_input={"next_step_id": "area_policies"}
    )
    delete_form = await hass.config_entries.options.async_configure(
        delete_flow["flow_id"], user_input={"next_step_id": "area_policy_delete"}
    )

    assert edit_form.get("type") is data_entry_flow.FlowResultType.FORM
    assert delete_form.get("type") is data_entry_flow.FlowResultType.FORM


async def test_saving_area_policy_preserves_other_maps_and_unknown_keys(
    hass: HomeAssistant,
) -> None:
    """Test saving area policy preserves global/device/source/unknown keys."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=_valid_user_input(),
        options={
            "device_policies": {"dev1": {CONF_ENABLE_AIR: True}},
            "source_overrides": {"dev1": {"temperature_entity_id": "sensor.temp"}},
            "global_policy": {CONF_ENABLE_AIR: True},
            "future_key": {"x": 1},
        },
    )
    entry.add_to_hass(hass)

    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "area_policies"}
    )
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "area_policy_add"}
    )
    result = await hass.config_entries.options.async_configure(
        init_result["flow_id"],
        user_input={
            "scope_id": "area1",
            CONF_ENABLE_AIR: False,
            CONF_ENABLE_LEAF: True,
            CONF_ENABLE_ABSOLUTE_HUMIDITY: True,
            CONF_ENABLE_DEW_POINT: True,
            CONF_LEAF_OFFSET: -1.1,
        },
    )

    assert result.get("type") is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["device_policies"] == entry.options["device_policies"]
    assert result["data"]["source_overrides"] == entry.options["source_overrides"]
    assert "global_policy" in result["data"]
    assert result["data"]["global_policy"][CONF_ENABLE_AIR] is True


async def test_saving_device_policy_preserves_other_maps_and_unknown_keys(
    hass: HomeAssistant,
) -> None:
    """Test saving device policy preserves global/area/source/unknown keys."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=_valid_user_input(),
        options={
            "area_policies": {"area1": {CONF_ENABLE_LEAF: False}},
            "source_overrides": {"dev1": {"humidity_entity_id": "sensor.hum"}},
            "global_policy": {CONF_ENABLE_LEAF: True},
            "future_key": "keep_me",
        },
    )
    entry.add_to_hass(hass)

    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "device_policies"}
    )
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "device_policy_add"}
    )
    result = await hass.config_entries.options.async_configure(
        init_result["flow_id"],
        user_input={
            "scope_id": "device_2",
            CONF_ENABLE_AIR: True,
            CONF_ENABLE_LEAF: False,
            CONF_ENABLE_ABSOLUTE_HUMIDITY: False,
            CONF_ENABLE_DEW_POINT: True,
            CONF_LEAF_OFFSET: -0.8,
        },
    )

    assert result.get("type") is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["area_policies"] == entry.options["area_policies"]
    assert result["data"]["source_overrides"] == entry.options["source_overrides"]
    assert "global_policy" in result["data"]
    assert result["data"]["global_policy"][CONF_ENABLE_LEAF] is True


async def test_area_policy_add_rejects_whitespace_scope_id(hass: HomeAssistant) -> None:
    """Test area policy add rejects empty/whitespace scope id."""
    entry = MockConfigEntry(domain=DOMAIN, data=_valid_user_input())
    entry.add_to_hass(hass)

    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "area_policies"}
    )
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "area_policy_add"}
    )
    result = await hass.config_entries.options.async_configure(
        init_result["flow_id"],
        user_input={
            "scope_id": "   ",
            CONF_ENABLE_AIR: True,
            CONF_ENABLE_LEAF: True,
            CONF_ENABLE_ABSOLUTE_HUMIDITY: True,
            CONF_ENABLE_DEW_POINT: True,
            CONF_LEAF_OFFSET: -1.0,
        },
    )

    assert result.get("type") is data_entry_flow.FlowResultType.FORM
    assert result.get("errors") == {"scope_id": "invalid_scope_id"}


async def test_area_delete_removes_selected_area_id(
    hass: HomeAssistant,
) -> None:
    """Test area delete removes the selected area id and preserves other keys."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=_valid_user_input(),
        options={
            "area_policies": {
                "a1": {CONF_ENABLE_AIR: True},
                "a2": {CONF_ENABLE_AIR: False},
            },
            "device_policies": {"d1": {CONF_ENABLE_LEAF: True}},
            "global_policy": {CONF_ENABLE_AIR: True},
            "source_overrides": {"d1": {"temperature_entity_id": "sensor.t1"}},
            "future_key": "keep",
        },
    )
    entry.add_to_hass(hass)

    init_result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "area_policies"}
    )
    await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"next_step_id": "area_policy_delete"}
    )
    result = await hass.config_entries.options.async_configure(
        init_result["flow_id"], user_input={"scope_id": "a1"}
    )

    assert result.get("type") is data_entry_flow.FlowResultType.CREATE_ENTRY
    assert "a1" not in result["data"]["area_policies"]
    assert "a2" in result["data"]["area_policies"]
    assert result["data"]["device_policies"] == entry.options["device_policies"]
    assert result["data"]["source_overrides"] == entry.options["source_overrides"]
    assert "global_policy" in result["data"]
    assert result["data"]["global_policy"][CONF_ENABLE_AIR] is True
