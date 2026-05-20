from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..const import DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME, DEFAULT_ABSOLUTE_HUMIDITY_ICON, DEFAULT_DEW_POINT_DISPLAY_NAME, DEFAULT_DEW_POINT_ICON, DEFAULT_DISPLAY_NAME, DEFAULT_ENABLE_ABSOLUTE_HUMIDITY, DEFAULT_ENABLE_AIR, DEFAULT_ENABLE_DEW_POINT, DEFAULT_ENABLE_LEAF, DEFAULT_ICON, DEFAULT_LEAF_DISPLAY_NAME, DEFAULT_LEAF_ICON, DEFAULT_LEAF_OFFSET
from .models import DisplayPolicy, GlobalPolicy, ScopedPolicyOverride, SourceOverride


class PolicyRepository:
    def __init__(self, raw: Mapping[str, Any] | None = None) -> None:
        self._raw = dict(raw or {})
        self._global_policy = self._parse_global_policy()
        self._area_policies = self._parse_scoped_overrides("area_policies")
        self._device_policies = self._parse_scoped_overrides("device_policies")
        self._source_overrides = self._parse_source_overrides()

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
        return dict(self._raw)

    def _parse_global_policy(self) -> GlobalPolicy:
        return GlobalPolicy(
            enable_air=bool(self._raw.get("enable_air", DEFAULT_ENABLE_AIR)),
            enable_leaf=bool(self._raw.get("enable_leaf", DEFAULT_ENABLE_LEAF)),
            enable_absolute_humidity=bool(self._raw.get("enable_absolute_humidity", DEFAULT_ENABLE_ABSOLUTE_HUMIDITY)),
            enable_dew_point=bool(self._raw.get("enable_dew_point", DEFAULT_ENABLE_DEW_POINT)),
            leaf_offset_c=float(self._raw.get("leaf_offset_c", DEFAULT_LEAF_OFFSET)),
            display=DisplayPolicy(
                icon=str(self._raw.get("icon", DEFAULT_ICON)),
                display_name=str(self._raw.get("display_name", DEFAULT_DISPLAY_NAME)),
                leaf_icon=str(self._raw.get("leaf_icon", DEFAULT_LEAF_ICON)),
                leaf_display_name=str(self._raw.get("leaf_display_name", DEFAULT_LEAF_DISPLAY_NAME)),
                absolute_humidity_icon=str(self._raw.get("absolute_humidity_icon", DEFAULT_ABSOLUTE_HUMIDITY_ICON)),
                absolute_humidity_display_name=str(self._raw.get("absolute_humidity_display_name", DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME)),
                dew_point_icon=str(self._raw.get("dew_point_icon", DEFAULT_DEW_POINT_ICON)),
                dew_point_display_name=str(self._raw.get("dew_point_display_name", DEFAULT_DEW_POINT_DISPLAY_NAME)),
            ),
        )

    def _parse_scoped_overrides(self, key: str) -> dict[str, ScopedPolicyOverride]:
        data = self._raw.get(key)
        if not isinstance(data, Mapping):
            return {}
        parsed: dict[str, ScopedPolicyOverride] = {}
        for scope_id, value in data.items():
            if not isinstance(scope_id, str) or not isinstance(value, Mapping):
                continue
            parsed[scope_id] = ScopedPolicyOverride(
                enable_air=self._as_optional_bool(value.get("enable_air")),
                enable_leaf=self._as_optional_bool(value.get("enable_leaf")),
                enable_absolute_humidity=self._as_optional_bool(value.get("enable_absolute_humidity")),
                enable_dew_point=self._as_optional_bool(value.get("enable_dew_point")),
                leaf_offset_c=self._as_optional_float(value.get("leaf_offset_c")),
            )
        return parsed

    def _parse_source_overrides(self) -> dict[str, SourceOverride]:
        data = self._raw.get("source_overrides")
        if not isinstance(data, Mapping):
            return {}
        parsed: dict[str, SourceOverride] = {}
        for device_id, value in data.items():
            if not isinstance(device_id, str) or not isinstance(value, Mapping):
                continue
            parsed[device_id] = SourceOverride(
                temperature_entity_id=self._as_optional_str(value.get("temperature_entity_id")),
                humidity_entity_id=self._as_optional_str(value.get("humidity_entity_id")),
            )
        return parsed

    @staticmethod
    def _as_optional_bool(value: Any) -> bool | None:
        return None if value is None else bool(value)

    @staticmethod
    def _as_optional_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_optional_str(value: Any) -> str | None:
        return None if value is None else str(value)
