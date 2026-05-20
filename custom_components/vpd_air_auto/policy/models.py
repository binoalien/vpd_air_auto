"""Dataclass models for V2 policy representation and resolution."""

from __future__ import annotations

from dataclasses import dataclass

from custom_components.vpd_air_auto.const import (
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
)


@dataclass(frozen=True, slots=True)
class DisplayPolicy:
    """Global presentation policy for all generated helper sensors."""

    icon: str = DEFAULT_ICON
    display_name: str = DEFAULT_DISPLAY_NAME
    leaf_icon: str = DEFAULT_LEAF_ICON
    leaf_display_name: str = DEFAULT_LEAF_DISPLAY_NAME
    absolute_humidity_icon: str = DEFAULT_ABSOLUTE_HUMIDITY_ICON
    absolute_humidity_display_name: str = DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME
    dew_point_icon: str = DEFAULT_DEW_POINT_ICON
    dew_point_display_name: str = DEFAULT_DEW_POINT_DISPLAY_NAME


@dataclass(frozen=True, slots=True)
class GlobalPolicy:
    """Global behavior and display defaults."""

    enable_air: bool = DEFAULT_ENABLE_AIR
    enable_leaf: bool = DEFAULT_ENABLE_LEAF
    enable_absolute_humidity: bool = DEFAULT_ENABLE_ABSOLUTE_HUMIDITY
    enable_dew_point: bool = DEFAULT_ENABLE_DEW_POINT
    leaf_offset_c: float = DEFAULT_LEAF_OFFSET
    display: DisplayPolicy = DisplayPolicy()


@dataclass(frozen=True, slots=True)
class ScopedPolicyOverride:
    """Optional behavior overrides for area and device scopes."""

    enable_air: bool | None = None
    enable_leaf: bool | None = None
    enable_absolute_humidity: bool | None = None
    enable_dew_point: bool | None = None
    leaf_offset_c: float | None = None


@dataclass(frozen=True, slots=True)
class SourceOverride:
    """Optional manually selected source entities for a device."""

    temperature_entity_id: str | None = None
    humidity_entity_id: str | None = None


@dataclass(frozen=True, slots=True)
class EffectiveDevicePolicy:
    """Resolved effective behavior for one target device."""

    enable_air: bool
    enable_leaf: bool
    enable_absolute_humidity: bool
    enable_dew_point: bool
    leaf_offset_c: float
    display: DisplayPolicy
    source_override: SourceOverride | None = None
    behavior_source: str = "global"
    leaf_offset_source: str = "global"
