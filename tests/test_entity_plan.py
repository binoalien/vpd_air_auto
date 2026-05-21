"""Tests for entity planning service."""

from __future__ import annotations

from custom_components.vpd_air_auto.const import (
    SENSOR_KIND_ABSOLUTE_HUMIDITY,
    SENSOR_KIND_AIR,
    SENSOR_KIND_DEW_POINT,
    SENSOR_KIND_LEAF,
)
from custom_components.vpd_air_auto.models import DeviceTopology
from custom_components.vpd_air_auto.policy.models import DisplayPolicy, EffectiveDevicePolicy
from custom_components.vpd_air_auto.services.entity_plan import EntityPlanService


def _policy(
    *,
    enable_air: bool = True,
    enable_leaf: bool = True,
    enable_absolute_humidity: bool = True,
    enable_dew_point: bool = True,
) -> EffectiveDevicePolicy:
    return EffectiveDevicePolicy(
        enable_air=enable_air,
        enable_leaf=enable_leaf,
        enable_absolute_humidity=enable_absolute_humidity,
        enable_dew_point=enable_dew_point,
        leaf_offset_c=-2.0,
        display=DisplayPolicy(),
    )


def test_enabled_kinds_for_policy() -> None:
    service = EntityPlanService()
    assert service.enabled_kinds_for_policy(
        _policy(enable_air=True, enable_leaf=False, enable_absolute_humidity=True)
    ) == {
        SENSOR_KIND_AIR,
        SENSOR_KIND_ABSOLUTE_HUMIDITY,
        SENSOR_KIND_DEW_POINT,
    }


def test_creatable_kinds_for_topology_removes_blocked_kinds() -> None:
    service = EntityPlanService()
    topology = DeviceTopology(
        device_id="device-1",
        device_name="Grow Tent",
        temperature_entity_id="sensor.grow_tent_temperature",
        humidity_entity_id="sensor.grow_tent_humidity",
        blocked_sensor_kinds=frozenset({SENSOR_KIND_LEAF, SENSOR_KIND_DEW_POINT}),
    )

    assert service.creatable_kinds_for_topology(topology, _policy()) == {
        SENSOR_KIND_AIR,
        SENSOR_KIND_ABSOLUTE_HUMIDITY,
    }


def test_creatable_kinds_for_topology_returns_empty_for_missing_topology() -> None:
    service = EntityPlanService()
    assert service.creatable_kinds_for_topology(None, _policy()) == set()
