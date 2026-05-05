"""Tests for the VPD Air Auto coordinator."""

# pylint: disable=protected-access,too-many-arguments

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import Event, HomeAssistant, State
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vpd_air_auto.const import (
    DOMAIN,
    SENSOR_KIND_ABSOLUTE_HUMIDITY,
    SENSOR_KIND_AIR,
    SENSOR_KIND_DEW_POINT,
    SENSOR_KIND_LEAF,
    IntegrationOptions,
)
from custom_components.vpd_air_auto.coordinator import (
    EventStateChangedData,
    VpdAirCoordinator,
)
from custom_components.vpd_air_auto.models import DeviceSnapshot, DeviceTopology


def _options(
    *,
    enable_air: bool = True,
    enable_leaf: bool = True,
    enable_absolute_humidity: bool = True,
    enable_dew_point: bool = True,
) -> IntegrationOptions:
    return IntegrationOptions(
        scan_interval_seconds=300,
        enable_air=enable_air,
        enable_leaf=enable_leaf,
        enable_absolute_humidity=enable_absolute_humidity,
        enable_dew_point=enable_dew_point,
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


def _device(device_id: str, name: str = "Grow Tent") -> SimpleNamespace:
    return SimpleNamespace(id=device_id, name=name, name_by_user=None)


def _entry(
    entity_id: str,
    *,
    platform: str = "test_platform",
    name: str | None = None,
    original_name: str | None = None,
    original_device_class: str | None = None,
    original_unit_of_measurement: str | None = None,
    entity_category: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        entity_id=entity_id,
        domain="sensor",
        platform=platform,
        name=name,
        original_name=original_name,
        original_device_class=original_device_class,
        original_unit_of_measurement=original_unit_of_measurement,
        entity_category=entity_category,
    )


def _snapshot(device_id: str, *, humidity_pct: float = 60.0) -> DeviceSnapshot:
    return DeviceSnapshot(
        device_id=device_id,
        device_name="Grow Tent",
        temperature_entity_id="sensor.grow_tent_temperature",
        humidity_entity_id="sensor.grow_tent_humidity",
        temperature_c=25.0,
        humidity_pct=humidity_pct,
        leaf_offset_c=-2.0,
        leaf_temperature_c=23.0,
        dew_point_c=16.68,
        vpd_air_kpa=1.27,
        vpd_leaf_kpa=1.58,
        absolute_humidity_gm3=13.8,
    )


def _build_coordinator(
    hass: HomeAssistant, *, options: IntegrationOptions | None = None
) -> VpdAirCoordinator:
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    return VpdAirCoordinator(hass, entry, options or _options())


async def test_async_setup_registers_periodic_rescan_listener(
    hass: HomeAssistant,
) -> None:
    """Test async setup registers periodic rescan listener."""
    coordinator = _build_coordinator(hass)
    unsub = MagicMock()

    with patch(
        "custom_components.vpd_air_auto.coordinator.async_track_time_interval",
        return_value=unsub,
    ) as mock_track:
        await coordinator._async_setup()

    mock_track.assert_called_once()
    assert coordinator._unsub_periodic_rescan is unsub


async def test_async_shutdown_cleans_up_registered_listeners(
    hass: HomeAssistant,
) -> None:
    """Test async shutdown cleans up registered listeners."""
    coordinator = _build_coordinator(hass)
    state_unsub = MagicMock()
    interval_unsub = MagicMock()
    coordinator._unsub_state_listener = state_unsub
    coordinator._unsub_periodic_rescan = interval_unsub

    await coordinator.async_shutdown()

    state_unsub.assert_called_once()
    interval_unsub.assert_called_once()
    assert coordinator._unsub_state_listener is None
    assert coordinator._unsub_periodic_rescan is None


async def test_async_update_data_returns_empty_when_all_sensor_types_disabled(
    hass: HomeAssistant,
) -> None:
    """Test async update data returns empty when all sensor types disabled."""
    coordinator = _build_coordinator(
        hass,
        options=_options(
            enable_air=False,
            enable_leaf=False,
            enable_absolute_humidity=False,
            enable_dew_point=False,
        ),
    )
    coordinator._topology = {
        "old": DeviceTopology("old", "Old", "sensor.old_temp", "sensor.old_humidity")
    }
    coordinator._source_to_device = {"sensor.old_temp": "old"}
    coordinator._tracked_entity_ids = {"sensor.old_temp"}

    with patch.object(coordinator, "_refresh_state_listener") as mock_refresh:
        result = await coordinator._async_update_data()

    assert result == {}
    assert not coordinator._topology
    assert coordinator._source_to_device == {}
    mock_refresh.assert_called_once()


async def test_async_update_data_discovers_topology_builds_snapshots_and_maps_sources(
    hass: HomeAssistant,
) -> None:
    """Test async update data discovers topology builds snapshots and maps sources."""
    coordinator = _build_coordinator(hass)
    topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
            blocked_sensor_kinds=frozenset(),
        )
    }
    snapshot = _snapshot("device-1")

    with (
        patch.object(
            coordinator, "_discover_topology", return_value=topology
        ) as mock_discover,
        patch.object(
            coordinator, "_build_snapshot_for_topology", return_value=snapshot
        ) as mock_build,
        patch.object(coordinator, "_refresh_state_listener") as mock_refresh,
    ):
        result = await coordinator._async_update_data()

    assert result == {"device-1": snapshot}
    assert coordinator._topology == topology
    assert coordinator._source_to_device == {
        "sensor.grow_tent_temperature": "device-1",
        "sensor.grow_tent_humidity": "device-1",
    }
    mock_discover.assert_called_once()
    mock_build.assert_called_once_with(topology["device-1"])
    mock_refresh.assert_called_once()


