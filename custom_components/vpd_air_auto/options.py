"""Option parsing, validation and schemas for VPD Air Auto."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.selector import (
    IconSelector,
    IconSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
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
    DEFAULT_SCAN_INTERVAL,
    MAX_LEAF_OFFSET,
    MAX_SCAN_INTERVAL,
    MIN_LEAF_OFFSET,
    MIN_SCAN_INTERVAL,
    IntegrationOptions,
)


def trimmed_nonempty_string(value: Any, error_key: str) -> str:
    """Validate and normalize a non-empty string setting."""
    if not isinstance(value, str):
        raise vol.Invalid(error_key)

    normalized = value.strip()
    if not normalized:
        raise vol.Invalid(error_key)

    return normalized


def validated_leaf_offset(value: Any) -> float:
    """Validate and normalize the global leaf temperature offset."""
    try:
        normalized = round(float(value), 1)
    except (TypeError, ValueError) as err:
        raise vol.Invalid("invalid_leaf_offset") from err

    if normalized < MIN_LEAF_OFFSET or normalized > MAX_LEAF_OFFSET:
        raise vol.Invalid("invalid_leaf_offset")

    return normalized


def resolve_options(entry: ConfigEntry) -> IntegrationOptions:
    """Resolve effective options from entry data and entry options."""
    return IntegrationOptions(
        scan_interval_seconds=int(
            entry.options.get(
                CONF_SCAN_INTERVAL,
                entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            )
        ),
        enable_air=bool(
            entry.options.get(
                CONF_ENABLE_AIR,
                entry.data.get(CONF_ENABLE_AIR, DEFAULT_ENABLE_AIR),
            )
        ),
        enable_leaf=bool(
            entry.options.get(
                CONF_ENABLE_LEAF,
                entry.data.get(CONF_ENABLE_LEAF, DEFAULT_ENABLE_LEAF),
            )
        ),
        enable_absolute_humidity=bool(
            entry.options.get(
                CONF_ENABLE_ABSOLUTE_HUMIDITY,
                entry.data.get(
                    CONF_ENABLE_ABSOLUTE_HUMIDITY, DEFAULT_ENABLE_ABSOLUTE_HUMIDITY
                ),
            )
        ),
        enable_dew_point=bool(
            entry.options.get(
                CONF_ENABLE_DEW_POINT,
                entry.data.get(CONF_ENABLE_DEW_POINT, DEFAULT_ENABLE_DEW_POINT),
            )
        ),
        icon=str(entry.options.get(CONF_ICON, entry.data.get(CONF_ICON, DEFAULT_ICON))),
        display_name=str(
            entry.options.get(
                CONF_DISPLAY_NAME,
                entry.data.get(CONF_DISPLAY_NAME, DEFAULT_DISPLAY_NAME),
            )
        ),
        leaf_icon=str(
            entry.options.get(
                CONF_LEAF_ICON,
                entry.data.get(CONF_LEAF_ICON, DEFAULT_LEAF_ICON),
            )
        ),
        leaf_display_name=str(
            entry.options.get(
                CONF_LEAF_DISPLAY_NAME,
                entry.data.get(CONF_LEAF_DISPLAY_NAME, DEFAULT_LEAF_DISPLAY_NAME),
            )
        ),
        leaf_offset_c=float(
            entry.options.get(
                CONF_LEAF_OFFSET,
                entry.data.get(CONF_LEAF_OFFSET, DEFAULT_LEAF_OFFSET),
            )
        ),
        absolute_humidity_icon=str(
            entry.options.get(
                CONF_ABSOLUTE_HUMIDITY_ICON,
                entry.data.get(
                    CONF_ABSOLUTE_HUMIDITY_ICON, DEFAULT_ABSOLUTE_HUMIDITY_ICON
                ),
            )
        ),
        absolute_humidity_display_name=str(
            entry.options.get(
                CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
                entry.data.get(
                    CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
                    DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
                ),
            )
        ),
        dew_point_icon=str(
            entry.options.get(
                CONF_DEW_POINT_ICON,
                entry.data.get(CONF_DEW_POINT_ICON, DEFAULT_DEW_POINT_ICON),
            )
        ),
        dew_point_display_name=str(
            entry.options.get(
                CONF_DEW_POINT_DISPLAY_NAME,
                entry.data.get(
                    CONF_DEW_POINT_DISPLAY_NAME, DEFAULT_DEW_POINT_DISPLAY_NAME
                ),
            )
        ),
    )


def build_schema(options: IntegrationOptions) -> vol.Schema:
    """Build the shared schema for setup and options."""
    return vol.Schema(
        {
            vol.Required(
                CONF_SCAN_INTERVAL, default=options.scan_interval_seconds
            ): vol.All(
                int,
                vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
            ),
            vol.Required(CONF_ENABLE_AIR, default=options.enable_air): bool,
            vol.Required(CONF_ENABLE_LEAF, default=options.enable_leaf): bool,
            vol.Required(
                CONF_ENABLE_ABSOLUTE_HUMIDITY,
                default=options.enable_absolute_humidity,
            ): bool,
            vol.Required(CONF_ENABLE_DEW_POINT, default=options.enable_dew_point): bool,
            vol.Required(CONF_ICON, default=options.icon): IconSelector(
                IconSelectorConfig(placeholder=DEFAULT_ICON)
            ),
            vol.Required(CONF_DISPLAY_NAME, default=options.display_name): str,
            vol.Required(CONF_LEAF_ICON, default=options.leaf_icon): IconSelector(
                IconSelectorConfig(placeholder=DEFAULT_LEAF_ICON)
            ),
            vol.Required(
                CONF_LEAF_DISPLAY_NAME, default=options.leaf_display_name
            ): str,
            vol.Required(
                CONF_LEAF_OFFSET, default=options.leaf_offset_c
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_LEAF_OFFSET,
                    max=MAX_LEAF_OFFSET,
                    step=0.1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="°C",
                )
            ),
            vol.Required(
                CONF_ABSOLUTE_HUMIDITY_ICON,
                default=options.absolute_humidity_icon,
            ): IconSelector(
                IconSelectorConfig(placeholder=DEFAULT_ABSOLUTE_HUMIDITY_ICON)
            ),
            vol.Required(
                CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
                default=options.absolute_humidity_display_name,
            ): str,
            vol.Required(
                CONF_DEW_POINT_ICON,
                default=options.dew_point_icon,
            ): IconSelector(IconSelectorConfig(placeholder=DEFAULT_DEW_POINT_ICON)),
            vol.Required(
                CONF_DEW_POINT_DISPLAY_NAME,
                default=options.dew_point_display_name,
            ): str,
        }
    )


def build_scoped_policy_schema(
    *,
    scope_id: str = "",
    policy: dict[str, Any] | None = None,
    include_scope_id: bool,
) -> vol.Schema:
    """Build schema for area/device behavior override editing."""
    policy = dict(policy or {})
    schema: dict[Any, Any] = {}
    if include_scope_id:
        schema[vol.Required("scope_id", default=scope_id)] = str

    schema.update(
        {
            vol.Required(
                CONF_ENABLE_AIR,
                default=bool(policy.get(CONF_ENABLE_AIR, DEFAULT_ENABLE_AIR)),
            ): bool,
            vol.Required(
                CONF_ENABLE_LEAF,
                default=bool(policy.get(CONF_ENABLE_LEAF, DEFAULT_ENABLE_LEAF)),
            ): bool,
            vol.Required(
                CONF_ENABLE_ABSOLUTE_HUMIDITY,
                default=bool(
                    policy.get(
                        CONF_ENABLE_ABSOLUTE_HUMIDITY, DEFAULT_ENABLE_ABSOLUTE_HUMIDITY
                    )
                ),
            ): bool,
            vol.Required(
                CONF_ENABLE_DEW_POINT,
                default=bool(
                    policy.get(CONF_ENABLE_DEW_POINT, DEFAULT_ENABLE_DEW_POINT)
                ),
            ): bool,
            vol.Required(
                CONF_LEAF_OFFSET,
                default=float(policy.get(CONF_LEAF_OFFSET, DEFAULT_LEAF_OFFSET)),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_LEAF_OFFSET,
                    max=MAX_LEAF_OFFSET,
                    step=0.1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="°C",
                )
            ),
        }
    )
    return vol.Schema(schema)


def normalize_scoped_policy_input(
    user_input: dict[str, Any],
    *,
    include_scope_id: bool,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Normalize area/device policy form input."""
    normalized: dict[str, Any] = {}
    errors: dict[str, str] = {}

    if include_scope_id:
        try:
            normalized["scope_id"] = trimmed_nonempty_string(
                user_input.get("scope_id"), "invalid_scope_id"
            )
        except vol.Invalid as err:
            errors["scope_id"] = str(err)

    for key in (
        CONF_ENABLE_AIR,
        CONF_ENABLE_LEAF,
        CONF_ENABLE_ABSOLUTE_HUMIDITY,
        CONF_ENABLE_DEW_POINT,
    ):
        normalized[key] = bool(user_input[key])

    try:
        normalized[CONF_LEAF_OFFSET] = validated_leaf_offset(
            user_input[CONF_LEAF_OFFSET]
        )
    except vol.Invalid as err:
        errors[CONF_LEAF_OFFSET] = str(err)

    return normalized, errors


