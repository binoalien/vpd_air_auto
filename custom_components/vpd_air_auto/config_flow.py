"""Config flow for VPD Air Auto."""

from __future__ import annotations

from collections.abc import Mapping
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
    BEHAVIOR_FIELDS,
    build_behavior_schema,
    build_schema,
    normalize_behavior_input,
    normalize_user_input,
    resolve_options,
)


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

    _selected_area_id: str | None = None
    _selected_device_id: str | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show root options menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["global_defaults", "area_policies", "device_policies"],
        )

    async def async_step_global_defaults(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit global default behavior options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            normalized_input, errors = normalize_behavior_input(user_input)
            if not errors:
                updates = dict(self.config_entry.options)
                updates.update(normalized_input)
                updates["global_policy"] = self._updated_global_policy(normalized_input)
                return self.async_create_entry(data=updates)

        return self.async_show_form(
            step_id="global_defaults",
            data_schema=build_behavior_schema(self._global_behavior_defaults()),
            errors=errors,
        )

    async def async_step_area_policies(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show area policy menu."""
        return self.async_show_menu(
            step_id="area_policies",
            menu_options=["area_policy_add", "area_policy_edit", "area_policy_delete"],
        )

    async def async_step_area_policy_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create an area override."""
        return await self._async_step_scoped_id_select("area", user_input, "add")

    async def async_step_device_policies(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show device policy menu."""
        return self.async_show_menu(
            step_id="device_policies",
            menu_options=["device_policy_add", "device_policy_edit", "device_policy_delete"],
        )

    async def async_step_device_policy_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create a device override."""
        return await self._async_step_scoped_id_select("device", user_input, "add")

    async def async_step_area_policy_edit(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._selected_area_id is None:
            return await self._async_step_scoped_id_select("area", user_input, "edit")
        return await self._async_step_scoped_edit("area", self._selected_area_id, user_input)

    async def async_step_area_policy_delete(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_step_scoped_delete("area", user_input)

    async def async_step_device_policy_edit(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._selected_device_id is None:
            return await self._async_step_scoped_id_select("device", user_input, "edit")
        return await self._async_step_scoped_edit("device", self._selected_device_id, user_input)

    async def async_step_device_policy_delete(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_step_scoped_delete("device", user_input)

    async def _async_step_scoped_id_select(
        self, scope: str, user_input: dict[str, Any] | None, mode: str
    ) -> ConfigFlowResult:
        key = "area_id" if scope == "area" else "device_id"
        errors: dict[str, str] = {}
        if user_input is not None:
            selected = str(user_input.get(key, "")).strip()
            scoped = self._scoped_map(f"{scope}_policies")
            if not selected:
                errors[key] = "required"
            elif mode == "add" and selected in scoped:
                errors[key] = "already_configured"
            elif mode in {"edit", "delete"} and selected not in scoped:
                errors[key] = "not_found"
            else:
                if scope == "area":
                    self._selected_area_id = selected
                    return await (self.async_step_area_policy_edit() if mode != "delete" else self.async_step_area_policy_delete())
                self._selected_device_id = selected
                return await (self.async_step_device_policy_edit() if mode != "delete" else self.async_step_device_policy_delete())

        return self.async_show_form(step_id=f"{scope}_policy_{mode}", data_schema=vol.Schema({vol.Required(key): str}), errors=errors)

    async def _async_step_scoped_edit(
        self, scope: str, scope_id: str, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        """Edit a scoped override."""
        errors: dict[str, str] = {}
        map_key = f"{scope}_policies"
        scoped = self._scoped_map(map_key)
        if user_input is not None:
            normalized, errors = normalize_behavior_input(user_input)
            if not errors:
                scoped[scope_id] = normalized
                updates = dict(self.config_entry.options)
                updates[map_key] = scoped
                return self.async_create_entry(data=updates)
        return self.async_show_form(
            step_id=f"{scope}_policy_edit",
            data_schema=build_behavior_schema(scoped.get(scope_id, {})),
            errors=errors,
        )

    async def _async_step_scoped_delete(
        self, scope: str, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        """Delete scoped override."""
        scope_id = self._selected_area_id if scope == "area" else self._selected_device_id
        if scope_id is None:
            return await self._async_step_scoped_id_select(scope, user_input, "delete")
        if user_input is not None:
            scoped = self._scoped_map(f"{scope}_policies")
            scoped.pop(scope_id, None)
            updates = dict(self.config_entry.options)
            updates[f"{scope}_policies"] = scoped
            return self.async_create_entry(data=updates)
        return self.async_show_form(step_id=f"{scope}_policy_delete", data_schema=vol.Schema({}), description_placeholders={"scope_id": scope_id})

    def _scoped_map(self, key: str) -> dict[str, dict[str, Any]]:
        value = self.config_entry.options.get(key, self.config_entry.data.get(key, {}))
        if not isinstance(value, Mapping):
            return {}
        return {str(k): dict(v) for k, v in value.items() if isinstance(k, str) and isinstance(v, Mapping)}

    def _global_behavior_defaults(self) -> dict[str, Any]:
        options = resolve_options(self.config_entry)
        return {
            "enable_air": options.enable_air,
            "enable_leaf": options.enable_leaf,
            "enable_absolute_humidity": options.enable_absolute_humidity,
            "enable_dew_point": options.enable_dew_point,
            "leaf_offset": options.leaf_offset_c,
        }

    def _updated_global_policy(self, updates: dict[str, Any]) -> dict[str, Any]:
        existing = self.config_entry.options.get(
            "global_policy", self.config_entry.data.get("global_policy", {})
        )
        merged = dict(existing) if isinstance(existing, Mapping) else {}
        for key in BEHAVIOR_FIELDS:
            if key in updates:
                merged[key] = updates[key]
        return merged
