"""Tests for entity planning service."""

from __future__ import annotations

from custom_components.vpd_air_auto.const import (
    SENSOR_KIND_ABSOLUTE_HUMIDITY,
    SENSOR_KIND_AIR,
    SENSOR_KIND_DEW_POINT,
    SENSOR_KIND_LEAF,
    IntegrationOptions,
)
from custom_components.vpd_air_auto.models import DeviceTopology
from custom_components.vpd_air_auto.services.entity_plan import EntityPlanService


def _options(
    *,
    enable_air: bool = True,
    enable_leaf: bool = True,
    enable_absolute_humidity: bool = True,
    enable_dew_point: bool = True,
) -> IntegrationOptions:
    return IntegrationOptions(
        scan_interval_seconds=300,
        enable_air=enable_air,
        enable_leaf=enable_leaf,
        enable_absolute_humidity=enable_absolute_humidity,
        enable_dew_point=enable_dew_point,
        icon="mdi:water-opacity",
        display_name="VPDair",
        leaf_icon="mdi:leaf",
        leaf_display_name="VPDleaf",
        leaf_offset_c=-2.0,
        absolute_humidity_icon="mdi:water",
        absolute_humidity_display_name="Absolute Humidity",
        dew_point_icon="mdi:thermometer-water",
        dew_point_display_name="Dew Point",
    )


def test_enabled_kinds_reflects_integration_options() -> None:
    """Test enabled kinds are derived from integration options."""
    service = EntityPlanService(
        _options(enable_air=True, enable_leaf=False, enable_absolute_humidity=True)
    )

    assert service.enabled_kinds() == {
        SENSOR_KIND_AIR,
        SENSOR_KIND_ABSOLUTE_HUMIDITY,
        SENSOR_KIND_DEW_POINT,
    }


def test_creatable_kinds_for_topology_removes_blocked_kinds() -> None:
    """Test creatable kinds are enabled kinds minus blocked kinds."""
    service = EntityPlanService(_options())
    topology = DeviceTopology(
        device_id="device-1",
        device_name="Grow Tent",
        temperature_entity_id="sensor.grow_tent_temperature",
        humidity_entity_id="sensor.grow_tent_humidity",
        blocked_sensor_kinds=frozenset({SENSOR_KIND_LEAF, SENSOR_KIND_DEW_POINT}),
    )

    assert service.creatable_kinds_for_topology(topology) == {
        SENSOR_KIND_AIR,
        SENSOR_KIND_ABSOLUTE_HUMIDITY,
    }


def test_creatable_kinds_for_topology_returns_empty_for_missing_topology() -> None:
    """Test missing topology yields no creatable kinds."""
    service = EntityPlanService(_options())

    assert service.creatable_kinds_for_topology(None) == set()


def test_creatable_kinds_for_topology_uses_effective_policy_over_global() -> None:
    """Test per-device policy input overrides global enabled kinds during planning."""
    from custom_components.vpd_air_auto.policy.models import EffectiveDevicePolicy, DisplayPolicy
    service = EntityPlanService(_options(enable_air=True, enable_leaf=True))
    topology = DeviceTopology(
        device_id="device-1",
        device_name="Grow Tent",
        temperature_entity_id="sensor.grow_tent_temperature",
        humidity_entity_id="sensor.grow_tent_humidity",
    )
    effective = EffectiveDevicePolicy(
        enable_air=False,
        enable_leaf=True,
        enable_absolute_humidity=False,
        enable_dew_point=False,
        leaf_offset_c=-1.0,
        display=DisplayPolicy(),
    )

    assert service.creatable_kinds_for_topology(topology, policy=effective) == {
        SENSOR_KIND_LEAF,
    }
