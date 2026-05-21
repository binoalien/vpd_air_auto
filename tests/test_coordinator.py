"""Tests for the VPD Air Auto coordinator."""

# pylint: disable=protected-access,too-many-arguments

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import ANY, AsyncMock, MagicMock, patch

from homeassistant.core import Event, HomeAssistant, State
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vpd_air_auto.const import (
    CONF_ENABLE_AIR,
    CONF_ENABLE_LEAF,
    CONF_LEAF_OFFSET,
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
from custom_components.vpd_air_auto.policy.models import SourceOverride


def _options(
    *,
    enable_air: bool = True,
    enable_leaf: bool = True,
    enable_absolute_humidity: bool = True,
    enable_dew_point: bool = True,
    leaf_offset_c: float = -2.0,
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
        leaf_offset_c=leaf_offset_c,
        absolute_humidity_icon="mdi:water",
        absolute_humidity_display_name="Absolute Humidity",
        dew_point_icon="mdi:thermometer-water",
        dew_point_display_name="Dew Point",
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
    hass: HomeAssistant,
    *,
    options: IntegrationOptions | None = None,
    entry_options: dict[str, Any] | None = None,
) -> VpdAirCoordinator:
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=entry_options or {})
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
    interval_unsub = MagicMock()
    coordinator._unsub_periodic_rescan = interval_unsub

    with patch.object(
        coordinator._subscription_manager,
        "shutdown",
        new=AsyncMock(),
    ) as mock_shutdown:
        await coordinator.async_shutdown()

    mock_shutdown.assert_awaited_once()
    interval_unsub.assert_called_once()
    assert coordinator._unsub_periodic_rescan is None


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
            coordinator._topology_discovery_service,
            "discover",
            return_value=topology,
        ) as mock_discover,
        patch.object(
            coordinator._snapshot_builder,
            "build_snapshot",
            return_value=snapshot,
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
    mock_discover.assert_called_once_with(source_overrides={})
    mock_build.assert_called_once_with(topology["device-1"], ANY)
    mock_refresh.assert_called_once()


async def test_async_update_data_skips_disabled_device_and_does_not_track_source(
    hass: HomeAssistant,
) -> None:
    """Disabled by area policy means no snapshot and no source tracking."""
    coordinator = _build_coordinator(
        hass,
        entry_options={
            "area_policies": {
                "area-1": {
                    CONF_ENABLE_AIR: False,
                    CONF_ENABLE_LEAF: False,
                }
            }
        },
    )
    topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
            blocked_sensor_kinds=frozenset(
                {SENSOR_KIND_ABSOLUTE_HUMIDITY, SENSOR_KIND_DEW_POINT}
            ),
            area_id="area-1",
        )
    }

    with (
        patch.object(
            coordinator._topology_discovery_service,
            "discover",
            return_value=topology,
        ),
        patch.object(coordinator._snapshot_builder, "build_snapshot") as mock_build,
        patch.object(coordinator, "_refresh_state_listener"),
    ):
        result = await coordinator._async_update_data()

    assert result == {}
    assert coordinator._source_to_device == {}
    mock_build.assert_not_called()


async def test_async_update_data_passes_source_overrides_to_discovery(
    hass: HomeAssistant,
) -> None:
    """Coordinator forwards parsed source overrides to topology discovery."""
    coordinator = _build_coordinator(
        hass,
        entry_options={
            "source_overrides": {
                "device-1": {"temperature_entity_id": "sensor.manual_temp"}
            }
        },
    )
    with (
        patch.object(
            coordinator._topology_discovery_service,
            "discover",
            return_value={},
        ) as mock_discover,
        patch.object(coordinator, "_refresh_state_listener"),
    ):
        await coordinator._async_update_data()

    mock_discover.assert_called_once_with(
        source_overrides={
            "device-1": SourceOverride(temperature_entity_id="sensor.manual_temp")
        }
    )


async def test_async_update_data_tracks_overridden_source_ids(
    hass: HomeAssistant,
) -> None:
    """Source map tracks override-selected entity IDs returned by discovery."""
    coordinator = _build_coordinator(hass)
    topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.manual_temp",
            humidity_entity_id="sensor.manual_hum",
            blocked_sensor_kinds=frozenset(),
        )
    }
    with (
        patch.object(
            coordinator._topology_discovery_service,
            "discover",
            return_value=topology,
        ),
        patch.object(
            coordinator._snapshot_builder,
            "build_snapshot",
            return_value=_snapshot("device-1"),
        ),
        patch.object(coordinator, "_refresh_state_listener"),
    ):
        await coordinator._async_update_data()

    assert coordinator._source_to_device == {
        "sensor.manual_temp": "device-1",
        "sensor.manual_hum": "device-1",
    }


