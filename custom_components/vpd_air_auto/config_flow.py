"""Config flow for VPD Air Auto."""

from __future__ import annotations

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
    build_global_defaults_schema,
    build_schema,
    build_scoped_policy_schema,
    normalize_global_defaults_input,
    normalize_scoped_policy_input,
    normalize_user_input,
    resolve_options,
)


class VpdAirAutoConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def is_matching(self, other_flow: ConfigFlow) -> bool:
        return other_flow.handler == DOMAIN

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}
        if user_input is not None:
            normalized_input, errors = normalize_user_input(user_input)
            if not errors:
                return self.async_create_entry(title=DEFAULT_NAME, data=normalized_input)

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
        return self.async_show_form(step_id="user", data_schema=build_schema(defaults), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return VpdAirAutoOptionsFlow()


class VpdAirAutoOptionsFlow(OptionsFlowWithReload):
    """Handle options for VPD Air Auto."""

    def __init__(self) -> None:
        self._edit_area_id: str | None = None
        self._edit_device_id: str | None = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=["global_defaults", "area_policies", "device_policies"],
        )

    async def async_step_global_defaults(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            normalized, errors = normalize_global_defaults_input(user_input)
            if not errors:
                options = dict(self.config_entry.options)
                options.update(normalized)
                global_policy = dict(options.get("global_policy", {}))
                for key in (
                    "enable_air",
                    "enable_leaf",
                    "enable_absolute_humidity",
                    "enable_dew_point",
                    "leaf_offset",
                ):
                    global_policy[key] = normalized[key]
                options["global_policy"] = global_policy
                return self.async_create_entry(data=options)

        return self.async_show_form(
            step_id="global_defaults",
            data_schema=build_global_defaults_schema(resolve_options(self.config_entry)),
            errors=errors,
        )

    async def async_step_area_policies(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="area_policies",
            menu_options=["add_area_policy", "edit_area_policy_select", "delete_area_policy"],
        )

    async def async_step_add_area_policy(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_add_scoped_policy("area_policies", "add_area_policy", user_input)

    async def async_step_edit_area_policy_select(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        area_policies = dict(self.config_entry.options.get("area_policies", {}))
        if not area_policies:
            return self.async_abort(reason="no_area_policies")
        if user_input is not None:
            self._edit_area_id = str(user_input["scope_id"])
            return await self.async_step_edit_area_policy()
        return self.async_show_form(
            step_id="edit_area_policy_select",
            data_schema=vol.Schema({vol.Required("scope_id"): vol.In(sorted(area_policies.keys()))}),
        )

    async def async_step_edit_area_policy(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._edit_area_id is None:
            return self.async_abort(reason="invalid_scope")
        return await self._async_edit_scoped_policy("area_policies", self._edit_area_id, "edit_area_policy", user_input)

    async def async_step_delete_area_policy(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_delete_scoped_policy("area_policies", "delete_area_policy", "no_area_policies", user_input)

    async def async_step_device_policies(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="device_policies",
            menu_options=["add_device_policy", "edit_device_policy_select", "delete_device_policy"],
        )

    async def async_step_add_device_policy(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_add_scoped_policy("device_policies", "add_device_policy", user_input)

    async def async_step_edit_device_policy_select(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        device_policies = dict(self.config_entry.options.get("device_policies", {}))
        if not device_policies:
            return self.async_abort(reason="no_device_policies")
        if user_input is not None:
            self._edit_device_id = str(user_input["scope_id"])
            return await self.async_step_edit_device_policy()
        return self.async_show_form(
            step_id="edit_device_policy_select",
            data_schema=vol.Schema({vol.Required("scope_id"): vol.In(sorted(device_policies.keys()))}),
        )

    async def async_step_edit_device_policy(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._edit_device_id is None:
            return self.async_abort(reason="invalid_scope")
        return await self._async_edit_scoped_policy("device_policies", self._edit_device_id, "edit_device_policy", user_input)

    async def async_step_delete_device_policy(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_delete_scoped_policy("device_policies", "delete_device_policy", "no_device_policies", user_input)

    async def _async_add_scoped_policy(self, options_key: str, step_id: str, user_input: dict[str, Any] | None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            scope_id = str(user_input["scope_id"]).strip()
            normalized, errors = normalize_scoped_policy_input(user_input)
            if not scope_id:
                errors["scope_id"] = "scope_id_required"
            if not errors:
                options = dict(self.config_entry.options)
                scoped = dict(options.get(options_key, {}))
                scoped[scope_id] = normalized
                options[options_key] = scoped
                return self.async_create_entry(data=options)

        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required("scope_id"): str,
                    **build_scoped_policy_schema().schema,
                }
            ),
            errors=errors,
        )

    async def _async_edit_scoped_policy(self, options_key: str, scope_id: str, step_id: str, user_input: dict[str, Any] | None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        scoped = dict(self.config_entry.options.get(options_key, {}))
        current = dict(scoped.get(scope_id, {}))
        if user_input is not None:
            normalized, errors = normalize_scoped_policy_input(user_input)
            if not errors:
                options = dict(self.config_entry.options)
                scoped[scope_id] = normalized
                options[options_key] = scoped
                return self.async_create_entry(data=options)

        return self.async_show_form(
            step_id=step_id,
            data_schema=build_scoped_policy_schema(current),
            errors=errors,
        )

    async def _async_delete_scoped_policy(self, options_key: str, step_id: str, empty_reason: str, user_input: dict[str, Any] | None) -> ConfigFlowResult:
        scoped = dict(self.config_entry.options.get(options_key, {}))
        if not scoped:
            return self.async_abort(reason=empty_reason)
        if user_input is not None:
            options = dict(self.config_entry.options)
            selected = str(user_input["scope_id"])
            scoped.pop(selected, None)
            options[options_key] = scoped
            return self.async_create_entry(data=options)

        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema({vol.Required("scope_id"): vol.In(sorted(scoped.keys()))}),
        )
