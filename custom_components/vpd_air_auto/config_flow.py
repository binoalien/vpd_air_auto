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
    CONF_ENABLE_ABSOLUTE_HUMIDITY,
    CONF_ENABLE_AIR,
    CONF_ENABLE_DEW_POINT,
    CONF_ENABLE_LEAF,
    CONF_LEAF_OFFSET,
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
    build_schema,
    build_scoped_policy_schema,
    normalize_scoped_policy_input,
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
                    title=DEFAULT_NAME,
                    data=normalized_input,
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

    _edited_scope_id: str
    _edited_scope_level: str

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show options menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["global_defaults", "area_policies", "device_policies"],
        )

    async def async_step_global_defaults(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit global defaults and flat compatibility options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            normalized_input, errors = normalize_user_input(user_input)
            if not errors:
                updated_options = dict(self.config_entry.options)
                updated_options.update(normalized_input)

                global_policy = self._entry_mapping("global_policy")
                global_policy.update(
                    {
                        CONF_ENABLE_AIR: normalized_input[CONF_ENABLE_AIR],
                        CONF_ENABLE_LEAF: normalized_input[CONF_ENABLE_LEAF],
                        CONF_ENABLE_ABSOLUTE_HUMIDITY: normalized_input[
                            CONF_ENABLE_ABSOLUTE_HUMIDITY
                        ],
                        CONF_ENABLE_DEW_POINT: normalized_input[CONF_ENABLE_DEW_POINT],
                        CONF_LEAF_OFFSET: normalized_input[CONF_LEAF_OFFSET],
                    }
                )
                updated_options["global_policy"] = global_policy
                updated_options["area_policies"] = self._entry_mapping("area_policies")
                updated_options["device_policies"] = self._entry_mapping(
                    "device_policies"
                )
                updated_options["source_overrides"] = self._entry_mapping(
                    "source_overrides"
                )
                return self.async_create_entry(data=updated_options)

        return self.async_show_form(
            step_id="global_defaults",
            data_schema=build_schema(resolve_options(self.config_entry)),
            errors=errors,
        )

    async def async_step_area_policies(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show area policy action menu."""
        return self.async_show_menu(
            step_id="area_policies",
            menu_options=["area_policy_add", "area_policy_edit", "area_policy_delete"],
        )

    async def async_step_device_policies(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show device policy action menu."""
        return self.async_show_menu(
            step_id="device_policies",
            menu_options=[
                "device_policy_add",
                "device_policy_edit",
                "device_policy_delete",
            ],
        )

    async def async_step_area_policy_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add an area policy override."""
        return await self._async_step_scoped_policy_edit("area", None, user_input)

    async def async_step_area_policy_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select and edit an area policy override."""
        return await self._async_step_select_scope("area", user_input)

    async def async_step_area_policy_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Delete an area policy override."""
        return await self._async_step_delete_scope("area", user_input)

    async def async_step_device_policy_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a device policy override."""
        return await self._async_step_scoped_policy_edit("device", None, user_input)

    async def async_step_device_policy_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select and edit a device policy override."""
        return await self._async_step_select_scope("device", user_input)

    async def async_step_device_policy_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Delete a device policy override."""
        return await self._async_step_delete_scope("device", user_input)

    async def async_step_edit_scoped_policy(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit the currently selected scoped policy."""
        return await self._async_step_scoped_policy_edit(
            self._edited_scope_level,
            self._edited_scope_id,
            user_input,
            include_scope_id=False,
        )

    async def _async_step_select_scope(
        self,
        scope_level: str,
        user_input: dict[str, Any] | None,
    ) -> ConfigFlowResult:
        scope_map = self._scope_map(scope_level)
        if user_input is not None:
            selected_scope = user_input.get("scope_id")
            if isinstance(selected_scope, str) and selected_scope in scope_map:
                self._edited_scope_level = scope_level
                self._edited_scope_id = selected_scope
                return await self.async_step_edit_scoped_policy()
            return self.async_show_form(
                step_id=f"{scope_level}_policy_edit",
                data_schema=self._scope_select_schema(scope_map),
                errors={"scope_id": "invalid_scope_id"},
            )

        return self.async_show_form(
            step_id=f"{scope_level}_policy_edit",
            data_schema=self._scope_select_schema(scope_map),
            errors={},
        )

    async def _async_step_delete_scope(
        self,
        scope_level: str,
        user_input: dict[str, Any] | None,
    ) -> ConfigFlowResult:
        scope_map = self._scope_map(scope_level)
        if user_input is not None:
            selected_scope = user_input.get("scope_id")
            if isinstance(selected_scope, str) and selected_scope in scope_map:
                scope_map.pop(selected_scope)
                return self.async_create_entry(
                    data=self._build_updated_options(scope_level, scope_map)
                )
            return self.async_show_form(
                step_id=f"{scope_level}_policy_delete",
                data_schema=self._scope_select_schema(scope_map),
                errors={"scope_id": "invalid_scope_id"},
            )

        return self.async_show_form(
            step_id=f"{scope_level}_policy_delete",
            data_schema=self._scope_select_schema(scope_map),
            errors={},
        )

    async def _async_step_scoped_policy_edit(
        self,
        scope_level: str,
        scope_id: str | None,
        user_input: dict[str, Any] | None,
        *,
        include_scope_id: bool = True,
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        scope_map = self._scope_map(scope_level)
        existing_policy = scope_map.get(scope_id, {}) if scope_id else {}

        if user_input is not None:
            normalized, errors = normalize_scoped_policy_input(
                user_input,
                include_scope_id=include_scope_id,
            )
            if not errors:
                resolved_scope_id = scope_id or normalized.pop("scope_id")
                scope_map[resolved_scope_id] = normalized
                return self.async_create_entry(
                    data=self._build_updated_options(scope_level, scope_map)
                )

        step_id = (
            "edit_scoped_policy"
            if not include_scope_id
            else f"{scope_level}_policy_add"
        )
        return self.async_show_form(
            step_id=step_id,
            data_schema=build_scoped_policy_schema(
                scope_id=scope_id or "",
                policy=existing_policy,
                include_scope_id=include_scope_id,
            ),
            errors=errors,
        )

    def _entry_mapping(self, key: str) -> dict[str, Any]:
        """Return key mapping from options with entry.data fallback."""
        value = self.config_entry.options.get(key, self.config_entry.data.get(key, {}))
        return dict(value) if isinstance(value, Mapping) else {}

    def _scope_map(self, scope_level: str) -> dict[str, Any]:
        """Return scoped map for area/device with options-data fallback."""
        return self._entry_mapping(f"{scope_level}_policies")

    def _build_updated_options(
        self,
        scope_level: str,
        updated_scope: dict[str, Any],
    ) -> dict[str, Any]:
        """Build updated options while preserving unrelated and scoped keys."""
        updated = dict(self.config_entry.options)
        updated[f"{scope_level}_policies"] = updated_scope
        updated["global_policy"] = self._entry_mapping("global_policy")
        updated["area_policies"] = self._entry_mapping("area_policies")
        updated["device_policies"] = self._entry_mapping("device_policies")
        updated["source_overrides"] = self._entry_mapping("source_overrides")
        return updated

    def _scope_select_schema(self, scope_map: dict[str, Any]) -> vol.Schema:
        """Build selector schema for choosing a scope id."""
        default_scope = next(iter(scope_map), "")
        choices = list(scope_map) or [""]
        return vol.Schema(
            {vol.Required("scope_id", default=default_scope): vol.In(choices)}
        )