async def test_source_state_changed_ignores_old_auto_entity_when_override_tracked(
    hass: HomeAssistant,
) -> None:
    """Untracked old auto source must not trigger snapshot rebuild."""
    coordinator = _build_coordinator(hass)
    topology = DeviceTopology(
        device_id="device-1",
        device_name="Grow Tent",
        temperature_entity_id="sensor.manual_temp",
        humidity_entity_id="sensor.manual_hum",
    )
    current_snapshot = _snapshot("device-1")
    coordinator._topology = {"device-1": topology}
    coordinator._source_to_device = {"sensor.manual_hum": "device-1"}
    coordinator.data = {"device-1": current_snapshot}
    coordinator._snapshot_builder.build_snapshot = MagicMock(
        return_value=current_snapshot
    )
    coordinator.async_set_updated_data = MagicMock()

    await coordinator._async_handle_source_state_changed(
        Event(
            "state_changed",
            data=EventStateChangedData(
                entity_id="sensor.auto_hum",
                old_state=State("sensor.auto_hum", state="old"),
                new_state=State("sensor.auto_hum", state="new"),
            ),
        )
    )

    coordinator._snapshot_builder.build_snapshot.assert_not_called()
    coordinator.async_set_updated_data.assert_not_called()


async def test_periodic_rescan_requests_refresh(hass: HomeAssistant) -> None:
    """Test periodic rescan requests refresh."""
    coordinator = _build_coordinator(hass)
    coordinator.async_request_refresh = AsyncMock()

    await coordinator._async_handle_periodic_rescan(datetime.now())

    coordinator.async_request_refresh.assert_awaited_once()


def test_creatable_kinds_for_device_delegates_to_entity_plan_service(
    hass: HomeAssistant,
) -> None:
    """Test creatable kinds for device delegates to entity plan service."""
    coordinator = _build_coordinator(hass)
    topology = DeviceTopology(
        device_id="device-1",
        device_name="Grow Tent",
        temperature_entity_id="sensor.grow_tent_temperature",
        humidity_entity_id="sensor.grow_tent_humidity",
        blocked_sensor_kinds=frozenset({SENSOR_KIND_AIR}),
    )
    coordinator._topology = {"device-1": topology}

    with patch.object(
        coordinator._entity_plan_service,
        "creatable_kinds_for_topology",
        return_value={SENSOR_KIND_ABSOLUTE_HUMIDITY, SENSOR_KIND_DEW_POINT},
    ) as mock_creatable:
        assert coordinator.creatable_kinds_for_device("device-1") == {
            SENSOR_KIND_ABSOLUTE_HUMIDITY,
            SENSOR_KIND_DEW_POINT,
        }

    mock_creatable.assert_called_once()
    assert coordinator.creatable_kinds_for_device("missing") == set()


def test_diagnostics_payload_contains_options_topology_snapshots_and_tracked_sources(
    hass: HomeAssistant,
) -> None:
    """Test diagnostics payload includes options, topology, snapshots, and sources."""
    coordinator = _build_coordinator(hass)
    coordinator._subscription_manager._tracked_entity_ids = {
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
    assert diagnostics["policy"]["global_policy"]["leaf_offset_c"] == -2.0
    assert diagnostics["effective_policies"]["device-1"]["behavior_source"] == "global"
    assert diagnostics["entity_plan"]["device-1"]["blocked_sensor_kinds"] == [SENSOR_KIND_LEAF]


def _contexts(device_ids: set[str]):
    yield from device_ids


def test_refresh_state_listener_delegates_to_subscription_manager(
    hass: HomeAssistant,
) -> None:
    """Test refresh state listener delegates to subscription manager."""
    coordinator = _build_coordinator(hass)
    coordinator._topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
        )
    }
    coordinator.async_contexts = lambda: _contexts({"device-1"})

    with patch.object(coordinator._subscription_manager, "refresh") as mock_refresh:
        coordinator._refresh_state_listener()

    mock_refresh.assert_called_once()
    kwargs = mock_refresh.call_args.kwargs
    assert kwargs["active_device_ids"] == {"device-1"}
    assert kwargs["topology_by_device_id"] == coordinator._topology
    handler = kwargs["handler"]
    assert callable(handler)
    assert handler.__self__ is coordinator
    assert handler.__func__ is coordinator._async_handle_source_state_changed.__func__


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
    coordinator._snapshot_builder.build_snapshot = MagicMock(return_value=next_snapshot)
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

    coordinator._snapshot_builder.build_snapshot.assert_called_once_with(topology, ANY)
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
    coordinator._snapshot_builder.build_snapshot = MagicMock(
        return_value=current_snapshot
    )
    coordinator.async_set_updated_data = MagicMock()

    await coordinator._async_handle_source_state_changed(
        Event(
            "state_changed",
            data=EventStateChangedData(
                entity_id="sensor.unknown",
                old_state=None,
                new_state=None,
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


async def test_flat_options_runtime_policy_respected_in_snapshot_builder(
    hass: HomeAssistant,
) -> None:
    """Flat options must drive runtime policy even without global_policy key."""
    coordinator = _build_coordinator(
        hass,
        options=_options(enable_air=False, leaf_offset_c=-1.1),
        entry_options={CONF_ENABLE_AIR: False, CONF_LEAF_OFFSET: -1.1},
    )
    topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
            blocked_sensor_kinds=frozenset(
                {SENSOR_KIND_AIR, SENSOR_KIND_ABSOLUTE_HUMIDITY, SENSOR_KIND_DEW_POINT}
            ),
        )
    }

    with (
        patch.object(
            coordinator._topology_discovery_service,
            "discover",
            return_value=topology,
        ),
        patch.object(
            coordinator._snapshot_builder,
            "build_snapshot",
            return_value=_snapshot("device-1"),
        ) as mock_build,
        patch.object(coordinator, "_refresh_state_listener"),
    ):
        await coordinator._async_update_data()

    policy = mock_build.call_args.args[1]
    assert policy.enable_air is False
    assert policy.leaf_offset_c == -1.1


async def test_source_change_does_not_re_add_policy_filtered_device(
    hass: HomeAssistant,
) -> None:
    """Policy-filtered devices should not be re-added by source updates."""
    coordinator = _build_coordinator(
        hass,
        entry_options={
            "area_policies": {
                "area-1": {
                    CONF_ENABLE_AIR: False,
                    CONF_ENABLE_LEAF: False,
                }
            }
        },
    )
    topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
            blocked_sensor_kinds=frozenset(
                {SENSOR_KIND_ABSOLUTE_HUMIDITY, SENSOR_KIND_DEW_POINT}
            ),
            area_id="area-1",
        )
    }

    with patch.object(
        coordinator._topology_discovery_service,
        "discover",
        return_value=topology,
    ):
        await coordinator._async_update_data()

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

    coordinator.async_set_updated_data.assert_not_called()


