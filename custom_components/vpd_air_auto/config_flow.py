"""Config flow for VPD Air Auto."""

from __future__ import annotations

from typing import Any

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
from .options import build_schema, normalize_user_input, resolve_options


class VpdAirAutoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VPD Air Auto."""

    VERSION = 1

    @staticmethod
    def is_matching(other_flow: ConfigFlow) -> bool:
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

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the integration options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            normalized_input, errors = normalize_user_input(user_input)
            if not errors:
                return self.async_create_entry(data=normalized_input)

        return self.async_show_form(
            step_id="init",
            data_schema=build_schema(resolve_options(self.config_entry)),
            errors=errors,
        )
