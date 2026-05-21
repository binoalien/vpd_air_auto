"""Tests for the snapshot builder service."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.vpd_air_auto.models import DeviceTopology
from custom_components.vpd_air_auto.policy.models import (
    DisplayPolicy,
    EffectiveDevicePolicy,
)
from custom_components.vpd_air_auto.services.snapshot_builder import SnapshotBuilder


def _topology() -> DeviceTopology:
    return DeviceTopology(
        device_id="device-1",
        device_name="Grow Tent",
        temperature_entity_id="sensor.grow_tent_temperature",
        humidity_entity_id="sensor.grow_tent_humidity",
    )


def _policy(*, leaf_offset_c: float = -2.0) -> EffectiveDevicePolicy:
    return EffectiveDevicePolicy(
        enable_air=True,
        enable_leaf=True,
        enable_absolute_humidity=True,
        enable_dew_point=True,
        leaf_offset_c=leaf_offset_c,
        display=DisplayPolicy(),
    )


def test_build_snapshot_computes_all_values(hass: HomeAssistant) -> None:
    """Test build snapshot computes all values."""
    builder = SnapshotBuilder(hass)
    topology = _topology()
    hass.states.async_set(
        "sensor.grow_tent_temperature",
        "25.0",
        {"device_class": "temperature", "unit_of_measurement": "°C"},
    )
    hass.states.async_set(
        "sensor.grow_tent_humidity",
        "60.0",
        {"device_class": "humidity", "unit_of_measurement": "%"},
    )

    snapshot = builder.build_snapshot(topology, _policy())

    assert snapshot.device_id == "device-1"
    assert snapshot.device_name == "Grow Tent"
    assert snapshot.temperature_entity_id == "sensor.grow_tent_temperature"
    assert snapshot.humidity_entity_id == "sensor.grow_tent_humidity"
    assert snapshot.temperature_c == 25.0
    assert snapshot.humidity_pct == 60.0
    assert snapshot.leaf_offset_c == -2.0
    assert snapshot.leaf_temperature_c == 23.0
    assert snapshot.dew_point_c == 16.698
    assert snapshot.vpd_air_kpa == 1.267
    assert snapshot.vpd_leaf_kpa == 0.909
    assert snapshot.absolute_humidity_gm3 == 13.814


def test_build_snapshot_handles_invalid_source_states(hass: HomeAssistant) -> None:
    """Test build snapshot handles invalid source states."""
    builder = SnapshotBuilder(hass)
    topology = _topology()
    hass.states.async_set(
        "sensor.grow_tent_temperature",
        "unknown",
        {"device_class": "temperature", "unit_of_measurement": "°C"},
    )
    hass.states.async_set(
        "sensor.grow_tent_humidity",
        "invalid",
        {"device_class": "humidity", "unit_of_measurement": "%"},
    )

    snapshot = builder.build_snapshot(topology, _policy())

    assert snapshot.device_id == "device-1"
    assert snapshot.device_name == "Grow Tent"
    assert snapshot.temperature_entity_id == "sensor.grow_tent_temperature"
    assert snapshot.humidity_entity_id == "sensor.grow_tent_humidity"
    assert snapshot.temperature_c is None
    assert snapshot.humidity_pct is None
    assert snapshot.leaf_offset_c == -2.0
    assert snapshot.leaf_temperature_c is None
    assert snapshot.dew_point_c is None
    assert snapshot.vpd_air_kpa is None
    assert snapshot.vpd_leaf_kpa is None
    assert snapshot.absolute_humidity_gm3 is None
