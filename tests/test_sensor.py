"""Tests for VPD Air Auto sensor entities."""

# pylint: disable=protected-access

from __future__ import annotations

from collections.abc import Iterable
from unittest.mock import Mock

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import Entity, MockConfigEntry

from custom_components.vpd_air_auto.const import (
    DOMAIN,
    SENSOR_KIND_ABSOLUTE_HUMIDITY,
    SENSOR_KIND_AIR,
    SENSOR_KIND_DEW_POINT,
    SENSOR_KIND_LEAF,
    UNIT_C,
    UNIT_GM3,
    UNIT_KPA,
    IntegrationOptions,
    make_absolute_humidity_unique_id,
    make_dew_point_unique_id,
    make_vpdair_unique_id,
    make_vpdleaf_unique_id,
)
from custom_components.vpd_air_auto.coordinator import VpdAirCoordinator
from custom_components.vpd_air_auto.models import DeviceSnapshot, DeviceTopology
from custom_components.vpd_air_auto.sensor import (
    PARALLEL_UPDATES,
    DerivedValueSensor,
    _registry_entry_kind,
    async_setup_entry,
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


def _snapshot(device_id: str) -> DeviceSnapshot:
    return DeviceSnapshot(
        device_id=device_id,
        device_name="Grow Tent",
        temperature_entity_id="sensor.grow_tent_temperature",
        humidity_entity_id="sensor.grow_tent_humidity",
        temperature_c=25.0,
        humidity_pct=60.0,
        leaf_offset_c=-2.0,
        leaf_temperature_c=23.0,
        dew_point_c=16.68,
        vpd_air_kpa=1.27,
        vpd_leaf_kpa=1.58,
        absolute_humidity_gm3=13.8,
    )


def _build_sensor(hass: HomeAssistant, kind: str) -> DerivedValueSensor:
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    coordinator = VpdAirCoordinator(hass, entry, _options())
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("test", "grow-tent")},
        name="Grow Tent",
    )
    coordinator._topology = {
        device.id: DeviceTopology(
            device_id=device.id,
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
            blocked_sensor_kinds=frozenset(),
        )
    }
    coordinator.data = {device.id: _snapshot(device.id)}
    return DerivedValueSensor(hass, coordinator, device.id, kind)


def test_air_sensor_properties(hass: HomeAssistant) -> None:
    """Test air sensor properties."""
    sensor = _build_sensor(hass, SENSOR_KIND_AIR)

    assert sensor.name == "VPDair"
    assert sensor.icon == "mdi:water-opacity"
    assert sensor.native_unit_of_measurement == UNIT_KPA
    assert sensor.device_class is None
    assert sensor.available is True
    assert sensor.native_value == 1.27
    assert sensor.state_class == "measurement"
    assert sensor.suggested_display_precision == 2
    assert sensor.extra_state_attributes == {
        "temperature_entity_id": "sensor.grow_tent_temperature",
        "humidity_entity_id": "sensor.grow_tent_humidity",
    }


def test_leaf_sensor_properties(hass: HomeAssistant) -> None:
    """Test leaf sensor properties."""
    sensor = _build_sensor(hass, SENSOR_KIND_LEAF)

    assert sensor.name == "VPDleaf"
    assert sensor.icon == "mdi:leaf"
    assert sensor.native_unit_of_measurement == UNIT_KPA
    assert sensor.device_class is None
    assert sensor.available is True
    assert sensor.native_value == 1.58
    assert sensor.extra_state_attributes == {
        "temperature_entity_id": "sensor.grow_tent_temperature",
        "humidity_entity_id": "sensor.grow_tent_humidity",
        "leaf_temperature_offset_c": -2.0,
    }


def test_dew_point_sensor_properties(hass: HomeAssistant) -> None:
    """Test dew point sensor properties."""
    sensor = _build_sensor(hass, SENSOR_KIND_DEW_POINT)

    assert sensor.name == "Dew Point"
    assert sensor.icon == "mdi:thermometer-water"
    assert sensor.native_unit_of_measurement == UNIT_C
    assert sensor.device_class == "temperature"
    assert sensor.available is True
    assert sensor.native_value == 16.68
    assert sensor.extra_state_attributes == {
        "temperature_entity_id": "sensor.grow_tent_temperature",
        "humidity_entity_id": "sensor.grow_tent_humidity",
    }


def test_absolute_humidity_sensor_properties(hass: HomeAssistant) -> None:
    """Test absolute humidity sensor properties."""
    sensor = _build_sensor(hass, SENSOR_KIND_ABSOLUTE_HUMIDITY)

    assert sensor.name == "Absolute Humidity"
    assert sensor.icon == "mdi:water"
    assert sensor.native_unit_of_measurement == UNIT_GM3
    assert sensor.device_class == "absolute_humidity"
    assert sensor.available is True
    assert sensor.native_value == 13.8
    assert sensor.extra_state_attributes == {
        "temperature_entity_id": "sensor.grow_tent_temperature",
        "humidity_entity_id": "sensor.grow_tent_humidity",
    }


