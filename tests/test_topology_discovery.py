"""Tests for topology discovery service."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from homeassistant.core import HomeAssistant

from custom_components.vpd_air_auto.discovery.topology import TopologyDiscoveryService


def _device(device_id: str, name: str = "Grow Tent") -> SimpleNamespace:
    return SimpleNamespace(id=device_id, name=name, name_by_user=None)


def _entry(  # pylint: disable=too-many-arguments
    entity_id: str,
    *,
    domain: str = "sensor",
    platform: str = "mqtt",
    original_device_class: str | None = None,
    original_unit_of_measurement: str | None = None,
    name: str | None = None,
    original_name: str | None = None,
    entity_category: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        entity_id=entity_id,
        domain=domain,
        platform=platform,
        original_device_class=original_device_class,
        original_unit_of_measurement=original_unit_of_measurement,
        entity_category=entity_category,
        name=name,
        original_name=original_name,
    )


class _DuplicateDetectionStub:  # pylint: disable=too-few-public-methods
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def detect_existing_derived_sensor_kinds(self, candidates):
        """Return fixed blocked kinds and record passed candidates."""
        self.calls.append([entry.entity_id for entry in candidates])
        return frozenset({"air"})


def test_discover_returns_topology_with_best_sources_and_blocked_kinds(
    hass: HomeAssistant,
) -> None:
    """Discover topology and prefer best candidates over lower-priority ones."""
    duplicate_detection = _DuplicateDetectionStub()
    service = TopologyDiscoveryService(hass, duplicate_detection)

    best_temp_entry = _entry(
        "sensor.grow_tent_temperature",
        original_device_class="temperature",
        original_unit_of_measurement="°C",
    )
    lower_priority_temp_entry = _entry(
        "sensor.grow_tent_temperature_diag",
        original_device_class="temperature",
        original_unit_of_measurement="°C",
        entity_category="diagnostic",
    )
    best_humidity_entry = _entry(
        "sensor.grow_tent_humidity",
        original_device_class="humidity",
        original_unit_of_measurement="%",
    )
    lower_priority_humidity_entry = _entry(
        "sensor.grow_tent_relative",
        original_device_class="humidity",
        original_unit_of_measurement="g/m3",
    )

    hass.states.async_set(
        "sensor.grow_tent_temperature",
        "24.5",
        {"device_class": "temperature", "unit_of_measurement": "°C"},
    )
    hass.states.async_set(
        "sensor.grow_tent_temperature_diag",
        "24.5",
        {"device_class": "temperature", "unit_of_measurement": "°C"},
    )
    hass.states.async_set(
        "sensor.grow_tent_humidity",
        "61",
        {"device_class": "humidity", "unit_of_measurement": "%"},
    )
    hass.states.async_set(
        "sensor.grow_tent_relative",
        "11.2",
        {"device_class": "humidity", "unit_of_measurement": "g/m3"},
    )

    device_registry = SimpleNamespace(devices={"dev1": _device("dev1", "Tent")})
    entity_registry = SimpleNamespace()

    with (
        patch(
            "custom_components.vpd_air_auto.discovery.topology.dr.async_get",
            return_value=device_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.discovery.topology.er.async_get",
            return_value=entity_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.discovery.topology.er.async_entries_for_device",
            return_value=[
                lower_priority_temp_entry,
                best_temp_entry,
                lower_priority_humidity_entry,
                best_humidity_entry,
            ],
        ),
    ):
        topology = service.discover()

    assert list(topology) == ["dev1"]
    assert topology["dev1"].temperature_entity_id == "sensor.grow_tent_temperature"
    assert topology["dev1"].humidity_entity_id == "sensor.grow_tent_humidity"
    assert topology["dev1"].blocked_sensor_kinds == frozenset({"air"})
    assert duplicate_detection.calls == [
        [
            "sensor.grow_tent_temperature_diag",
            "sensor.grow_tent_temperature",
            "sensor.grow_tent_relative",
            "sensor.grow_tent_humidity",
        ]
    ]


def test_discover_skips_devices_without_complete_source_pair(
    hass: HomeAssistant,
) -> None:
    """Skip devices when either temperature or humidity source cannot be selected."""
    duplicate_detection = _DuplicateDetectionStub()
    service = TopologyDiscoveryService(hass, duplicate_detection)

    only_temp_entry = _entry(
        "sensor.only_temperature",
        original_device_class="temperature",
        original_unit_of_measurement="°C",
    )

    hass.states.async_set(
        "sensor.only_temperature",
        "23",
        {"device_class": "temperature", "unit_of_measurement": "°C"},
    )

    device_registry = SimpleNamespace(devices={"dev1": _device("dev1")})
    entity_registry = SimpleNamespace()

    with (
        patch(
            "custom_components.vpd_air_auto.discovery.topology.dr.async_get",
            return_value=device_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.discovery.topology.er.async_get",
            return_value=entity_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.discovery.topology.er.async_entries_for_device",
            return_value=[only_temp_entry],
        ),
    ):
        topology = service.discover()

    assert not topology
    assert not duplicate_detection.calls
