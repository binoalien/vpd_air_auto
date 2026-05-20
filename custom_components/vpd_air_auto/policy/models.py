from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DisplayPolicy:
    icon: str
    display_name: str
    leaf_icon: str
    leaf_display_name: str
    absolute_humidity_icon: str
    absolute_humidity_display_name: str
    dew_point_icon: str
    dew_point_display_name: str


@dataclass(frozen=True, slots=True)
class GlobalPolicy:
    enable_air: bool
    enable_leaf: bool
    enable_absolute_humidity: bool
    enable_dew_point: bool
    leaf_offset_c: float
    display: DisplayPolicy


@dataclass(frozen=True, slots=True)
class ScopedPolicyOverride:
    enable_air: bool | None = None
    enable_leaf: bool | None = None
    enable_absolute_humidity: bool | None = None
    enable_dew_point: bool | None = None
    leaf_offset_c: float | None = None


@dataclass(frozen=True, slots=True)
class SourceOverride:
    temperature_entity_id: str | None = None
    humidity_entity_id: str | None = None


@dataclass(frozen=True, slots=True)
class EffectiveDevicePolicy:
    enable_air: bool
    enable_leaf: bool
    enable_absolute_humidity: bool
    enable_dew_point: bool
    leaf_offset_c: float
    display: DisplayPolicy
    source_override: SourceOverride | None = None
