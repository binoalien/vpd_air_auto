"""Pure-Python parser/repository for V2 policy dictionaries."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

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
)

from .models import DisplayPolicy, GlobalPolicy, ScopedPolicyOverride, SourceOverride


class PolicyRepository:
    """Load and expose typed policy models from a nested mapping."""

    def __init__(self, raw: Mapping[str, Any] | None = None) -> None:
        """Initialize repository with optional raw mapping."""
        self._raw = dict(raw or {})
        self._global_policy = self._parse_global_policy(self._mapping("global_policy"))
        self._area_policies = self._parse_scoped_map(self._mapping("area_policies"))
        self._device_policies = self._parse_scoped_map(self._mapping("device_policies"))
        self._source_overrides = self._parse_source_map(
            self._mapping("source_overrides")
        )

    @property
    def global_policy(self) -> GlobalPolicy:
        """Return global defaults."""
        return self._global_policy

    @property
    def area_policies(self) -> Mapping[str, ScopedPolicyOverride]:
        """Return per-area overrides."""
        return self._area_policies

    @property
    def device_policies(self) -> Mapping[str, ScopedPolicyOverride]:
        """Return per-device overrides."""
        return self._device_policies

    @property
    def source_overrides(self) -> Mapping[str, SourceOverride]:
        """Return per-device source override models."""
        return self._source_overrides

    def as_dict(self) -> dict[str, Any]:
        """Serialize repository state into nested dictionary form."""
        return {
            "global_policy": asdict(self._global_policy),
            "area_policies": {
                key: asdict(value) for key, value in self._area_policies.items()
            },
            "device_policies": {
                key: asdict(value) for key, value in self._device_policies.items()
            },
            "source_overrides": {
                key: asdict(value) for key, value in self._source_overrides.items()
            },
        }

    def _mapping(self, key: str) -> dict[str, Any]:
        return self._mapping_or_empty(self._raw.get(key))

    def _parse_global_policy(self, raw_global: Mapping[str, Any]) -> GlobalPolicy:
        display_defaults = DisplayPolicy()
        return GlobalPolicy(
            enable_air=self._as_bool_or_default(
                raw_global.get(CONF_ENABLE_AIR),
                True,
            ),
            enable_leaf=self._as_bool_or_default(
                raw_global.get(CONF_ENABLE_LEAF),
                True,
            ),
            enable_absolute_humidity=self._as_bool_or_default(
                raw_global.get(CONF_ENABLE_ABSOLUTE_HUMIDITY),
                True,
            ),
            enable_dew_point=self._as_bool_or_default(
                raw_global.get(CONF_ENABLE_DEW_POINT),
                True,
            ),
            leaf_offset_c=self._float_or_default(
                raw_global.get(CONF_LEAF_OFFSET),
                -2.0,
            ),
            display=DisplayPolicy(
                icon=self._str_or_default(raw_global.get(CONF_ICON), display_defaults.icon),
                display_name=self._str_or_default(
                    raw_global.get(CONF_DISPLAY_NAME),
                    display_defaults.display_name,
                ),
                leaf_icon=self._str_or_default(
                    raw_global.get(CONF_LEAF_ICON), display_defaults.leaf_icon
                ),
                leaf_display_name=self._str_or_default(
                    raw_global.get(CONF_LEAF_DISPLAY_NAME),
                    display_defaults.leaf_display_name,
                ),
                absolute_humidity_icon=self._str_or_default(
                    raw_global.get(CONF_ABSOLUTE_HUMIDITY_ICON),
                    display_defaults.absolute_humidity_icon,
                ),
                absolute_humidity_display_name=self._str_or_default(
                    raw_global.get(CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME),
                    display_defaults.absolute_humidity_display_name,
                ),
                dew_point_icon=self._str_or_default(
                    raw_global.get(CONF_DEW_POINT_ICON), display_defaults.dew_point_icon
                ),
                dew_point_display_name=self._str_or_default(
                    raw_global.get(CONF_DEW_POINT_DISPLAY_NAME),
                    display_defaults.dew_point_display_name,
                ),
            ),
        )

    def _parse_scoped_map(
        self,
        scoped: Mapping[str, Any],
    ) -> dict[str, ScopedPolicyOverride]:
        parsed: dict[str, ScopedPolicyOverride] = {}
        for scope_id, value in scoped.items():
            if not isinstance(scope_id, str) or not isinstance(value, Mapping):
                continue
            parsed[scope_id] = ScopedPolicyOverride(
                enable_air=self._as_optional_bool(value.get(CONF_ENABLE_AIR)),
                enable_leaf=self._as_optional_bool(value.get(CONF_ENABLE_LEAF)),
                enable_absolute_humidity=self._as_optional_bool(
                    value.get(CONF_ENABLE_ABSOLUTE_HUMIDITY)
                ),
                enable_dew_point=self._as_optional_bool(
                    value.get(CONF_ENABLE_DEW_POINT)
                ),
                leaf_offset_c=self._optional_float(value.get(CONF_LEAF_OFFSET)),
            )
        return parsed

    def _parse_source_map(self, scoped: Mapping[str, Any]) -> dict[str, SourceOverride]:
        parsed: dict[str, SourceOverride] = {}
        for device_id, value in scoped.items():
            if not isinstance(device_id, str) or not isinstance(value, Mapping):
                continue
            parsed[device_id] = SourceOverride(
                temperature_entity_id=self._entity_id_or_none(
                    value.get("temperature_entity_id")
                ),
                humidity_entity_id=self._entity_id_or_none(value.get("humidity_entity_id")),
            )
        return parsed

    @staticmethod
    def _as_bool_or_default(value: Any, default: bool) -> bool:
        """Return bool only for real bool input, otherwise fallback default."""
        return value if isinstance(value, bool) else default

    @staticmethod
    def _as_optional_bool(value: Any) -> bool | None:
        """Return bool only for real bool input, otherwise None."""
        return value if isinstance(value, bool) else None

    @staticmethod
    def _mapping_or_empty(value: Any) -> dict[str, Any]:
        return dict(value) if isinstance(value, Mapping) else {}

    @staticmethod
    def _float_or_default(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _str_or_default(value: Any, default: str) -> str:
        normalized = PolicyRepository._optional_str(value)
        return normalized if normalized is not None else default

    @staticmethod
    def _entity_id_or_none(value: Any) -> str | None:
        return PolicyRepository._optional_str(value)
