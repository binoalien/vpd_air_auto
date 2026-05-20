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


def test_refresh_replaces_listener_when_tracked_set_changes(
    hass: HomeAssistant,
) -> None:
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


def test_refresh_is_idempotent_for_unchanged_tracked_set(
    hass: HomeAssistant,
) -> None:
    """It does not re-subscribe when active device sources stay the same."""
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
    ) as mock_track:
        tracked_first = manager.refresh(
            active_device_ids={"device-1"},
            topology_by_device_id=topology,
            handler=AsyncMock(),
        )
        tracked_second = manager.refresh(
            active_device_ids={"device-1"},
            topology_by_device_id=topology,
            handler=AsyncMock(),
        )

    mock_track.assert_called_once()
    unsub.assert_not_called()
    assert tracked_first == tracked_second
    assert manager.tracked_entity_ids == {
        "sensor.grow_tent_temperature",
        "sensor.grow_tent_humidity",
    }


def test_refresh_with_empty_active_devices_skips_listener_creation(
    hass: HomeAssistant,
) -> None:
    """It returns empty set and does not install listener for empty contexts."""
    manager = SubscriptionManager(hass)
    topology = {
        "device-1": DeviceTopology(
            device_id="device-1",
            device_name="Grow Tent",
            temperature_entity_id="sensor.grow_tent_temperature",
            humidity_entity_id="sensor.grow_tent_humidity",
        )
    }

    with patch(
        "custom_components.vpd_air_auto.services.subscriptions.async_track_state_change_event"
    ) as mock_track:
        tracked = manager.refresh(
            active_device_ids=set(),
            topology_by_device_id=topology,
            handler=AsyncMock(),
        )

    assert tracked == set()
    assert manager.tracked_entity_ids == set()
    mock_track.assert_not_called()


async def test_shutdown_clears_listener_and_tracked_entities(
    hass: HomeAssistant,
) -> None:
    """It unsubscribes and clears tracked state on shutdown."""
    # pylint: disable=protected-access
    manager = SubscriptionManager(hass)
    unsub = MagicMock()
    manager._unsub_state_listener = unsub
    manager._tracked_entity_ids = {"sensor.a"}

    await manager.shutdown()

    unsub.assert_called_once()
    assert manager.tracked_entity_ids == set()
    assert manager._unsub_state_listener is None


async def test_shutdown_without_active_listener_is_safe(
    hass: HomeAssistant,
) -> None:
    """It is safe to shut down when no listener exists."""
    # pylint: disable=protected-access
    manager = SubscriptionManager(hass)

    await manager.shutdown()

    assert manager.tracked_entity_ids == set()
