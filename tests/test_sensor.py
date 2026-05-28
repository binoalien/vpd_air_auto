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


def test_parallel_updates() -> None:
    """Test platform update parallelism setting."""
    assert PARALLEL_UPDATES == 0



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


async def test_async_setup_entry_syncs_without_duplicate_adds_and_preserves_registry(
    hass: HomeAssistant,
) -> None:
    """Test setup/sync add behavior and no stale registry deletion."""
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
    creatable = [SENSOR_KIND_AIR, SENSOR_KIND_LEAF]
    coordinator.creatable_kinds_for_device = Mock(side_effect=lambda _id: list(creatable))

    remove_callback = Mock()
    coordinator.async_add_listener = Mock(return_value=remove_callback)
    added_entities = []

    def _capture_add_entities(
        new_entities: Iterable[Entity],
        update_before_add: bool = False,
        *,
        config_subentry_id: str | None = None,
    ) -> None:
        _ = (update_before_add, config_subentry_id)
        added_entities.extend(new_entities)

    await async_setup_entry(hass, entry, _capture_add_entities)
    assert {(entity._device_id, entity._kind) for entity in added_entities} == {
        (device.id, SENSOR_KIND_AIR),
        (device.id, SENSOR_KIND_LEAF),
    }

    sync_callback = coordinator.async_add_listener.call_args.args[0]
    sync_callback()
    assert len(added_entities) == 2

    creatable.append(SENSOR_KIND_DEW_POINT)
    sync_callback()
    assert {(entity._device_id, entity._kind) for entity in added_entities} == {
        (device.id, SENSOR_KIND_AIR),
        (device.id, SENSOR_KIND_LEAF),
        (device.id, SENSOR_KIND_DEW_POINT),
    }

    entity_registry = er.async_get(hass)
    stale = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        make_absolute_humidity_unique_id(device.id),
        config_entry=entry,
        device_id=device.id,
        original_name="Absolute Humidity",
    )

    creatable.remove(SENSOR_KIND_LEAF)
    sync_callback()
    assert entity_registry.async_get(stale.entity_id) is stale


async def test_device_registry_attachment_and_entity_registry_device_id(
    hass: HomeAssistant,
) -> None:
    """Test generated sensor binds to the existing device registry device."""
    sensor = _build_sensor(hass, SENSOR_KIND_AIR)
    assert sensor.device_entry is not None
    source_device_id = sensor._device_id
    assert sensor.device_entry.id == source_device_id

    entity_registry = er.async_get(hass)
    entry = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        sensor.unique_id,
        device_id=source_device_id,
        original_name=sensor.name,
    )
    assert entry.device_id == source_device_id
    assert dr.async_get(hass).async_get(source_device_id) is sensor.device_entry


async def test_duplicate_detection_blocking_keeps_existing_registry_entry(
    hass: HomeAssistant,
) -> None:
    """Test blocked kinds do not remove existing generated registry entities."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    coordinator = VpdAirCoordinator(hass, entry, _options())
    entry.runtime_data = coordinator
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("test", "dup")}, name="Dup Device"
    )
    coordinator.data = {device.id: _snapshot(device.id)}
    coordinator.creatable_kinds_for_device = Mock(return_value=[SENSOR_KIND_AIR])
    coordinator.async_add_listener = Mock(return_value=Mock())
    added_entities = []

    await async_setup_entry(hass, entry, lambda ents, **_: added_entities.extend(ents))
    entity_registry = er.async_get(hass)
    blocked = entity_registry.async_get_or_create(
        "sensor", DOMAIN, make_vpdleaf_unique_id(device.id), config_entry=entry, device_id=device.id, original_name="VPDleaf"
    )

    sync_callback = coordinator.async_add_listener.call_args.args[0]
    sync_callback()

    assert entity_registry.async_get(blocked.entity_id) is blocked
    assert {(e._device_id, e._kind) for e in added_entities} == {(device.id, SENSOR_KIND_AIR)}


async def test_missing_coordinator_data_keeps_registry_entries(
    hass: HomeAssistant,
) -> None:
    """Test missing coordinator data does not remove existing registry entities."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    coordinator = VpdAirCoordinator(hass, entry, _options())
    entry.runtime_data = coordinator
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("test", "missing")}, name="Missing Device"
    )
    coordinator.data = {device.id: _snapshot(device.id)}
    coordinator.creatable_kinds_for_device = Mock(return_value=[SENSOR_KIND_AIR])
    coordinator.async_add_listener = Mock(return_value=Mock())

    await async_setup_entry(hass, entry, lambda _ents, **_: None)
    entity_registry = er.async_get(hass)
    existing = entity_registry.async_get_or_create(
        "sensor", DOMAIN, make_vpdair_unique_id(device.id), config_entry=entry, device_id=device.id, original_name="VPDair"
    )

    coordinator.data = {}
    sync_callback = coordinator.async_add_listener.call_args.args[0]
    sync_callback()

    assert entity_registry.async_get(existing.entity_id) is existing