async def test_periodic_rescan_requests_refresh(hass: HomeAssistant) -> None:
    """Test periodic rescan requests refresh."""
    coordinator = _build_coordinator(hass)
    coordinator.async_request_refresh = AsyncMock()

    await coordinator._async_handle_periodic_rescan(datetime.now())

    coordinator.async_request_refresh.assert_awaited_once()


def test_creatable_kinds_for_device_respects_enabled_flags_and_blocked_kinds(
    hass: HomeAssistant,
) -> None:
    """Test creatable kinds for device respects enabled flags and blocked kinds."""
    coordinator = _build_coordinator(
        hass,
        options=_options(
            enable_air=True,
            enable_leaf=False,
            enable_absolute_humidity=True,
            enable_dew_point=True,
        ),
    )
    coordinator._topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
            blocked_sensor_kinds=frozenset({SENSOR_KIND_AIR}),
        )
    }

    creatable = coordinator.creatable_kinds_for_device("device-1")

    assert creatable == {SENSOR_KIND_ABSOLUTE_HUMIDITY, SENSOR_KIND_DEW_POINT}
    assert coordinator.creatable_kinds_for_device("missing") == set()


def test_diagnostics_payload_contains_options_topology_snapshots_and_tracked_sources(
    hass: HomeAssistant,
) -> None:
    """
    Test diagnostics payload contains options, topology snapshots, and tracked sources.

    This test verifies that the diagnostics payload includes the expected options,
    topology snapshots, and tracked sources.
    """
    coordinator = _build_coordinator(hass)
    coordinator._tracked_entity_ids = {
        "sensor.grow_tent_temperature",
        "sensor.grow_tent_humidity",
    }
    coordinator._topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
            blocked_sensor_kinds=frozenset({SENSOR_KIND_LEAF}),
        )
    }
    coordinator.data = {"device-1": _snapshot("device-1")}

    diagnostics: dict[str, Any] = coordinator.diagnostics_payload()

    assert diagnostics["options"]["display_name"] == "VPDair"
    assert diagnostics["options"]["dew_point_display_name"] == "Dew Point"
    assert diagnostics["tracked_entity_ids"] == [
        "sensor.grow_tent_humidity",
        "sensor.grow_tent_temperature",
    ]
    assert diagnostics["topology"]["device-1"]["blocked_sensor_kinds"] == frozenset(
        {SENSOR_KIND_LEAF}
    )
    assert diagnostics["snapshots"]["device-1"]["vpd_air_kpa"] == 1.27
    assert diagnostics["snapshots"]["device-1"]["dew_point_c"] == 16.68


def _contexts(device_ids: set[str]):
    yield from device_ids


def test_refresh_state_listener_tracks_only_active_context_sources(
    hass: HomeAssistant,
) -> None:
    """Test refresh state listener tracks only active context sources."""
    coordinator = _build_coordinator(hass)
    coordinator._topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
        ),
        "device-2": DeviceTopology(
            device_id="device-2",
            device_name="Dry Room",
            temperature_entity_id="sensor.dry_room_temperature",
            humidity_entity_id="sensor.dry_room_humidity",
        ),
    }
    coordinator.async_contexts = lambda: _contexts({"device-1"})
    unsub = MagicMock()

    with patch(
        "custom_components.vpd_air_auto.coordinator.async_track_state_change_event",
        return_value=unsub,
    ) as mock_track:
        coordinator._refresh_state_listener()

    assert coordinator._tracked_entity_ids == {
        "sensor.grow_tent_temperature",
        "sensor.grow_tent_humidity",
    }
    mock_track.assert_called_once()
    assert coordinator._unsub_state_listener is unsub

    coordinator.async_contexts = lambda: _contexts(set())
    coordinator._refresh_state_listener()
    unsub.assert_called_once()
    assert coordinator._tracked_entity_ids == set()


