"""Subscription management for source entity state changes."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_state_change_event,
)

from ..models import DeviceTopology

type StateChangedHandler = Callable[[Event[EventStateChangedData]], Awaitable[None]]


class SubscriptionManager:
    """Manage source-state subscriptions for active coordinator contexts."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the manager."""
        self._hass = hass
        self._tracked_entity_ids: set[str] = set()
        self._unsub_state_listener: Callable[[], None] | None = None

    @property
    def tracked_entity_ids(self) -> set[str]:
        """Return the currently tracked source entity IDs."""
        return self._tracked_entity_ids

    @callback
    def refresh(
        self,
        *,
        active_device_ids: set[str],
        topology_by_device_id: dict[str, DeviceTopology],
        handler: StateChangedHandler,
    ) -> set[str]:
        """Update state-change listener for currently active device sources."""
        tracked_entity_ids = {
            entity_id
            for device_id in active_device_ids
            for topology in [topology_by_device_id.get(device_id)]
            if topology is not None
            for entity_id in (
                topology.temperature_entity_id,
                topology.humidity_entity_id,
            )
        }

        if tracked_entity_ids == self._tracked_entity_ids:
            return self._tracked_entity_ids

        if self._unsub_state_listener is not None:
            self._unsub_state_listener()
            self._unsub_state_listener = None

        self._tracked_entity_ids = tracked_entity_ids
        if not tracked_entity_ids:
            return self._tracked_entity_ids

        self._unsub_state_listener = async_track_state_change_event(
            self._hass,
            tracked_entity_ids,
            handler,
        )
        return self._tracked_entity_ids

    async def shutdown(self) -> None:
        """Tear down the active state-change listener."""
        if self._unsub_state_listener is not None:
            self._unsub_state_listener()
            self._unsub_state_listener = None
