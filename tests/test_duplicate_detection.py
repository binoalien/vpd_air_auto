"""Tests for duplicate detection service."""

from __future__ import annotations

from custom_components.vpd_air_auto.const import (
    SENSOR_KIND_ABSOLUTE_HUMIDITY,
    SENSOR_KIND_AIR,
    SENSOR_KIND_DEW_POINT,
    SENSOR_KIND_LEAF,
    IntegrationOptions,
)
from custom_components.vpd_air_auto.discovery.duplicates import (
    DuplicateDetectionService,
)

from .test_coordinator import _entry


def test_detect_existing_derived_sensor_kinds(hass):
    """Foreign sensors matching aliases are blocked as derived kinds."""
    options = IntegrationOptions()
    service = DuplicateDetectionService(hass, options)

    entries = [
        _entry("sensor.grow_tent_vpdair_foreign", original_name="VPDair"),
        _entry("sensor.grow_tent_leaf_vpd_foreign", original_name="Leaf VPD"),
        _entry(
            "sensor.grow_tent_absolute_humidity_foreign",
            original_name="Absolute Humidity",
            original_device_class="absolute_humidity",
        ),
        _entry("sensor.grow_tent_dew_point_foreign", original_name="Dew Point"),
    ]

    hass.states.async_set(
        "sensor.grow_tent_vpdair_foreign", "1.25", {"friendly_name": "VPDair"}
    )
    hass.states.async_set(
        "sensor.grow_tent_leaf_vpd_foreign",
        "1.50",
        {"friendly_name": "Leaf VPD"},
    )
    hass.states.async_set(
        "sensor.grow_tent_absolute_humidity_foreign",
        "13.8",
        {"device_class": "absolute_humidity", "friendly_name": "Absolute Humidity"},
    )
    hass.states.async_set(
        "sensor.grow_tent_dew_point_foreign",
        "16.6",
        {
            "friendly_name": "Dew Point",
            "unit_of_measurement": "°C",
            "device_class": "temperature",
        },
    )

    assert service.detect_existing_derived_sensor_kinds(entries) == frozenset(
        {
            SENSOR_KIND_AIR,
            SENSOR_KIND_LEAF,
            SENSOR_KIND_ABSOLUTE_HUMIDITY,
            SENSOR_KIND_DEW_POINT,
        }
    )
