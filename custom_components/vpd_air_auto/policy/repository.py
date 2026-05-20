"""Repository/parser for V2 policy dictionaries."""

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
from .models import DisplayPolicy, GlobalPolicy, ScopedPolicyOverride, SourceOverride


class PolicyRepository:
    """Typed repository for the V2 policy tree."""

    def __init__(self, raw: Mapping[str, Any] | None = None) -> None:
        """Parse raw policy data into typed policy models."""
        self._raw: Mapping[str, Any] = raw or {}
        self._global_policy = self._parse_global_policy(self._raw.get("global_policy"))
        self._area_policies = self._parse_scoped_map(self._raw.get("area_policies"))
        self._device_policies = self._parse_scoped_map(self._raw.get("device_policies"))
        self._source_overrides = self._parse_source_map(self._raw.get("source_overrides"))

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
        """Return normalized dictionary form."""
        return {
            "global_policy": asdict(self._global_policy),
            "area_policies": {key: asdict(value) for key, value in self._area_policies.items()},
            "device_policies": {key: asdict(value) for key, value in self._device_policies.items()},
            "source_overrides": {
                key: asdict(value) for key, value in self._source_overrides.items()
            },
        }

    def _parse_global_policy(self, raw_global: Any) -> GlobalPolicy:
        data = raw_global if isinstance(raw_global, Mapping) else {}
        display = DisplayPolicy(
            icon=str(data.get(CONF_ICON, DisplayPolicy.icon)),
            display_name=str(data.get(CONF_DISPLAY_NAME, DisplayPolicy.display_name)),
            leaf_icon=str(data.get(CONF_LEAF_ICON, DisplayPolicy.leaf_icon)),
            leaf_display_name=str(
                data.get(CONF_LEAF_DISPLAY_NAME, DisplayPolicy.leaf_display_name)
            ),
            absolute_humidity_icon=str(
                data.get(
                    CONF_ABSOLUTE_HUMIDITY_ICON,
                    DisplayPolicy.absolute_humidity_icon,
                )
            ),
            absolute_humidity_display_name=str(
                data.get(
                    CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
                    DisplayPolicy.absolute_humidity_display_name,
                )
            ),
            dew_point_icon=str(data.get(CONF_DEW_POINT_ICON, DisplayPolicy.dew_point_icon)),
            dew_point_display_name=str(
                data.get(CONF_DEW_POINT_DISPLAY_NAME, DisplayPolicy.dew_point_display_name)
            ),
        )
        return GlobalPolicy(
            enable_air=bool(data.get(CONF_ENABLE_AIR, GlobalPolicy.enable_air)),
            enable_leaf=bool(data.get(CONF_ENABLE_LEAF, GlobalPolicy.enable_leaf)),
            enable_absolute_humidity=bool(
                data.get(CONF_ENABLE_ABSOLUTE_HUMIDITY, GlobalPolicy.enable_absolute_humidity)
            ),
            enable_dew_point=bool(data.get(CONF_ENABLE_DEW_POINT, GlobalPolicy.enable_dew_point)),
            leaf_offset_c=float(data.get(CONF_LEAF_OFFSET, GlobalPolicy.leaf_offset_c)),
            display=display,
        )

    def _parse_scoped_map(self, raw_map: Any) -> dict[str, ScopedPolicyOverride]:
        if not isinstance(raw_map, Mapping):
            return {}

        parsed: dict[str, ScopedPolicyOverride] = {}
        for scope_id, scope_raw in raw_map.items():
            if not isinstance(scope_id, str) or not isinstance(scope_raw, Mapping):
                continue
            parsed[scope_id] = ScopedPolicyOverride(
                enable_air=self._optional_bool(scope_raw.get(CONF_ENABLE_AIR)),
                enable_leaf=self._optional_bool(scope_raw.get(CONF_ENABLE_LEAF)),
                enable_absolute_humidity=self._optional_bool(
                    scope_raw.get(CONF_ENABLE_ABSOLUTE_HUMIDITY)
                ),
                enable_dew_point=self._optional_bool(scope_raw.get(CONF_ENABLE_DEW_POINT)),
                leaf_offset_c=self._optional_float(scope_raw.get(CONF_LEAF_OFFSET)),
            )
        return parsed

    def _parse_source_map(self, raw_map: Any) -> dict[str, SourceOverride]:
        if not isinstance(raw_map, Mapping):
            return {}

        parsed: dict[str, SourceOverride] = {}
        for device_id, override_raw in raw_map.items():
            if not isinstance(device_id, str) or not isinstance(override_raw, Mapping):
                continue
            parsed[device_id] = SourceOverride(
                temperature_entity_id=self._optional_str(
                    override_raw.get("temperature_entity_id")
                ),
                humidity_entity_id=self._optional_str(
                    override_raw.get("humidity_entity_id")
                ),
            )
        return parsed

    def _optional_bool(self, value: Any) -> bool | None:
        if value is None:
            return None
        return bool(value)

    def _optional_float(self, value: Any) -> float | None:
        if value is None:
            return None
        return float(value)

    def _optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        return str(value)
