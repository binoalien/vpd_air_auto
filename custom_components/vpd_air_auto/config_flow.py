"""Config flow for VPD Air Auto."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    OptionsFlowWithReload,
)
from homeassistant.core import callback

from .const import (
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
    IntegrationOptions,
)
from .options import (
    build_behavior_schema,
    build_schema,
    normalize_behavior_input,
    normalize_user_input,
    resolve_options,
)




BEHAVIOR_FIELDS = (
    CONF_ENABLE_AIR,
    CONF_ENABLE_LEAF,
    CONF_ENABLE_ABSOLUTE_HUMIDITY,
    CONF_ENABLE_DEW_POINT,
    CONF_LEAF_OFFSET,
)


def _merged_policy_data(config_entry: ConfigEntry) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(config_entry.data, dict):
        merged.update(config_entry.data)
    if isinstance(config_entry.options, dict):
        merged.update(config_entry.options)
    return merged


def _policy_behavior_defaults(data: dict[str, Any]) -> dict[str, Any]:
    global_policy = data.get("global_policy") if isinstance(data.get("global_policy"), dict) else {}
    return {
        CONF_ENABLE_AIR: global_policy.get(CONF_ENABLE_AIR, data.get(CONF_ENABLE_AIR, DEFAULT_ENABLE_AIR)),
        CONF_ENABLE_LEAF: global_policy.get(CONF_ENABLE_LEAF, data.get(CONF_ENABLE_LEAF, DEFAULT_ENABLE_LEAF)),
        CONF_ENABLE_ABSOLUTE_HUMIDITY: global_policy.get(CONF_ENABLE_ABSOLUTE_HUMIDITY, data.get(CONF_ENABLE_ABSOLUTE_HUMIDITY, DEFAULT_ENABLE_ABSOLUTE_HUMIDITY)),
        CONF_ENABLE_DEW_POINT: global_policy.get(CONF_ENABLE_DEW_POINT, data.get(CONF_ENABLE_DEW_POINT, DEFAULT_ENABLE_DEW_POINT)),
        CONF_LEAF_OFFSET: global_policy.get(CONF_LEAF_OFFSET, data.get(CONF_LEAF_OFFSET, DEFAULT_LEAF_OFFSET)),
    }


def _scope_entry_defaults(scoped_map: dict[str, Any], scope_id: str) -> dict[str, Any]:
    existing = scoped_map.get(scope_id) if isinstance(scoped_map.get(scope_id), dict) else {}
    return {
        CONF_ENABLE_AIR: existing.get(CONF_ENABLE_AIR),
        CONF_ENABLE_LEAF: existing.get(CONF_ENABLE_LEAF),
        CONF_ENABLE_ABSOLUTE_HUMIDITY: existing.get(CONF_ENABLE_ABSOLUTE_HUMIDITY),
        CONF_ENABLE_DEW_POINT: existing.get(CONF_ENABLE_DEW_POINT),
        CONF_LEAF_OFFSET: existing.get(CONF_LEAF_OFFSET),
    }


class VpdAirAutoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VPD Air Auto."""

    VERSION = 1

    def is_matching(self, other_flow: ConfigFlow) -> bool:
        """Return whether another flow is for this integration."""
        return other_flow.handler == DOMAIN

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}

        if user_input is not None:
            normalized_input, errors = normalize_user_input(user_input)
            if not errors:
                return self.async_create_entry(
                    title=DEFAULT_NAME, data=normalized_input
                )

        defaults = IntegrationOptions(
            scan_interval_seconds=DEFAULT_SCAN_INTERVAL,
            enable_air=DEFAULT_ENABLE_AIR,
            enable_leaf=DEFAULT_ENABLE_LEAF,
            enable_absolute_humidity=DEFAULT_ENABLE_ABSOLUTE_HUMIDITY,
            enable_dew_point=DEFAULT_ENABLE_DEW_POINT,
            icon=DEFAULT_ICON,
            display_name=DEFAULT_DISPLAY_NAME,
            leaf_icon=DEFAULT_LEAF_ICON,
            leaf_display_name=DEFAULT_LEAF_DISPLAY_NAME,
            leaf_offset_c=DEFAULT_LEAF_OFFSET,
            absolute_humidity_icon=DEFAULT_ABSOLUTE_HUMIDITY_ICON,
            absolute_humidity_display_name=DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
            dew_point_icon=DEFAULT_DEW_POINT_ICON,
            dew_point_display_name=DEFAULT_DEW_POINT_DISPLAY_NAME,
        )
        return self.async_show_form(
            step_id="user",
            data_schema=build_schema(defaults),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow handler."""
        return VpdAirAutoOptionsFlow()


class VpdAirAutoOptionsFlow(OptionsFlowWithReload):
    """Handle options for VPD Air Auto."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Show menu for scoped policy editing."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["global_defaults", "area_policies", "device_policies"],
        )

    async def async_step_global_defaults(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Edit global defaults and keep flat compatibility fields in sync."""
        merged = _merged_policy_data(self.config_entry)
        if user_input is not None:
            normalized_input, errors = normalize_user_input(user_input)
            if not errors:
                updated = dict(self.config_entry.options)
                updated.update(normalized_input)
                global_policy = dict(updated.get("global_policy", {}))
                for key in BEHAVIOR_FIELDS:
                    global_policy[key] = normalized_input[key]
                updated["global_policy"] = global_policy
                return self.async_create_entry(data=updated)
            return self.async_show_form(step_id="global_defaults", data_schema=build_schema(resolve_options(self.config_entry)), errors=errors)

        return self.async_show_form(step_id="global_defaults", data_schema=build_schema(resolve_options(self.config_entry)), errors={})

    async def async_step_area_policies(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            action = user_input["action"]
            scope_id = user_input["scope_id"].strip()
            self._editing_scope_type = "area_policies"
            self._editing_scope_id = scope_id
            if action == "add_edit":
                return await self.async_step_scope_behavior()
            return await self._delete_scope_policy("area_policies", scope_id)
        return self.async_show_form(step_id="area_policies", data_schema=vol.Schema({vol.Required("scope_id"): str, vol.Required("action", default="add_edit"): vol.In(["add_edit", "delete"])}), errors={})

    async def async_step_device_policies(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            action = user_input["action"]
            scope_id = user_input["scope_id"].strip()
            self._editing_scope_type = "device_policies"
            self._editing_scope_id = scope_id
            if action == "add_edit":
                return await self.async_step_scope_behavior()
            return await self._delete_scope_policy("device_policies", scope_id)
        return self.async_show_form(step_id="device_policies", data_schema=vol.Schema({vol.Required("scope_id"): str, vol.Required("action", default="add_edit"): vol.In(["add_edit", "delete"])}), errors={})

    async def async_step_scope_behavior(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        scope_type = self._editing_scope_type
        scope_id = self._editing_scope_id
        merged = _merged_policy_data(self.config_entry)
        scoped_map = dict(merged.get(scope_type, {}))
        defaults = _scope_entry_defaults(scoped_map, scope_id)

        if user_input is not None:
            normalized, errors = normalize_behavior_input(user_input, allow_none=True)
            if not errors:
                updated = dict(self.config_entry.options)
                target_map = dict(updated.get(scope_type, {}))
                target_map[scope_id] = normalized
                updated[scope_type] = target_map
                return self.async_create_entry(data=updated)
            return self.async_show_form(step_id="scope_behavior", data_schema=build_behavior_schema(defaults, allow_none=True), errors=errors)

        return self.async_show_form(step_id="scope_behavior", data_schema=build_behavior_schema(defaults, allow_none=True), errors={})

    async def _delete_scope_policy(self, scope_type: str, scope_id: str) -> ConfigFlowResult:
        updated = dict(self.config_entry.options)
        target_map = dict(updated.get(scope_type, {}))
        target_map.pop(scope_id, None)
        updated[scope_type] = target_map
        return self.async_create_entry(data=updated)
