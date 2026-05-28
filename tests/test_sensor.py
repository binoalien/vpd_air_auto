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
    """Test parallel updates constant."""
    assert PARALLEL_UPDATES == 0


def test_unique_id_building_matches_public_helpers(hass: HomeAssistant) -> None:
    """Test unique id building matches public helpers."""
    sensor_air = _build_sensor(hass, SENSOR_KIND_AIR)
    sensor_leaf = _build_sensor(hass, SENSOR_KIND_LEAF)
    sensor_abs = _build_sensor(hass, SENSOR_KIND_ABSOLUTE_HUMIDITY)
    sensor_dew = _build_sensor(hass, SENSOR_KIND_DEW_POINT)

    assert sensor_air.unique_id == make_vpdair_unique_id(sensor_air._device_id)
    assert sensor_leaf.unique_id == make_vpdleaf_unique_id(
        sensor_leaf._device_id
    )
    assert sensor_abs.unique_id == make_absolute_humidity_unique_id(
        sensor_abs._device_id
    )
    assert sensor_dew.unique_id == make_dew_point_unique_id(
        sensor_dew._device_id
    )


def test_sensor_with_missing_device_entry_is_safe(hass: HomeAssistant) -> None:
    """Test sensor handles missing device registry entry safely."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    coordinator = VpdAirCoordinator(hass, entry, _options())
    unknown_device_id = "missing-device-id"
    sensor = DerivedValueSensor(
        hass, coordinator, unknown_device_id, SENSOR_KIND_AIR
    )

    assert sensor.device_entry is None
    assert sensor.available is False
    assert sensor.native_value is None
    assert not sensor.extra_state_attributes
    assert sensor.unique_id == make_vpdair_unique_id(unknown_device_id)


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


async def test_async_setup_entry_adds_expected_entities_and_no_duplicates(
    hass: HomeAssistant,
) -> None:
    """Test async setup entry adds expected entities and avoids duplicates."""
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
    ) -> None:
        _ = (update_before_add, config_subentry_id)
        added_entities.extend(new_entities)

    await async_setup_entry(hass, entry, _capture_add_entities)

    assert {(entity._device_id, entity._kind) for entity in added_entities} == {
        (device.id, SENSOR_KIND_AIR),
        (device.id, SENSOR_KIND_LEAF),
    }
    coordinator.async_add_listener.assert_called_once()

    sync_callback = coordinator.async_add_listener.call_args.args[0]
    sync_callback()
    assert len(added_entities) == 2

    coordinator.creatable_kinds_for_device = Mock(
        return_value=[SENSOR_KIND_AIR, SENSOR_KIND_LEAF, SENSOR_KIND_DEW_POINT]
    )
    sync_callback()
    assert {(entity._device_id, entity._kind) for entity in added_entities} == {
        (device.id, SENSOR_KIND_AIR),
        (device.id, SENSOR_KIND_LEAF),
        (device.id, SENSOR_KIND_DEW_POINT),
    }

    if entry._on_unload is not None:
        unload_callback = entry._on_unload[-1]
        maybe_result = unload_callback()
        if maybe_result is not None and hasattr(maybe_result, "__await__"):
            await maybe_result
        remove_callback.assert_called_once()
    else:
        remove_callback.assert_not_called()


async def test_setup_entry_entities_attach_to_existing_device_registry_device(
    hass: HomeAssistant,
) -> None:
    """Test generated sensors attach to the existing source device."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    coordinator = VpdAirCoordinator(hass, entry, _options())
    entry.runtime_data = coordinator
    device_registry = dr.async_get(hass)
    source_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("test", "registry-attach")},
        name="Registry Attach Device",
    )
    coordinator.data = {source_device.id: _snapshot(source_device.id)}
    coordinator.creatable_kinds_for_device = Mock(return_value=[SENSOR_KIND_AIR])
    coordinator.async_add_listener = Mock(return_value=Mock())
    added_entities: list[DerivedValueSensor] = []

    def _capture_add_entities(
        new_entities: Iterable[Entity],
        update_before_add: bool = False,
        *,
        config_subentry_id: str | None = None,
    ) -> None:
        _ = (update_before_add, config_subentry_id)
        added_entities.extend(new_entities)
        entity_registry = er.async_get(hass)
        for new_entity in new_entities:
            entity_registry.async_get_or_create(
                "sensor",
                DOMAIN,
                new_entity.unique_id,
                config_entry=entry,
                device_id=(
                    new_entity.device_entry.id
                    if new_entity.device_entry
                    else None
                ),
                original_name=new_entity.name,
            )

    await async_setup_entry(hass, entry, _capture_add_entities)

    assert len(added_entities) == 1
    added_sensor = added_entities[0]
    assert added_sensor.device_entry == source_device

    all_devices = list(device_registry.devices.values())
    assert len(all_devices) == 1

    entity_registry = er.async_get(hass)
    entity_id = entity_registry.async_get_entity_id(
        "sensor", DOMAIN, make_vpdair_unique_id(source_device.id)
    )
    registry_entry = entity_registry.async_get(entity_id) if entity_id else None
    assert registry_entry is not None
    assert registry_entry.device_id == source_device.id


