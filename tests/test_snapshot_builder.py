"""Tests for SnapshotBuilder service."""

from homeassistant.core import HomeAssistant

from custom_components.vpd_air_auto.const import IntegrationOptions
from custom_components.vpd_air_auto.models import DeviceTopology
from custom_components.vpd_air_auto.services.snapshot_builder import SnapshotBuilder


def _options() -> IntegrationOptions:
    return IntegrationOptions(
        scan_interval_seconds=300,
        display_name="VPDair",
        leaf_display_name="VPDleaf",
        absolute_humidity_display_name="Absolute Humidity",
        dew_point_display_name="Dew Point",
        icon="mdi:water-opacity",
        leaf_icon="mdi:leaf",
        absolute_humidity_icon="mdi:water",
        dew_point_icon="mdi:thermometer-water",
        enable_air=True,
        enable_leaf=True,
        enable_absolute_humidity=True,
        enable_dew_point=True,
        leaf_offset_c=-2.0,
    )


def test_build_computes_all_values(hass: HomeAssistant) -> None:
    """SnapshotBuilder computes all expected derived values."""
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

    snapshot = SnapshotBuilder(hass, _options()).build(topology)

    assert snapshot.temperature_c == 25.0
    assert snapshot.humidity_pct == 60.0
    assert snapshot.leaf_temperature_c == 23.0
    assert snapshot.vpd_air_kpa is not None
    assert snapshot.vpd_leaf_kpa is not None
    assert snapshot.absolute_humidity_gm3 is not None
