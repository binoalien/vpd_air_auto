"""Tests for subscription manager."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.vpd_air_auto.models import DeviceTopology
from custom_components.vpd_air_auto.services.subscriptions import SubscriptionManager


def test_refresh_tracks_sources_for_active_contexts(hass: HomeAssistant) -> None:
    """It subscribes only to source entities of active devices."""
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

    with patch(
        "custom_components.vpd_air_auto.services.subscriptions.async_track_state_change_event",
        return_value=MagicMock(),
    ) as mock_track:
        tracked = manager.refresh(
            active_device_ids={"device-1"},
            topology_by_device_id=topology,
            handler=AsyncMock(),
        )

    assert tracked == {"sensor.grow_tent_temperature", "sensor.grow_tent_humidity"}
    assert manager.tracked_entity_ids == tracked
    mock_track.assert_called_once()


def test_refresh_replaces_listener_when_tracked_set_changes(hass: HomeAssistant) -> None:
    """It unsubscribes previous listener before replacing it."""
    manager = SubscriptionManager(hass)
    topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
        )
    }
    unsub_old = MagicMock()
    unsub_new = MagicMock()

    with patch(
        "custom_components.vpd_air_auto.services.subscriptions.async_track_state_change_event",
        side_effect=[unsub_old, unsub_new],
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

    unsub_old.assert_called_once()
    assert manager.tracked_entity_ids == {
        "sensor.grow_tent_temperature",
        "sensor.grow_tent_humidity",
    }
    assert manager._unsub_state_listener is unsub_new


async def test_shutdown_clears_listener_and_tracked_entities(hass: HomeAssistant) -> None:
    """It unsubscribes and clears tracked state on shutdown."""
    manager = SubscriptionManager(hass)
    unsub = MagicMock()
    manager._unsub_state_listener = unsub
    manager._tracked_entity_ids = {"sensor.a"}

    await manager.shutdown()

    unsub.assert_called_once()
    assert manager.tracked_entity_ids == set()
    assert manager._unsub_state_listener is None