async def test_source_state_changed_updates_only_affected_device(
    hass: HomeAssistant,
) -> None:
    """Test source state changed updates only affected device."""
    coordinator = _build_coordinator(hass)
    topology = DeviceTopology(
        device_id="device-1",
        device_name="Grow Tent",
        temperature_entity_id="sensor.grow_tent_temperature",
        humidity_entity_id="sensor.grow_tent_humidity",
    )
    current_snapshot = _snapshot("device-1", humidity_pct=60.0)
    next_snapshot = _snapshot("device-1", humidity_pct=65.0)
    coordinator._topology = {"device-1": topology}
    coordinator._source_to_device = {"sensor.grow_tent_humidity": "device-1"}
    coordinator.data = {"device-1": current_snapshot}
    coordinator._build_snapshot_for_topology = MagicMock(return_value=next_snapshot)
    coordinator.async_set_updated_data = MagicMock()

    await coordinator._async_handle_source_state_changed(
        Event(
            "state_changed",
            data=EventStateChangedData(
                entity_id="sensor.grow_tent_humidity",
                old_state=State("sensor.grow_tent_humidity", state="old"),
                new_state=State("sensor.grow_tent_humidity", state="new"),
            ),
        )
    )

    coordinator._build_snapshot_for_topology.assert_called_once_with(topology)
    coordinator.async_set_updated_data.assert_called_once_with(
        {"device-1": next_snapshot}
    )


async def test_source_state_changed_ignores_unknown_or_unchanged_sources(
    hass: HomeAssistant,
) -> None:
    """Test source state changed ignores unknown or unchanged sources."""
    coordinator = _build_coordinator(hass)
    topology = DeviceTopology(
        device_id="device-1",
        device_name="Grow Tent",
        temperature_entity_id="sensor.grow_tent_temperature",
        humidity_entity_id="sensor.grow_tent_humidity",
    )
    current_snapshot = _snapshot("device-1")
    coordinator._topology = {"device-1": topology}
    coordinator._source_to_device = {"sensor.grow_tent_humidity": "device-1"}
    coordinator.data = {"device-1": current_snapshot}
    coordinator._build_snapshot_for_topology = MagicMock(return_value=current_snapshot)
    coordinator.async_set_updated_data = MagicMock()

    await coordinator._async_handle_source_state_changed(
        Event(
            "state_changed",
            data=EventStateChangedData(
                entity_id="sensor.unknown", old_state=None, new_state=None
            ),
        )
    )
    await coordinator._async_handle_source_state_changed(
        Event(
            "state_changed",
            data=EventStateChangedData(
                entity_id="sensor.grow_tent_humidity",
                old_state=State("sensor.grow_tent_humidity", state="old"),
                new_state=State("sensor.grow_tent_humidity", state="new"),
            ),
        )
    )

    coordinator.async_set_updated_data.assert_not_called()


