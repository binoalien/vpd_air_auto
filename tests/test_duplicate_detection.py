"""Tests for duplicate detection service."""

from __future__ import annotations

from types import SimpleNamespace

from homeassistant.core import HomeAssistant

from custom_components.vpd_air_auto.const import (
    DOMAIN,
    SENSOR_KIND_ABSOLUTE_HUMIDITY,
    SENSOR_KIND_AIR,
    SENSOR_KIND_DEW_POINT,
    SENSOR_KIND_LEAF,
)
from custom_components.vpd_air_auto.discovery.duplicates import (
    DuplicateDetectionService,
)

from .test_coordinator import _build_options


def _entry(
    entity_id: str,
    *,
    domain: str = "sensor",
    platform: str = "mqtt",
    name: str | None = None,
    original_name: str | None = None,
    original_device_class: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        entity_id=entity_id,
        domain=domain,
        platform=platform,
        name=name,
        original_name=original_name,
        original_device_class=original_device_class,
    )


def test_detect_existing_derived_sensor_kinds(hass: HomeAssistant) -> None:
    """Detect all blocked kinds from alias and device-class matching."""
    service = DuplicateDetectionService(hass, _build_options())

    hass.states.async_set(
        "sensor.grow_tent_vpdair_foreign",
        "1.25",
        {"friendly_name": "VPDair"},
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
        {"friendly_name": "Dew Point"},
    )

    blocked = service.detect_existing_derived_sensor_kinds(
        [
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
    )

    assert blocked == frozenset(
        {
            SENSOR_KIND_AIR,
            SENSOR_KIND_LEAF,
            SENSOR_KIND_ABSOLUTE_HUMIDITY,
            SENSOR_KIND_DEW_POINT,
        }
    )
