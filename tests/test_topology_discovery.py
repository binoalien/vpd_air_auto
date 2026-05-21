"""Tests for topology discovery service."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from homeassistant.core import HomeAssistant

from custom_components.vpd_air_auto.discovery.topology import TopologyDiscoveryService
from custom_components.vpd_air_auto.policy.models import SourceOverride


def _device(
    device_id: str,
    name: str = "Grow Tent",
    *,
    area_id: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(id=device_id, name=name, name_by_user=None, area_id=area_id)


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

    area_registry = SimpleNamespace(async_get_area=lambda _area_id: None)
    device_registry = SimpleNamespace(devices={"dev1": _device("dev1", "Tent")})
    entity_registry = SimpleNamespace()

    with (
        patch(
            "custom_components.vpd_air_auto.discovery.topology.dr.async_get",
            return_value=device_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.discovery.topology.ar.async_get",
            return_value=area_registry,
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
    assert topology["dev1"].area_id is None
    assert topology["dev1"].area_name is None
    assert duplicate_detection.calls == [
        [
            "sensor.grow_tent_temperature_diag",
            "sensor.grow_tent_temperature",
            "sensor.grow_tent_relative",
            "sensor.grow_tent_humidity",
        ]
    ]


def test_discover_sets_area_id_and_area_name_when_device_has_area(
    hass: HomeAssistant,
) -> None:
    """Topology includes area metadata when area assignment exists."""
    duplicate_detection = _DuplicateDetectionStub()
    service = TopologyDiscoveryService(hass, duplicate_detection)

    temp_entry = _entry(
        "sensor.grow_tent_temperature",
        original_device_class="temperature",
        original_unit_of_measurement="°C",
    )
    humidity_entry = _entry(
        "sensor.grow_tent_humidity",
        original_device_class="humidity",
        original_unit_of_measurement="%",
    )
    hass.states.async_set(
        "sensor.grow_tent_temperature",
        "24.5",
        {"device_class": "temperature", "unit_of_measurement": "°C"},
    )
    hass.states.async_set(
        "sensor.grow_tent_humidity",
        "61",
        {"device_class": "humidity", "unit_of_measurement": "%"},
    )

    area_registry = SimpleNamespace(
        async_get_area=lambda area_id: SimpleNamespace(name="Flower Room")
        if area_id == "area-1"
        else None
    )
    device_registry = SimpleNamespace(
        devices={"dev1": _device("dev1", "Tent", area_id="area-1")}
    )
    entity_registry = SimpleNamespace()

    with (
        patch(
            "custom_components.vpd_air_auto.discovery.topology.dr.async_get",
            return_value=device_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.discovery.topology.ar.async_get",
            return_value=area_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.discovery.topology.er.async_get",
            return_value=entity_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.discovery.topology.er.async_entries_for_device",
            return_value=[temp_entry, humidity_entry],
        ),
    ):
        topology = service.discover()

    assert topology["dev1"].area_id == "area-1"
    assert topology["dev1"].area_name == "Flower Room"


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

    area_registry = SimpleNamespace(async_get_area=lambda _area_id: None)
    device_registry = SimpleNamespace(devices={"dev1": _device("dev1")})
    entity_registry = SimpleNamespace()

    with (
        patch(
            "custom_components.vpd_air_auto.discovery.topology.dr.async_get",
            return_value=device_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.discovery.topology.ar.async_get",
            return_value=area_registry,
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


def test_discover_respects_valid_manual_source_overrides(
    hass: HomeAssistant,
) -> None:
    """Manual source overrides replace automatically selected sources when valid."""
    duplicate_detection = _DuplicateDetectionStub()
    service = TopologyDiscoveryService(hass, duplicate_detection)

    temp_auto = _entry("sensor.temp_auto", original_device_class="temperature")
    temp_manual = _entry("sensor.temp_manual", original_device_class="temperature")
    humidity_auto = _entry("sensor.humidity_auto", original_device_class="humidity")
    humidity_manual = _entry(
        "sensor.humidity_manual", original_device_class="humidity"
    )
    for entity_id, state, device_class, unit in (
        ("sensor.temp_auto", "24", "temperature", "°C"),
        ("sensor.temp_manual", "26", "temperature", "°C"),
        ("sensor.humidity_auto", "52", "humidity", "%"),
        ("sensor.humidity_manual", "64", "humidity", "%"),
    ):
        hass.states.async_set(
            entity_id,
            state,
            {"device_class": device_class, "unit_of_measurement": unit},
        )

    area_registry = SimpleNamespace(async_get_area=lambda _area_id: None)
    device_registry = SimpleNamespace(devices={"dev1": _device("dev1")})
    entity_registry = SimpleNamespace()

    with (
        patch(
            "custom_components.vpd_air_auto.discovery.topology.dr.async_get",
            return_value=device_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.discovery.topology.ar.async_get",
            return_value=area_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.discovery.topology.er.async_get",
            return_value=entity_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.discovery.topology.er.async_entries_for_device",
            return_value=[temp_auto, temp_manual, humidity_auto, humidity_manual],
        ),
    ):
        topology = service.discover(
            {
                "dev1": SourceOverride(
                    temperature_entity_id="sensor.temp_manual",
                    humidity_entity_id="sensor.humidity_manual",
                )
            }
        )

    assert topology["dev1"].temperature_entity_id == "sensor.temp_manual"
    assert topology["dev1"].humidity_entity_id == "sensor.humidity_manual"


def test_discover_ignores_invalid_manual_source_overrides(
    hass: HomeAssistant,
) -> None:
    """Invalid manual sources do not break fallback automatic source selection."""
    duplicate_detection = _DuplicateDetectionStub()
    service = TopologyDiscoveryService(hass, duplicate_detection)

    temp_auto = _entry("sensor.temp_auto", original_device_class="temperature")
    humidity_auto = _entry("sensor.humidity_auto", original_device_class="humidity")
    temp_wrong_class = _entry(
        "sensor.temp_wrong_class", original_device_class="humidity"
    )
    hass.states.async_set(
        "sensor.temp_auto", "24", {"device_class": "temperature", "unit_of_measurement": "°C"}
    )
    hass.states.async_set(
        "sensor.humidity_auto", "53", {"device_class": "humidity", "unit_of_measurement": "%"}
    )
    hass.states.async_set(
        "sensor.temp_wrong_class", "61", {"device_class": "humidity", "unit_of_measurement": "%"}
    )

    area_registry = SimpleNamespace(async_get_area=lambda _area_id: None)
    device_registry = SimpleNamespace(devices={"dev1": _device("dev1")})
    entity_registry = SimpleNamespace()

    with (
        patch("custom_components.vpd_air_auto.discovery.topology.dr.async_get", return_value=device_registry),
        patch("custom_components.vpd_air_auto.discovery.topology.ar.async_get", return_value=area_registry),
        patch("custom_components.vpd_air_auto.discovery.topology.er.async_get", return_value=entity_registry),
        patch(
            "custom_components.vpd_air_auto.discovery.topology.er.async_entries_for_device",
            return_value=[temp_auto, humidity_auto, temp_wrong_class],
        ),
    ):
        topology = service.discover(
            {
                "dev1": SourceOverride(
                    temperature_entity_id="sensor.temp_wrong_class",
                    humidity_entity_id="sensor.missing",
                )
            }
        )

    assert topology["dev1"].temperature_entity_id == "sensor.temp_auto"
    assert topology["dev1"].humidity_entity_id == "sensor.humidity_auto"
