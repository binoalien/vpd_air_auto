"""Internal data models for the VPD Air Auto integration."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class DeviceTopology:
    """The source entities selected for one Home Assistant device."""

    device_id: str
    device_name: str
    temperature_entity_id: str
    humidity_entity_id: str
    blocked_sensor_kinds: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True, slots=True)
class DeviceSnapshot:
    """Computed inputs and outputs for one Home Assistant device."""

    device_id: str
    device_name: str
    temperature_entity_id: str
    humidity_entity_id: str
    temperature_c: float | None
    humidity_pct: float | None
    leaf_offset_c: float
    leaf_temperature_c: float | None
    dew_point_c: float | None
    vpd_air_kpa: float | None
    vpd_leaf_kpa: float | None
    absolute_humidity_gm3: float | None
