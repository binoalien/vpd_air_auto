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
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    SENSOR_KIND_ABSOLUTE_HUMIDITY,
    SENSOR_KIND_AIR,
    SENSOR_KIND_DEW_POINT,
    SENSOR_KIND_LEAF,
    IntegrationOptions,
)
from .discovery.duplicates import DuplicateDetectionService
from .discovery.topology import TopologyDiscoveryService
from .models import DeviceSnapshot, DeviceTopology
from .services.snapshot_builder import SnapshotBuilder

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
        self._snapshot_builder = SnapshotBuilder(hass, options.leaf_offset_c)
        self._duplicate_detection_service = DuplicateDetectionService(hass, options)
        self._topology_discovery_service = TopologyDiscoveryService(
            hass, self._duplicate_detection_service
        )
        self._topology: dict[str, DeviceTopology] = {}
        self._source_to_device: dict[str, str] = {}
        self._tracked_entity_ids: set[str] = set()
        self._unsub_state_listener: Callable[[], None] | None = None
        self._unsub_periodic_rescan: Callable[[], None] | None = None

    async def async_shutdown(self) -> None:
        """Tear down listeners."""
        if self._unsub_state_listener is not None:
            self._unsub_state_listener()
            self._unsub_state_listener = None

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
        if not (
            self.options.enable_air
            or self.options.enable_leaf
            or self.options.enable_absolute_humidity
            or self.options.enable_dew_point
        ):
            self._topology = {}
            self._source_to_device = {}
            self._refresh_state_listener()
            return {}

        topology = self._topology_discovery_service.discover()
        snapshots = {
            device_id: self._snapshot_builder.build_snapshot(device_topology)
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

        enabled: set[str] = set()
        if self.options.enable_air:
            enabled.add(SENSOR_KIND_AIR)
        if self.options.enable_leaf:
            enabled.add(SENSOR_KIND_LEAF)
        if self.options.enable_absolute_humidity:
            enabled.add(SENSOR_KIND_ABSOLUTE_HUMIDITY)
        if self.options.enable_dew_point:
            enabled.add(SENSOR_KIND_DEW_POINT)

        return enabled.difference(device_topology.blocked_sensor_kinds)

    @callback
    def diagnostics_payload(self) -> dict[str, object]:
        """Return a sanitized diagnostics payload for the whole config entry."""
        return {
            "options": asdict(self.options),
            "tracked_entity_ids": sorted(self._tracked_entity_ids),
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
        tracked_entity_ids = {
            entity_id
            for device_id in self.async_contexts()
            for topology in [self._topology.get(device_id)]
            if topology is not None
            for entity_id in (
                topology.temperature_entity_id,
                topology.humidity_entity_id,
            )
        }

        if tracked_entity_ids == self._tracked_entity_ids:
            return

        if self._unsub_state_listener is not None:
            self._unsub_state_listener()
            self._unsub_state_listener = None

        self._tracked_entity_ids = tracked_entity_ids
        if not tracked_entity_ids:
            return

        self._unsub_state_listener = async_track_state_change_event(
            self.hass,
            tracked_entity_ids,
            self._async_handle_source_state_changed,
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
        next_snapshot = self._snapshot_builder.build_snapshot(device_topology)
        if current_data.get(device_id) == next_snapshot:
            return

        next_data = dict(current_data)
        next_data[device_id] = next_snapshot
        self.async_set_updated_data(next_data)