def normalize_user_input(
    user_input: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    """Normalize validated config/options form input."""
    normalized_input = dict(user_input)
    errors: dict[str, str] = {}

    field_error_map = {
        CONF_ICON: "invalid_icon",
        CONF_DISPLAY_NAME: "invalid_display_name",
        CONF_LEAF_ICON: "invalid_leaf_icon",
        CONF_LEAF_DISPLAY_NAME: "invalid_leaf_display_name",
        CONF_ABSOLUTE_HUMIDITY_ICON: "invalid_absolute_humidity_icon",
        CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME: "invalid_absolute_humidity_display_name",
        CONF_DEW_POINT_ICON: "invalid_dew_point_icon",
        CONF_DEW_POINT_DISPLAY_NAME: "invalid_dew_point_display_name",
    }

    for field_name, error_key in field_error_map.items():
        try:
            normalized_input[field_name] = trimmed_nonempty_string(
                user_input[field_name], error_key
            )
        except vol.Invalid as err:
            errors[field_name] = str(err)

    try:
        normalized_input[CONF_LEAF_OFFSET] = validated_leaf_offset(
            user_input[CONF_LEAF_OFFSET]
        )
    except vol.Invalid as err:
        errors[CONF_LEAF_OFFSET] = str(err)

    return normalized_input, errors


def normalize_source_override_input(
    user_input: dict[str, Any],
) -> tuple[dict[str, str | None], dict[str, str]]:
    """Normalize manual source override input for one device."""
    normalized: dict[str, str | None] = {
        "temperature_entity_id": None,
        "humidity_entity_id": None,
    }
    errors: dict[str, str] = {}

    for field_name in ("temperature_entity_id", "humidity_entity_id"):
        raw_value = user_input.get(field_name)
        if raw_value in (None, ""):
            continue
        if not isinstance(raw_value, str):
            errors[field_name] = "invalid_source_entity_id"
            continue
        normalized_value = raw_value.strip()
        if not normalized_value.startswith("sensor."):
            errors[field_name] = "invalid_source_entity_id"
            continue
        normalized[field_name] = normalized_value

    if not normalized["temperature_entity_id"] and not normalized["humidity_entity_id"]:
        errors["base"] = "missing_source_override"

    return normalized, errors
