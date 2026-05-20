"""Policy repository/parser for V2 policy dictionaries."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from ..const import (
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
)
from .models import (
    DisplayPolicy,
    GlobalPolicy,
    ScopedPolicyOverride,
    SourceOverride,
)

DISPLAY_POLICY_KEY = "display_policy"
GLOBAL_POLICY_KEY = "global_policy"
AREA_POLICIES_KEY = "area_policies"
DEVICE_POLICIES_KEY = "device_policies"
SOURCE_OVERRIDES_KEY = "source_overrides"
TEMPERATURE_ENTITY_ID_KEY = "temperature_entity_id"
HUMIDITY_ENTITY_ID_KEY = "humidity_entity_id"


class PolicyRepository:
    """Typed access to raw V2 policy dictionaries."""

    def __init__(self, raw: Mapping[str, Any] | None = None) -> None:
        self._raw = dict(raw or {})
        self._global_policy = self._parse_global_policy(self._raw)
        self._area_policies = self._parse_scoped_map(self._raw.get(AREA_POLICIES_KEY))
        self._device_policies = self._parse_scoped_map(
            self._raw.get(DEVICE_POLICIES_KEY)
        )
        self._source_overrides = self._parse_source_override_map(
            self._raw.get(SOURCE_OVERRIDES_KEY)
        )

    @property
    def global_policy(self) -> GlobalPolicy:
        return self._global_policy

    @property
    def area_policies(self) -> Mapping[str, ScopedPolicyOverride]:
        return self._area_policies

    @property
    def device_policies(self) -> Mapping[str, ScopedPolicyOverride]:
        return self._device_policies

    @property
    def source_overrides(self) -> Mapping[str, SourceOverride]:
        return self._source_overrides

    def as_dict(self) -> dict[str, Any]:
        return {
            GLOBAL_POLICY_KEY: {
                CONF_ENABLE_AIR: self.global_policy.enable_air,
                CONF_ENABLE_LEAF: self.global_policy.enable_leaf,
                CONF_ENABLE_ABSOLUTE_HUMIDITY: self.global_policy.enable_absolute_humidity,
                CONF_ENABLE_DEW_POINT: self.global_policy.enable_dew_point,
                CONF_LEAF_OFFSET: self.global_policy.leaf_offset_c,
            },
            DISPLAY_POLICY_KEY: asdict(self.global_policy.display),
            AREA_POLICIES_KEY: {
                key: _scoped_policy_to_dict(value)
                for key, value in self.area_policies.items()
            },
            DEVICE_POLICIES_KEY: {
                key: _scoped_policy_to_dict(value)
                for key, value in self.device_policies.items()
            },
            SOURCE_OVERRIDES_KEY: {
                key: asdict(value) for key, value in self.source_overrides.items()
            },
        }

    def _parse_global_policy(self, raw: Mapping[str, Any]) -> GlobalPolicy:
        display_raw = _as_mapping(raw.get(DISPLAY_POLICY_KEY))
        global_raw = _as_mapping(raw.get(GLOBAL_POLICY_KEY))
        display = DisplayPolicy(
            icon=_as_str_or_default(display_raw.get(CONF_ICON), DisplayPolicy().icon),
            display_name=_as_str_or_default(
                display_raw.get(CONF_DISPLAY_NAME), DisplayPolicy().display_name
            ),
            leaf_icon=_as_str_or_default(
                display_raw.get(CONF_LEAF_ICON), DisplayPolicy().leaf_icon
            ),
            leaf_display_name=_as_str_or_default(
                display_raw.get(CONF_LEAF_DISPLAY_NAME), DisplayPolicy().leaf_display_name
            ),
            absolute_humidity_icon=_as_str_or_default(
                display_raw.get(CONF_ABSOLUTE_HUMIDITY_ICON),
                DisplayPolicy().absolute_humidity_icon,
            ),
            absolute_humidity_display_name=_as_str_or_default(
                display_raw.get(CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME),
                DisplayPolicy().absolute_humidity_display_name,
            ),
            dew_point_icon=_as_str_or_default(
                display_raw.get(CONF_DEW_POINT_ICON), DisplayPolicy().dew_point_icon
            ),
            dew_point_display_name=_as_str_or_default(
                display_raw.get(CONF_DEW_POINT_DISPLAY_NAME),
                DisplayPolicy().dew_point_display_name,
            ),
        )
        return GlobalPolicy(
            enable_air=_as_bool_or_default(
                global_raw.get(CONF_ENABLE_AIR), GlobalPolicy().enable_air
            ),
            enable_leaf=_as_bool_or_default(
                global_raw.get(CONF_ENABLE_LEAF), GlobalPolicy().enable_leaf
            ),
            enable_absolute_humidity=_as_bool_or_default(
                global_raw.get(CONF_ENABLE_ABSOLUTE_HUMIDITY),
                GlobalPolicy().enable_absolute_humidity,
            ),
            enable_dew_point=_as_bool_or_default(
                global_raw.get(CONF_ENABLE_DEW_POINT), GlobalPolicy().enable_dew_point
            ),
            leaf_offset_c=_as_float_or_default(
                global_raw.get(CONF_LEAF_OFFSET), GlobalPolicy().leaf_offset_c
            ),
            display=display,
        )

    def _parse_scoped_map(self, raw: Any) -> dict[str, ScopedPolicyOverride]:
        raw_mapping = _as_mapping(raw)
        output: dict[str, ScopedPolicyOverride] = {}
        for key, value in raw_mapping.items():
            if not isinstance(key, str):
                continue
            item = _as_mapping(value)
            output[key] = ScopedPolicyOverride(
                enable_air=_as_optional_bool(item.get(CONF_ENABLE_AIR)),
                enable_leaf=_as_optional_bool(item.get(CONF_ENABLE_LEAF)),
                enable_absolute_humidity=_as_optional_bool(
                    item.get(CONF_ENABLE_ABSOLUTE_HUMIDITY)
                ),
                enable_dew_point=_as_optional_bool(item.get(CONF_ENABLE_DEW_POINT)),
                leaf_offset_c=_as_optional_float(item.get(CONF_LEAF_OFFSET)),
            )
        return output

    def _parse_source_override_map(self, raw: Any) -> dict[str, SourceOverride]:
        raw_mapping = _as_mapping(raw)
        output: dict[str, SourceOverride] = {}
        for key, value in raw_mapping.items():
            if not isinstance(key, str):
                continue
            item = _as_mapping(value)
            output[key] = SourceOverride(
                temperature_entity_id=_as_optional_str(
                    item.get(TEMPERATURE_ENTITY_ID_KEY)
                ),
                humidity_entity_id=_as_optional_str(item.get(HUMIDITY_ENTITY_ID_KEY)),
            )
        return output


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_bool_or_default(value: Any, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _as_optional_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _as_float_or_default(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_str_or_default(value: Any, default: str) -> str:
    return value if isinstance(value, str) and value else default


def _as_optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _scoped_policy_to_dict(policy: ScopedPolicyOverride) -> dict[str, Any]:
    return {
        CONF_ENABLE_AIR: policy.enable_air,
        CONF_ENABLE_LEAF: policy.enable_leaf,
        CONF_ENABLE_ABSOLUTE_HUMIDITY: policy.enable_absolute_humidity,
        CONF_ENABLE_DEW_POINT: policy.enable_dew_point,
        CONF_LEAF_OFFSET: policy.leaf_offset_c,
    }
