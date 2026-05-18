"""Tests for topology discovery service."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from homeassistant.core import HomeAssistant

from custom_components.vpd_air_auto.const import (
    DOMAIN,
    SENSOR_KIND_ABSOLUTE_HUMIDITY,
    SENSOR_KIND_AIR,
    SENSOR_KIND_DEW_POINT,
    SENSOR_KIND_LEAF,
    IntegrationOptions,
)
from custom_components.vpd_air_auto.discovery.duplicates import DuplicateDetectionService
from custom_components.vpd_air_auto.discovery.topology import TopologyDiscoveryService


def _device(device_id: str, name: str = "Grow Tent") -> SimpleNamespace:
    return SimpleNamespace(id=device_id, name=name, name_by_user=None)


def _entry(  # pylint: disable=too-many-arguments
    entity_id: str,
    *,
    platform: str = "test_platform",
    name: str | None = None,
    original_name: str | None = None,
    original_device_class: str | None = None,
    original_unit_of_measurement: str | None = None,
    entity_category: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        entity_id=entity_id,
        domain="sensor",
        platform=platform,
        name=name,
        original_name=original_name,
        original_device_class=original_device_class,
        original_unit_of_measurement=original_unit_of_measurement,
        entity_category=entity_category,
    )


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


def _service(hass: HomeAssistant) -> TopologyDiscoveryService:
    return TopologyDiscoveryService(
        hass,
        DuplicateDetectionService(hass, _options()),
    )


def test_discover_selects_best_sources_and_blocks_duplicate_sensor_kinds(
    hass: HomeAssistant,
) -> None:
    """Discover selects best source entities and computes blocked kinds."""
    service = _service(hass)
    device = _device("device-1")
    device_registry = SimpleNamespace(devices={device.id: device})
    entity_registry = SimpleNamespace()

    entries = [
        _entry(
            "sensor.grow_tent_temp_aux",
            original_name="Aux Temp",
            original_device_class="temperature",
            original_unit_of_measurement="°C",
        ),
        _entry(
            "sensor.grow_tent_temperature",
            original_name="Grow Tent Temperature",
            original_device_class="temperature",
            original_unit_of_measurement="°C",
        ),
        _entry(
            "sensor.grow_tent_humidity_generic",
            original_name="Humidity Generic",
            original_device_class="humidity",
            original_unit_of_measurement="%",
        ),
        _entry(
            "sensor.grow_tent_humidity",
            original_name="Grow Tent Humidity",
            original_device_class="humidity",
            original_unit_of_measurement="%",
        ),
        _entry("sensor.grow_tent_vpdair_foreign", original_name="VPDair"),
        _entry("sensor.grow_tent_leaf_vpd_foreign", original_name="Leaf VPD"),
        _entry(
            "sensor.grow_tent_absolute_humidity_foreign",
            original_name="Absolute Humidity",
            original_device_class="absolute_humidity",
        ),
        _entry("sensor.grow_tent_dew_point_foreign", original_name="Dew Point"),
        _entry(
            "sensor.own_helper_should_be_ignored",
            platform=DOMAIN,
            original_name="VPDair",
            original_device_class="humidity",
        ),
    ]

    hass.states.async_set(
        "sensor.grow_tent_temperature",
        "25.0",
        {"device_class": "temperature", "unit_of_measurement": "%", "friendly_name": "Grow Tent Temperature"},
    )
    hass.states.async_set("sensor.grow_tent_temp_aux", "24.8", {"device_class": "temperature", "unit_of_measurement": "°C", "friendly_name": "Aux Temp"})
    hass.states.async_set("sensor.grow_tent_humidity", "60", {"device_class": "humidity", "unit_of_measurement": "%", "friendly_name": "Grow Tent Humidity"})
    hass.states.async_set("sensor.grow_tent_humidity_generic", "59", {"device_class": "humidity", "unit_of_measurement": "%", "friendly_name": "Humidity Generic"})
    hass.states.async_set("sensor.grow_tent_vpdair_foreign", "1.25", {"friendly_name": "VPDair"})
    hass.states.async_set("sensor.grow_tent_leaf_vpd_foreign", "1.50", {"friendly_name": "Leaf VPD"})
    hass.states.async_set("sensor.grow_tent_absolute_humidity_foreign", "13.8", {"device_class": "absolute_humidity", "friendly_name": "Absolute Humidity"})
    hass.states.async_set("sensor.grow_tent_dew_point_foreign", "16.6", {"friendly_name": "Dew Point", "unit_of_measurement": "°C", "device_class": "temperature"})

    with (
        patch("custom_components.vpd_air_auto.discovery.topology.dr.async_get", return_value=device_registry),
        patch("custom_components.vpd_air_auto.discovery.topology.er.async_get", return_value=entity_registry),
        patch("custom_components.vpd_air_auto.discovery.topology.er.async_entries_for_device", return_value=entries),
    ):
        topology = service.discover()

    assert topology["device-1"].temperature_entity_id == "sensor.grow_tent_temperature"
    assert topology["device-1"].humidity_entity_id == "sensor.grow_tent_humidity"
    assert topology["device-1"].blocked_sensor_kinds == frozenset(
        {
            SENSOR_KIND_AIR,
            SENSOR_KIND_LEAF,
            SENSOR_KIND_ABSOLUTE_HUMIDITY,
            SENSOR_KIND_DEW_POINT,
        }
    )


def test_discover_skips_devices_without_complete_source_pair(hass: HomeAssistant) -> None:
    """Discover skips devices without both source classes."""
    service = _service(hass)
    device = _device("device-1")
    device_registry = SimpleNamespace(devices={device.id: device})
    entity_registry = SimpleNamespace()
    entries = [
        _entry(
            "sensor.grow_tent_temperature",
            original_name="Grow Tent Temperature",
            original_device_class="temperature",
            original_unit_of_measurement="°C",
        )
    ]
    hass.states.async_set(
        "sensor.grow_tent_temperature",
        "25.0",
        {"device_class": "temperature", "unit_of_measurement": "°C"},
    )

    with (
        patch("custom_components.vpd_air_auto.discovery.topology.dr.async_get", return_value=device_registry),
        patch("custom_components.vpd_air_auto.discovery.topology.er.async_get", return_value=entity_registry),
        patch("custom_components.vpd_air_auto.discovery.topology.er.async_entries_for_device", return_value=entries),
    ):
        topology = service.discover()

    assert not topology