def test_discover_topology_selects_best_sources_and_blocks_duplicate_sensor_kinds(
    hass: HomeAssistant,
) -> None:
    """Test discover topology selects best sources and blocks duplicate sensor kinds."""
    coordinator = _build_coordinator(hass)
    device = _device("device-1")
    device_registry = SimpleNamespace(devices={device.id: device})
    entity_registry = SimpleNamespace()

    entries = [
        _entry(
            "sensor.grow_tent_temp_aux",
            original_name="Aux Temp",
            original_device_class="temperature",
            original_unit_of_measurement="°C",
        ),
        _entry(
            "sensor.grow_tent_temperature",
            original_name="Grow Tent Temperature",
            original_device_class="temperature",
            original_unit_of_measurement="°C",
        ),
        _entry(
            "sensor.grow_tent_humidity_generic",
            original_name="Humidity Generic",
            original_device_class="humidity",
            original_unit_of_measurement="%",
        ),
        _entry(
            "sensor.grow_tent_humidity",
            original_name="Grow Tent Humidity",
            original_device_class="humidity",
            original_unit_of_measurement="%",
        ),
        _entry(
            "sensor.grow_tent_vpdair_foreign",
            original_name="VPDair",
            original_device_class=None,
        ),
        _entry(
            "sensor.grow_tent_leaf_vpd_foreign",
            original_name="Leaf VPD",
            original_device_class=None,
        ),
        _entry(
            "sensor.grow_tent_absolute_humidity_foreign",
            original_name="Absolute Humidity",
            original_device_class="absolute_humidity",
        ),
        _entry(
            "sensor.grow_tent_dew_point_foreign",
            original_name="Dew Point",
            original_device_class=None,
        ),
        _entry(
            "sensor.own_helper_should_be_ignored",
            platform=DOMAIN,
            original_name="VPDair",
            original_device_class="humidity",
        ),
    ]

    hass.states.async_set(
        "sensor.grow_tent_temperature",
        "25.0",
        {
            "device_class": "temperature",
            "unit_of_measurement": "°C",
            "friendly_name": "Grow Tent Temperature",
        },
    )
    hass.states.async_set(
        "sensor.grow_tent_temp_aux",
        "24.8",
        {
            "device_class": "temperature",
            "unit_of_measurement": "°C",
            "friendly_name": "Aux Temp",
        },
    )
    hass.states.async_set(
        "sensor.grow_tent_humidity",
        "60",
        {
            "device_class": "humidity",
            "unit_of_measurement": "%",
            "friendly_name": "Grow Tent Humidity",
        },
    )
    hass.states.async_set(
        "sensor.grow_tent_humidity_generic",
        "59",
        {
            "device_class": "humidity",
            "unit_of_measurement": "%",
            "friendly_name": "Humidity Generic",
        },
    )
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
        {
            "friendly_name": "Dew Point",
            "unit_of_measurement": "°C",
            "device_class": "temperature",
        },
    )

    with (
        patch(
            "custom_components.vpd_air_auto.coordinator.dr.async_get",
            return_value=device_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.coordinator.er.async_get",
            return_value=entity_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.coordinator.er.async_entries_for_device",
            return_value=entries,
        ),
    ):
        topology = coordinator._discover_topology()

    assert topology["device-1"].temperature_entity_id == "sensor.grow_tent_temperature"
    assert topology["device-1"].humidity_entity_id == "sensor.grow_tent_humidity"
    assert topology["device-1"].blocked_sensor_kinds == frozenset(
        {
            SENSOR_KIND_AIR,
            SENSOR_KIND_LEAF,
            SENSOR_KIND_ABSOLUTE_HUMIDITY,
            SENSOR_KIND_DEW_POINT,
        }
    )


def test_discover_topology_skips_devices_without_complete_source_pair(
    hass: HomeAssistant,
) -> None:
    """Test discover topology skips devices without complete source pair."""
    coordinator = _build_coordinator(hass)
    device = _device("device-1")
    device_registry = SimpleNamespace(devices={device.id: device})
    entity_registry = SimpleNamespace()
    entries = [
        _entry(
            "sensor.grow_tent_temperature",
            original_name="Grow Tent Temperature",
            original_device_class="temperature",
            original_unit_of_measurement="°C",
        )
    ]
    hass.states.async_set(
        "sensor.grow_tent_temperature",
        "25.0",
        {"device_class": "temperature", "unit_of_measurement": "°C"},
    )

    with (
        patch(
            "custom_components.vpd_air_auto.coordinator.dr.async_get",
            return_value=device_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.coordinator.er.async_get",
            return_value=entity_registry,
        ),
        patch(
            "custom_components.vpd_air_auto.coordinator.er.async_entries_for_device",
            return_value=entries,
        ),
    ):
        topology = coordinator._discover_topology()

    assert not topology


def test_build_snapshot_for_topology_computes_all_values(hass: HomeAssistant) -> None:
    """Test build snapshot for topology computes all values."""
    coordinator = _build_coordinator(hass)
    topology = DeviceTopology(
        device_id="device-1",
        device_name="Grow Tent",
        temperature_entity_id="sensor.grow_tent_temperature",
        humidity_entity_id="sensor.grow_tent_humidity",
    )
    hass.states.async_set(
        "sensor.grow_tent_temperature",
        "25.0",
        {"device_class": "temperature", "unit_of_measurement": "°C"},
    )
    hass.states.async_set(
        "sensor.grow_tent_humidity",
        "60.0",
        {"device_class": "humidity", "unit_of_measurement": "%"},
    )

    snapshot = coordinator._build_snapshot_for_topology(topology)

    assert snapshot.temperature_c == 25.0
    assert snapshot.humidity_pct == 60.0
    assert snapshot.leaf_temperature_c == 23.0
    assert snapshot.vpd_air_kpa is not None
    assert snapshot.vpd_leaf_kpa is not None
    assert snapshot.absolute_humidity_gm3 is not None
