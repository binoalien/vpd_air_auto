"""Tests for source-state subscriptions service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.vpd_air_auto.models import DeviceTopology
from custom_components.vpd_air_auto.services.subscriptions import SubscriptionManager


def test_refresh_tracks_entities_for_active_devices(hass: HomeAssistant) -> None:
    manager = SubscriptionManager(hass)
    topology = {
        "device-1": DeviceTopology(
            "device-1", "Grow Tent", "sensor.grow_temp", "sensor.grow_humidity"
        ),
        "device-2": DeviceTopology(
            "device-2", "Dry Room", "sensor.dry_temp", "sensor.dry_humidity"
        ),
    }
    handler = AsyncMock()
    unsub = MagicMock()

    with patch(
        "custom_components.vpd_air_auto.services.subscriptions.async_track_state_change_event",
        return_value=unsub,
    ) as mock_track:
        tracked = manager.refresh(
            active_device_ids={"device-1"},
            topology_by_device_id=topology,
            handler=handler,
        )

    assert tracked == {"sensor.grow_temp", "sensor.grow_humidity"}
    assert manager.tracked_entity_ids == {"sensor.grow_temp", "sensor.grow_humidity"}
    mock_track.assert_called_once()


def test_refresh_replaces_listener_when_tracked_entities_change(
    hass: HomeAssistant,
) -> None:
    manager = SubscriptionManager(hass)
    topology = {
        "device-1": DeviceTopology(
            "device-1", "Grow Tent", "sensor.grow_temp", "sensor.grow_humidity"
        ),
        "device-2": DeviceTopology(
            "device-2", "Dry Room", "sensor.dry_temp", "sensor.dry_humidity"
        ),
    }
    handler = AsyncMock()
    first_unsub = MagicMock()
    second_unsub = MagicMock()

    with patch(
        "custom_components.vpd_air_auto.services.subscriptions.async_track_state_change_event",
        side_effect=[first_unsub, second_unsub],
    ):
        manager.refresh(
            active_device_ids={"device-1"},
            topology_by_device_id=topology,
            handler=handler,
        )
        manager.refresh(
            active_device_ids={"device-2"},
            topology_by_device_id=topology,
            handler=handler,
        )

    first_unsub.assert_called_once()
    assert manager.tracked_entity_ids == {"sensor.dry_temp", "sensor.dry_humidity"}


async def test_shutdown_unsubscribes_and_clears_tracked_entities(
    hass: HomeAssistant,
) -> None:
    manager = SubscriptionManager(hass)
    topology = {
        "device-1": DeviceTopology(
            "device-1", "Grow Tent", "sensor.grow_temp", "sensor.grow_humidity"
        )
    }
    handler = AsyncMock()
    unsub = MagicMock()

    with patch(
        "custom_components.vpd_air_auto.services.subscriptions.async_track_state_change_event",
        return_value=unsub,
    ):
        manager.refresh(
            active_device_ids={"device-1"},
            topology_by_device_id=topology,
            handler=handler,
        )

    await manager.shutdown()

    unsub.assert_called_once()
    assert manager.tracked_entity_ids == set()