def test_sensor_unavailable_without_snapshot(hass: HomeAssistant) -> None:
    """Test sensor unavailable without snapshot."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    coordinator = VpdAirCoordinator(hass, entry, _options())
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("test", "no-snapshot")},
        name="No Snapshot Device",
    )

    sensor = DerivedValueSensor(hass, coordinator, device.id, SENSOR_KIND_AIR)

    assert sensor.available is False
    assert sensor.native_value is None
    assert not sensor.extra_state_attributes


def test_registry_entry_kind_and_parallel_updates() -> None:
    """Test registry entry kind and parallel updates."""
    assert PARALLEL_UPDATES == 0
    assert _registry_entry_kind("prefix_vpdair") == SENSOR_KIND_AIR
    assert _registry_entry_kind("prefix_vpdleaf") == SENSOR_KIND_LEAF
    assert (
        _registry_entry_kind("prefix_absolute_humidity")
        == SENSOR_KIND_ABSOLUTE_HUMIDITY
    )
    assert _registry_entry_kind("prefix_dew_point") == SENSOR_KIND_DEW_POINT
    assert _registry_entry_kind("prefix_unknown") is None


def test_unique_id_building_matches_public_helpers(hass: HomeAssistant) -> None:
    """Test unique id building matches public helpers."""
    sensor_air = _build_sensor(hass, SENSOR_KIND_AIR)
    sensor_leaf = _build_sensor(hass, SENSOR_KIND_LEAF)
    sensor_abs = _build_sensor(hass, SENSOR_KIND_ABSOLUTE_HUMIDITY)
    sensor_dew = _build_sensor(hass, SENSOR_KIND_DEW_POINT)

    assert sensor_air.unique_id == make_vpdair_unique_id(sensor_air._device_id)
    assert sensor_leaf.unique_id == make_vpdleaf_unique_id(
        sensor_leaf._device_id)
    assert sensor_abs.unique_id == make_absolute_humidity_unique_id(
        sensor_abs._device_id
    )
    assert sensor_dew.unique_id == make_dew_point_unique_id(
        sensor_dew._device_id)


async def test_sensor_added_and_removed_notifies_context_tracking(
    hass: HomeAssistant,
) -> None:
    """Test sensor added and removed notifies context tracking."""
    sensor = _build_sensor(hass, SENSOR_KIND_AIR)
    sensor.coordinator.async_note_context_change = Mock()

    await sensor.async_added_to_hass()
    await sensor.async_will_remove_from_hass()

    assert sensor.coordinator.async_note_context_change.call_count == 2


def test_handle_coordinator_update_writes_state(hass: HomeAssistant) -> None:
    """Test handle coordinator update writes state."""
    sensor = _build_sensor(hass, SENSOR_KIND_AIR)
    sensor.async_write_ha_state = Mock()

    sensor._handle_coordinator_update()

    sensor.async_write_ha_state.assert_called_once()


async def test_async_setup_entry_adds_and_removes_expected_entities(
    hass: HomeAssistant,
) -> None:
    """Test async setup entry adds and removes expected entities."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    coordinator = VpdAirCoordinator(hass, entry, _options())
    entry.runtime_data = coordinator
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("test", "setup-entry")},
        name="Setup Entry Device",
    )
    coordinator.data = {device.id: _snapshot(device.id)}
    coordinator.creatable_kinds_for_device = Mock(
        return_value=[SENSOR_KIND_AIR, SENSOR_KIND_LEAF]
    )

    remove_callback = Mock()
    coordinator.async_add_listener = Mock(return_value=remove_callback)
    added_entities = []

    def _capture_add_entities(
        new_entities: Iterable[Entity],
        update_before_add: bool = False,
        *,
        config_subentry_id: str | None = None,
    ) -> None:  # pylint: disable=unused-argument
        added_entities.extend(new_entities)

    await async_setup_entry(hass, entry, _capture_add_entities)

    assert {(entity._device_id, entity._kind) for entity in added_entities} == {
        (device.id, SENSOR_KIND_AIR),
        (device.id, SENSOR_KIND_LEAF),
    }
    coordinator.async_add_listener.assert_called_once()

    entity_registry = er.async_get(hass)
    stale = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        make_absolute_humidity_unique_id(device.id),
        config_entry=entry,
        device_id=device.id,
        original_name="Absolute Humidity",
    )
    entity_registry.async_remove = Mock(wraps=entity_registry.async_remove)

    sync_callback = coordinator.async_add_listener.call_args.args[0]
    sync_callback()

    entity_registry.async_remove.assert_called_once_with(stale.entity_id)
    if entry._on_unload is not None:
        unload_callback = entry._on_unload[-1]
        maybe_result = unload_callback()
        if maybe_result is not None and hasattr(maybe_result, "__await__"):
            await maybe_result
        remove_callback.assert_called_once()
    else:
        remove_callback.assert_not_called()
