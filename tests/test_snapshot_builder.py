"""Tests for snapshot builder service."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.vpd_air_auto.const import IntegrationOptions
from custom_components.vpd_air_auto.models import DeviceTopology
from custom_components.vpd_air_auto.services.snapshot_builder import SnapshotBuilder


def _options() -> IntegrationOptions:
    return IntegrationOptions(
        scan_interval_seconds=300,
        enable_air=True,
        enable_leaf=True,
        enable_absolute_humidity=True,
        enable_dew_point=True,
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


def test_build_snapshot_returns_expected_values(hass: HomeAssistant) -> None:
    """Build snapshot with valid temperature and humidity states."""
    hass.states.async_set(
        "sensor.grow_tent_temperature", "25", {"device_class": "temperature"}
    )
    hass.states.async_set(
        "sensor.grow_tent_humidity", "60", {"device_class": "humidity"}
    )

    builder = SnapshotBuilder(hass, _options())
    snapshot = builder.build_snapshot(
        DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
            blocked_sensor_kinds=frozenset(),
        )
    )

    assert snapshot.temperature_c == 25.0
    assert snapshot.humidity_pct == 60.0
    assert snapshot.leaf_offset_c == -2.0
    assert snapshot.leaf_temperature_c == 23.0
    assert snapshot.dew_point_c == 16.68
    assert snapshot.vpd_air_kpa == 1.27
    assert snapshot.vpd_leaf_kpa == 1.58
    assert snapshot.absolute_humidity_gm3 == 13.8


def test_build_snapshot_handles_invalid_source_states(hass: HomeAssistant) -> None:
    """Build snapshot with non-numeric source states."""
    hass.states.async_set("sensor.grow_tent_temperature", "unknown")
    hass.states.async_set("sensor.grow_tent_humidity", "not_a_number")

    builder = SnapshotBuilder(hass, _options())
    snapshot = builder.build_snapshot(
        DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
            blocked_sensor_kinds=frozenset(),
        )
    )

    assert snapshot.temperature_c is None
    assert snapshot.humidity_pct is None
    assert snapshot.leaf_temperature_c is None
    assert snapshot.dew_point_c is None
    assert snapshot.vpd_air_kpa is None
    assert snapshot.vpd_leaf_kpa is None
    assert snapshot.absolute_humidity_gm3 is None
