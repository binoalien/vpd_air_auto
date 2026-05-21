"""Tests for topology discovery service."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from homeassistant.core import HomeAssistant

from custom_components.vpd_air_auto.discovery.topology import TopologyDiscoveryService


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


def test_discover_applies_valid_manual_source_overrides(
    hass: HomeAssistant,
) -> None:
    """Manual source overrides replace auto-selected entities when valid."""
    duplicate_detection = _DuplicateDetectionStub()
    service = TopologyDiscoveryService(hass, duplicate_detection)

    auto_temp = _entry("sensor.auto_temp", original_device_class="temperature")
    manual_temp = _entry("sensor.manual_temp", original_device_class="temperature")
    auto_humidity = _entry("sensor.auto_humidity", original_device_class="humidity")

    hass.states.async_set("sensor.auto_temp", "24", {"device_class": "temperature"})
    hass.states.async_set("sensor.manual_temp", "25", {"device_class": "temperature"})
    hass.states.async_set("sensor.auto_humidity", "62", {"device_class": "humidity"})

    area_registry = SimpleNamespace(async_get_area=lambda _area_id: None)
    device_registry = SimpleNamespace(devices={"dev1": _device("dev1")})
    entity_registry = SimpleNamespace()

    with (
        patch("custom_components.vpd_air_auto.discovery.topology.dr.async_get", return_value=device_registry),
        patch("custom_components.vpd_air_auto.discovery.topology.ar.async_get", return_value=area_registry),
        patch("custom_components.vpd_air_auto.discovery.topology.er.async_get", return_value=entity_registry),
        patch("custom_components.vpd_air_auto.discovery.topology.er.async_entries_for_device", return_value=[auto_temp, manual_temp, auto_humidity]),
    ):
        topology = service.discover(
            {
                "dev1": SimpleNamespace(
                    temperature_entity_id="sensor.manual_temp",
                    humidity_entity_id=None,
                )
            }
        )

    assert topology["dev1"].temperature_entity_id == "sensor.manual_temp"
    assert topology["dev1"].humidity_entity_id == "sensor.auto_humidity"


def test_discover_ignores_invalid_manual_source_overrides(
    hass: HomeAssistant,
) -> None:
    """Invalid manual source overrides fall back to auto-selection heuristics."""
    duplicate_detection = _DuplicateDetectionStub()
    service = TopologyDiscoveryService(hass, duplicate_detection)

    auto_temp = _entry("sensor.auto_temp", original_device_class="temperature")
    auto_humidity = _entry("sensor.auto_humidity", original_device_class="humidity")
    wrong_class = _entry("sensor.bad_humidity", original_device_class="temperature")

    hass.states.async_set("sensor.auto_temp", "24", {"device_class": "temperature"})
    hass.states.async_set("sensor.auto_humidity", "62", {"device_class": "humidity"})
    hass.states.async_set("sensor.bad_humidity", "62", {"device_class": "temperature"})

    area_registry = SimpleNamespace(async_get_area=lambda _area_id: None)
    device_registry = SimpleNamespace(devices={"dev1": _device("dev1")})
    entity_registry = SimpleNamespace()

    with (
        patch("custom_components.vpd_air_auto.discovery.topology.dr.async_get", return_value=device_registry),
        patch("custom_components.vpd_air_auto.discovery.topology.ar.async_get", return_value=area_registry),
        patch("custom_components.vpd_air_auto.discovery.topology.er.async_get", return_value=entity_registry),
        patch("custom_components.vpd_air_auto.discovery.topology.er.async_entries_for_device", return_value=[auto_temp, auto_humidity, wrong_class]),
    ):
        topology = service.discover(
            {
                "dev1": SimpleNamespace(
                    temperature_entity_id="sensor.missing",
                    humidity_entity_id="sensor.bad_humidity",
                )
            }
        )

    assert topology["dev1"].temperature_entity_id == "sensor.auto_temp"
    assert topology["dev1"].humidity_entity_id == "sensor.auto_humidity"
