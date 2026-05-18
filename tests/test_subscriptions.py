"""Tests for source subscription management."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.vpd_air_auto.models import DeviceTopology
from custom_components.vpd_air_auto.services.subscriptions import SubscriptionManager


def test_refresh_tracks_active_context_sources(hass: HomeAssistant) -> None:
    """Test manager tracks source entities for active device contexts."""
    manager = SubscriptionManager(hass)
    topology = {
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

    unsub = MagicMock()
    with patch(
        "custom_components.vpd_air_auto.services.subscriptions.async_track_state_change_event",
        return_value=unsub,
    ) as mock_track:
        tracked = manager.refresh(
            active_device_ids={"device-1"},
            topology_by_device_id=topology,
            handler=AsyncMock(),
        )

    assert tracked == {
        "sensor.grow_tent_temperature",
        "sensor.grow_tent_humidity",
    }
    assert manager.tracked_entity_ids == tracked
    mock_track.assert_called_once()


def test_refresh_replaces_listener_on_tracked_entity_change(hass: HomeAssistant) -> None:
    """Test manager replaces listener when active tracked entities change."""
    manager = SubscriptionManager(hass)
    topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
        )
    }

    first_unsub = MagicMock()
    second_unsub = MagicMock()
    with patch(
        "custom_components.vpd_air_auto.services.subscriptions.async_track_state_change_event",
        side_effect=[first_unsub, second_unsub],
    ):
        manager.refresh(
            active_device_ids={"device-1"},
            topology_by_device_id=topology,
            handler=AsyncMock(),
        )
        manager.refresh(
            active_device_ids=set(),
            topology_by_device_id=topology,
            handler=AsyncMock(),
        )
        manager.refresh(
            active_device_ids={"device-1"},
            topology_by_device_id=topology,
            handler=AsyncMock(),
        )

    first_unsub.assert_called_once()
    second_unsub.assert_not_called()


async def test_shutdown_unsubscribes_active_listener(hass: HomeAssistant) -> None:
    """Test shutdown unsubscribes active listener."""
    manager = SubscriptionManager(hass)
    topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
        )
    }

    unsub = MagicMock()
    with patch(
        "custom_components.vpd_air_auto.services.subscriptions.async_track_state_change_event",
        return_value=unsub,
    ):
        manager.refresh(
            active_device_ids={"device-1"},
            topology_by_device_id=topology,
            handler=AsyncMock(),
        )

    await manager.shutdown()

    unsub.assert_called_once()
    assert manager.tracked_entity_ids == {
        "sensor.grow_tent_temperature",
        "sensor.grow_tent_humidity",
    }