async def test_sync_keeps_registry_entry_when_kind_is_not_creatable(
    hass: HomeAssistant,
) -> None:
    """Test registry entries are not removed when kind becomes non-creatable."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    coordinator = VpdAirCoordinator(hass, entry, _options())
    entry.runtime_data = coordinator
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("test", "policy-disable")},
        name="Policy Disable Device",
    )
    coordinator.data = {device.id: _snapshot(device.id)}
    coordinator.creatable_kinds_for_device = Mock(return_value=[SENSOR_KIND_AIR])
    coordinator.async_add_listener = Mock(return_value=Mock())
    added_entities: list[DerivedValueSensor] = []

    def _capture_add_entities(new_entities: Iterable[Entity], **_: object) -> None:
        added_entities.extend(new_entities)

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

    await async_setup_entry(hass, entry, _capture_add_entities)
    sync_callback = coordinator.async_add_listener.call_args.args[0]
    sync_callback()

    assert entity_registry.async_get(stale.entity_id) is not None
    entity_registry.async_remove.assert_not_called()
    assert {(entity._device_id, entity._kind) for entity in added_entities} == {
        (device.id, SENSOR_KIND_AIR)
    }


async def test_sync_keeps_registry_entries_when_coordinator_data_missing(
    hass: HomeAssistant,
) -> None:
    """Test registry entries are preserved when coordinator data becomes empty."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    coordinator = VpdAirCoordinator(hass, entry, _options())
    entry.runtime_data = coordinator
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("test", "missing-data")},
        name="Missing Data Device",
    )
    coordinator.data = {device.id: _snapshot(device.id)}
    coordinator.creatable_kinds_for_device = Mock(return_value=[SENSOR_KIND_AIR])
    coordinator.async_add_listener = Mock(return_value=Mock())
    added_entities: list[DerivedValueSensor] = []

    def _capture_add_entities(new_entities: Iterable[Entity], **_: object) -> None:
        added_entities.extend(new_entities)

    entity_registry = er.async_get(hass)
    air = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        make_vpdair_unique_id(device.id),
        config_entry=entry,
        device_id=device.id,
        original_name="VPDair",
    )
    leaf = entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        make_vpdleaf_unique_id(device.id),
        config_entry=entry,
        device_id=device.id,
        original_name="VPDleaf",
    )
    entity_registry.async_remove = Mock(wraps=entity_registry.async_remove)

    await async_setup_entry(hass, entry, _capture_add_entities)
    assert len(added_entities) == 1
    coordinator.data = {}
    sync_callback = coordinator.async_add_listener.call_args.args[0]
    sync_callback()

    assert entity_registry.async_get(air.entity_id) is not None
    assert entity_registry.async_get(leaf.entity_id) is not None
    entity_registry.async_remove.assert_not_called()
    assert len(added_entities) == 1
