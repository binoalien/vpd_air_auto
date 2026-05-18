"""Tests for subscription manager."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.vpd_air_auto.models import DeviceTopology
from custom_components.vpd_air_auto.services.subscriptions import SubscriptionManager


def test_refresh_tracks_active_context_sources(hass) -> None:
    manager = SubscriptionManager(hass)
    topology = {
        "device-1": DeviceTopology("device-1", "Grow Tent", "sensor.t1", "sensor.h1"),
        "device-2": DeviceTopology("device-2", "Dry Room", "sensor.t2", "sensor.h2"),
    }
    handler = AsyncMock()
    unsub = MagicMock()

    with patch(
        "custom_components.vpd_air_auto.services.subscriptions.async_track_state_change_event",
        return_value=unsub,
    ) as mock_track:
        tracked = manager.refresh(
            active_device_ids={"device-1"}, topology_by_device_id=topology, handler=handler
        )

    assert tracked == {"sensor.t1", "sensor.h1"}
    assert manager.tracked_entity_ids == {"sensor.t1", "sensor.h1"}
    mock_track.assert_called_once()


def test_refresh_replaces_listener_when_tracked_entities_change(hass) -> None:
    manager = SubscriptionManager(hass)
    topology = {
        "device-1": DeviceTopology("device-1", "Grow Tent", "sensor.t1", "sensor.h1"),
    }
    handler = AsyncMock()
    first_unsub = MagicMock()
    second_unsub = MagicMock()

    with patch(
        "custom_components.vpd_air_auto.services.subscriptions.async_track_state_change_event",
        side_effect=[first_unsub, second_unsub],
    ):
        manager.refresh(active_device_ids={"device-1"}, topology_by_device_id=topology, handler=handler)
        manager.refresh(active_device_ids=set(), topology_by_device_id=topology, handler=handler)

    first_unsub.assert_called_once()
    assert manager.tracked_entity_ids == set()


async def test_shutdown_clears_listener_and_tracked_entities(hass) -> None:
    manager = SubscriptionManager(hass)
    topology = {
        "device-1": DeviceTopology("device-1", "Grow Tent", "sensor.t1", "sensor.h1"),
    }
    handler = AsyncMock()
    unsub = MagicMock()

    with patch(
        "custom_components.vpd_air_auto.services.subscriptions.async_track_state_change_event",
        return_value=unsub,
    ):
        manager.refresh(active_device_ids={"device-1"}, topology_by_device_id=topology, handler=handler)

    await manager.shutdown()

    unsub.assert_called_once()
    assert manager.tracked_entity_ids == set()