async def test_global_disabled_area_enabled_device_stays_active_and_uses_area_offset(
    hass: HomeAssistant,
) -> None:
    """Area override should enable a globally disabled device and set leaf offset."""
    coordinator = _build_coordinator(
        hass,
        options=_options(
            enable_air=False,
            enable_leaf=False,
            enable_absolute_humidity=False,
            enable_dew_point=False,
            leaf_offset_c=-2.0,
        ),
        entry_options={
            "area_policies": {
                "area-1": {
                    CONF_ENABLE_AIR: True,
                    CONF_LEAF_OFFSET: -0.8,
                }
            }
        },
    )
    topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
            blocked_sensor_kinds=frozenset(
                {SENSOR_KIND_LEAF, SENSOR_KIND_ABSOLUTE_HUMIDITY, SENSOR_KIND_DEW_POINT}
            ),
            area_id="area-1",
        )
    }

    with (
        patch.object(
            coordinator._topology_discovery_service,
            "discover",
            return_value=topology,
        ),
        patch.object(
            coordinator._snapshot_builder,
            "build_snapshot",
            return_value=_snapshot("device-1"),
        ) as mock_build,
        patch.object(coordinator, "_refresh_state_listener"),
    ):
        result = await coordinator._async_update_data()

    assert result == {"device-1": _snapshot("device-1")}
    policy = mock_build.call_args.args[1]
    assert policy.enable_air is True
    assert policy.leaf_offset_c == -0.8


async def test_device_policy_overrides_area_and_global_at_runtime(
    hass: HomeAssistant,
) -> None:
    """Device-level policy should win over area and global defaults at runtime."""
    coordinator = _build_coordinator(
        hass,
        options=_options(enable_air=False, leaf_offset_c=-2.0),
        entry_options={
            "area_policies": {
                "area-1": {
                    CONF_ENABLE_AIR: False,
                    CONF_LEAF_OFFSET: -0.8,
                }
            },
            "device_policies": {
                "device-1": {
                    CONF_ENABLE_AIR: True,
                    CONF_LEAF_OFFSET: -1.4,
                }
            },
        },
    )
    topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
            blocked_sensor_kinds=frozenset(
                {SENSOR_KIND_LEAF, SENSOR_KIND_ABSOLUTE_HUMIDITY, SENSOR_KIND_DEW_POINT}
            ),
            area_id="area-1",
        )
    }

    with (
        patch.object(
            coordinator._topology_discovery_service,
            "discover",
            return_value=topology,
        ),
        patch.object(
            coordinator._snapshot_builder,
            "build_snapshot",
            return_value=_snapshot("device-1"),
        ) as mock_build,
        patch.object(coordinator, "_refresh_state_listener"),
    ):
        result = await coordinator._async_update_data()

    assert result == {"device-1": _snapshot("device-1")}
    policy = mock_build.call_args.args[1]
    assert policy.enable_air is True
    assert policy.leaf_offset_c == -1.4
    assert policy.behavior_source == "device"
    assert policy.leaf_offset_source == "device"
