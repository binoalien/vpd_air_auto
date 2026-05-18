"""Tests for duplicate detection service."""

from __future__ import annotations

from types import SimpleNamespace

from homeassistant.core import HomeAssistant

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


def _build_options(
    *,
    display_name: str = "VPDair",
    leaf_display_name: str = "VPDleaf",
    absolute_humidity_display_name: str = "Absolute Humidity",
    dew_point_display_name: str = "Dew Point",
) -> IntegrationOptions:
    return IntegrationOptions(
        scan_interval_seconds=300,
        enable_air=True,
        enable_leaf=True,
        enable_absolute_humidity=True,
        enable_dew_point=True,
        icon="mdi:water-opacity",
        display_name=display_name,
        leaf_icon="mdi:leaf",
        leaf_display_name=leaf_display_name,
        leaf_offset_c=-2.0,
        absolute_humidity_icon="mdi:water",
        absolute_humidity_display_name=absolute_humidity_display_name,
        dew_point_icon="mdi:thermometer-water",
        dew_point_display_name=dew_point_display_name,
    )


def _entry(  # pylint: disable=too-many-arguments
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
    """Detect all supported duplicate kinds from aliases and device class."""
    service = DuplicateDetectionService(hass, _build_options())

    entries = [
        _entry("sensor.foreign_vpd_air", original_name="VPDair"),
        _entry("sensor.foreign_vpd_leaf", name="Leaf VPD"),
        _entry(
            "sensor.foreign_abs_humidity", original_device_class="absolute_humidity"
        ),
        _entry("sensor.foreign_dew_point", original_name="Dew Point"),
        _entry("sensor.own_helper", platform="vpd_air_auto", original_name="VPDair"),
        _entry(
            "binary_sensor.should_skip", domain="binary_sensor", original_name="VPDair"
        ),
    ]

    hass.states.async_set("sensor.foreign_vpd_air", "1.2", {"friendly_name": "VPDair"})
    hass.states.async_set(
        "sensor.foreign_vpd_leaf", "1.4", {"friendly_name": "Leaf VPD"}
    )
    hass.states.async_set(
        "sensor.foreign_abs_humidity",
        "13.0",
        {"friendly_name": "Absolute Humidity", "device_class": "absolute_humidity"},
    )
    hass.states.async_set(
        "sensor.foreign_dew_point", "15.8", {"friendly_name": "Dew Point"}
    )

    blocked = service.detect_existing_derived_sensor_kinds(entries)

    assert blocked == frozenset(
        {
            SENSOR_KIND_AIR,
            SENSOR_KIND_LEAF,
            SENSOR_KIND_ABSOLUTE_HUMIDITY,
            SENSOR_KIND_DEW_POINT,
        }
    )


def test_detect_existing_derived_sensor_kinds_uses_custom_display_names(
    hass: HomeAssistant,
) -> None:
    """Detect duplicates by user-defined display names."""
    service = DuplicateDetectionService(
        hass,
        _build_options(
            display_name="Grow Air",
            leaf_display_name="Grow Leaf",
            absolute_humidity_display_name="Grow Absolute",
            dew_point_display_name="Grow Dew",
        ),
    )

    entries = [
        _entry("sensor.custom_air", original_name="Grow Air"),
        _entry("sensor.custom_leaf", original_name="Grow Leaf"),
        _entry("sensor.custom_abs", original_name="Grow Absolute"),
        _entry("sensor.custom_dew", original_name="Grow Dew"),
    ]

    blocked = service.detect_existing_derived_sensor_kinds(entries)

    assert blocked == frozenset(
        {
            SENSOR_KIND_AIR,
            SENSOR_KIND_LEAF,
            SENSOR_KIND_ABSOLUTE_HUMIDITY,
            SENSOR_KIND_DEW_POINT,
        }
    )
