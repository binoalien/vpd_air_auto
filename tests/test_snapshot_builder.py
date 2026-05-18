"""Tests for the snapshot builder service."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.vpd_air_auto.models import DeviceTopology
from custom_components.vpd_air_auto.services.snapshot_builder import SnapshotBuilder


def test_build_snapshot_computes_all_values(hass: HomeAssistant) -> None:
    """Test build snapshot computes all values."""
    builder = SnapshotBuilder(hass, -2.0)
    topology = DeviceTopology(
        device_id="device-1",
        device_name="Grow Tent",
        temperature_entity_id="sensor.grow_tent_temperature",
        humidity_entity_id="sensor.grow_tent_humidity",
    )
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

    snapshot = builder.build_snapshot(topology)

    assert snapshot.temperature_c == 25.0
    assert snapshot.humidity_pct == 60.0
    assert snapshot.leaf_temperature_c == 23.0
    assert snapshot.vpd_air_kpa is not None
    assert snapshot.vpd_leaf_kpa is not None
    assert snapshot.absolute_humidity_gm3 is not None
