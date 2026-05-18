"""Tests for duplicate detection service."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.vpd_air_auto.const import (
    SENSOR_KIND_ABSOLUTE_HUMIDITY,
    SENSOR_KIND_AIR,
    SENSOR_KIND_DEW_POINT,
    SENSOR_KIND_LEAF,
)
from custom_components.vpd_air_auto.discovery.duplicates import (
    DuplicateDetectionService,
)

from .test_coordinator import _entry, _options


def test_detect_existing_derived_sensor_kinds(hass: HomeAssistant) -> None:
    """Detect all duplicate kinds from foreign entities."""
    service = DuplicateDetectionService(_options())

    entries = [
        _entry(
            "sensor.foreign_vpdair",
            original_name="VPDair",
            original_device_class=None,
        ),
        _entry(
            "sensor.foreign_leaf_vpd",
            original_name="Leaf VPD",
            original_device_class=None,
        ),
        _entry(
            "sensor.foreign_abs_humidity",
            original_name="Absolute Humidity",
            original_device_class="absolute_humidity",
        ),
        _entry(
            "sensor.foreign_dew_point",
            original_name="Dew Point",
            original_device_class=None,
        ),
        _entry("sensor.own_helper", platform="vpd_air_auto", original_name="VPDair"),
    ]

    hass.states.async_set("sensor.foreign_vpdair", "1.2", {"friendly_name": "VPDair"})
    hass.states.async_set(
        "sensor.foreign_leaf_vpd", "1.3", {"friendly_name": "Leaf VPD"}
    )
    hass.states.async_set(
        "sensor.foreign_abs_humidity",
        "13",
        {"friendly_name": "Absolute Humidity", "device_class": "absolute_humidity"},
    )
    hass.states.async_set(
        "sensor.foreign_dew_point", "14", {"friendly_name": "Dew Point"}
    )

    blocked = service.detect_existing_derived_sensor_kinds(
        entries,
        lambda entity_id: hass.states.get(entity_id).attributes.get("friendly_name"),
        lambda entry: getattr(entry, "original_device_class", None),
    )

    assert blocked == frozenset(
        {
            SENSOR_KIND_AIR,
            SENSOR_KIND_LEAF,
            SENSOR_KIND_ABSOLUTE_HUMIDITY,
            SENSOR_KIND_DEW_POINT,
        }
    )
