"""Coordinator for VPD Air Auto."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_time_interval,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, IntegrationOptions
from .discovery.duplicates import DuplicateDetectionService
from .discovery.topology import TopologyDiscoveryService
from .models import DeviceSnapshot, DeviceTopology
from .policy.repository import PolicyRepository
from .policy.resolver import PolicyResolver
from .services.entity_plan import EntityPlanService
from .services.snapshot_builder import SnapshotBuilder
from .services.subscriptions import SubscriptionManager

_LOGGER = logging.getLogger(__name__)


class VpdAirCoordinator(DataUpdateCoordinator[dict[str, DeviceSnapshot]]):  # pylint: disable=too-many-instance-attributes
    """Discover valid source devices and compute sensor values efficiently."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        options: IntegrationOptions,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            always_update=False,
        )
        self.config_entry = config_entry
        self.options = options
        self._scan_interval = timedelta(seconds=options.scan_interval_seconds)
        self._snapshot_builder = SnapshotBuilder(hass)
        self._duplicate_detection_service = DuplicateDetectionService(hass, options)
        self._topology_discovery_service = TopologyDiscoveryService(
            hass, self._duplicate_detection_service
        )
        self._entity_plan_service = EntityPlanService(options)
        self._policy_resolver = PolicyResolver(
            PolicyRepository({**config_entry.data, **config_entry.options})
        )
        self._topology: dict[str, DeviceTopology] = {}
        self._source_to_device: dict[str, str] = {}
        self._subscription_manager = SubscriptionManager(hass)
        self._unsub_periodic_rescan: Callable[[], None] | None = None

    async def async_shutdown(self) -> None:
        """Tear down listeners."""
        await self._subscription_manager.shutdown()

        if self._unsub_periodic_rescan is not None:
            self._unsub_periodic_rescan()
            self._unsub_periodic_rescan = None

    async def _async_setup(self) -> None:
        """Set up the push-style coordinator and the slow topology rescan timer."""
        self._unsub_periodic_rescan = async_track_time_interval(
            self.hass,
            self._async_handle_periodic_rescan,
            self._scan_interval,
        )

    async def _async_update_data(self) -> dict[str, DeviceSnapshot]:
        """Discover source devices and compute their current sensor values."""
        if not self._entity_plan_service.enabled_kinds():
            self._topology = {}
            self._source_to_device = {}
            self._refresh_state_listener()
            return {}

        topology = self._topology_discovery_service.discover()
        snapshots = {
            device_id: self._snapshot_builder.build_snapshot(
                device_topology,
                self._effective_policy_for_topology(device_topology).leaf_offset_c,
            )
            for device_id, device_topology in topology.items()
        }

        self._topology = topology
        self._source_to_device = {
            entity_id: device_id
            for device_id, device_topology in topology.items()
            for entity_id in (
                device_topology.temperature_entity_id,
                device_topology.humidity_entity_id,
            )
        }
        self._refresh_state_listener()
        return snapshots

    async def _async_handle_periodic_rescan(self, _: datetime) -> None:
        """Rescan Home Assistant devices at a slow interval."""
        await self.async_request_refresh()

    @callback
    def async_note_context_change(self) -> None:
        """Refresh source subscriptions after entities were added or removed."""
        self._refresh_state_listener()

    @callback
    def creatable_kinds_for_device(self, device_id: str) -> set[str]:
        """Return enabled sensor kinds that are not already present on the device."""
        device_topology = self._topology.get(device_id)
        if device_topology is None:
            return set()

        return self._entity_plan_service.creatable_kinds_for_topology(
            device_topology,
            self._effective_policy_for_topology(device_topology),
        )

    @callback
    def diagnostics_payload(self) -> dict[str, object]:
        """Return a sanitized diagnostics payload for the whole config entry."""
        return {
            "options": asdict(self.options),
            "tracked_entity_ids": sorted(self._subscription_manager.tracked_entity_ids),
            "topology": {
                device_id: asdict(topology)
                for device_id, topology in self._topology.items()
            },
            "snapshots": {
                device_id: asdict(snapshot)
                for device_id, snapshot in (self.data or {}).items()
            },
        }

    @callback
    def device_diagnostics_payload(self, device_id: str) -> dict[str, object]:
        """Return a diagnostics payload scoped to a single Home Assistant device."""
        return {
            "device_id": device_id,
            "creatable_kinds": sorted(self.creatable_kinds_for_device(device_id)),
            "topology": asdict(self._topology[device_id])
            if device_id in self._topology
            else None,
            "snapshot": asdict(self.data[device_id])
            if self.data and device_id in self.data
            else None,
        }

    @callback
    def _refresh_state_listener(self) -> None:
        """Track source state changes only for entities used by active listeners."""
        self._subscription_manager.refresh(
            active_device_ids=set(self.async_contexts()),
            topology_by_device_id=self._topology,
            handler=self._async_handle_source_state_changed,
        )

    async def _async_handle_source_state_changed(
        self, event: Event[EventStateChangedData]
    ) -> None:
        """Update only the device affected by one source sensor state change."""
        entity_id = event.data.get("entity_id")
        if not isinstance(entity_id, str):
            return

        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        if old_state == new_state:
            return

        device_id = self._source_to_device.get(entity_id)
        if device_id is None:
            return

        device_topology = self._topology.get(device_id)
        if device_topology is None:
            return

        current_data = self.data or {}
        next_snapshot = self._snapshot_builder.build_snapshot(
            device_topology,
            self._effective_policy_for_topology(device_topology).leaf_offset_c,
        )
        if current_data.get(device_id) == next_snapshot:
            return

        next_data = dict(current_data)
        next_data[device_id] = next_snapshot
        self.async_set_updated_data(next_data)

    def _effective_policy_for_topology(self, topology: DeviceTopology):
        """Resolve active runtime policy for one topology device."""
        return self._policy_resolver.resolve_for_device(
            device_id=topology.device_id,
            area_id=topology.area_id,
            apply_device_overrides=False,
        )
