"""Coordinator for VPD Air Auto."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    EventStateChangedData,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .calculations import (
    calculate_absolute_humidity_gm3,
    calculate_dew_point_c,
    calculate_leaf_temperature_c,
    calculate_vpd_air_kpa,
    calculate_vpd_leaf_kpa,
    coerce_humidity_pct,
    coerce_temperature_c,
)
from .const import (
    DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
    DEFAULT_DEW_POINT_DISPLAY_NAME,
    DEFAULT_DISPLAY_NAME,
    DEFAULT_LEAF_DISPLAY_NAME,
    DOMAIN,
    SENSOR_KIND_ABSOLUTE_HUMIDITY,
    SENSOR_KIND_AIR,
    SENSOR_KIND_DEW_POINT,
    SENSOR_KIND_LEAF,
    SOURCE_DOMAIN_SENSOR,
    IntegrationOptions,
)
from .models import DeviceSnapshot, DeviceTopology
from .selection import (
    TARGET_HUMIDITY,
    TARGET_TEMPERATURE,
    SourceCandidate,
    choose_best_entity_id,
    normalize_identifier,
)

_LOGGER = logging.getLogger(__name__)

_ABSOLUTE_HUMIDITY_DEVICE_CLASS = "absolute_humidity"


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

        topology = self._discover_topology()
        snapshots = {
            device_id: self._build_snapshot_for_topology(device_topology)
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
        next_snapshot = self._build_snapshot_for_topology(device_topology)
        if current_data.get(device_id) == next_snapshot:
            return

        next_data = dict(current_data)
        next_data[device_id] = next_snapshot
        self.async_set_updated_data(next_data)

    @callback
    def _discover_topology(self) -> dict[str, DeviceTopology]:
        """Build the source-entity topology for all matching Home Assistant devices."""
        entity_registry = er.async_get(self.hass)
        device_registry = dr.async_get(self.hass)

        topology: dict[str, DeviceTopology] = {}

        for device in device_registry.devices.values():
            candidates = list(
                er.async_entries_for_device(
                    entity_registry,
                    device.id,
                    include_disabled_entities=False,
                )
            )

            temperature_entity_id = self._pick_best_entity(
                candidates, target_device_class=TARGET_TEMPERATURE
            )
            humidity_entity_id = self._pick_best_entity(
                candidates, target_device_class=TARGET_HUMIDITY
            )

            if temperature_entity_id is None or humidity_entity_id is None:
                continue

            topology[device.id] = DeviceTopology(
                device_id=device.id,
                device_name=device.name_by_user or device.name or device.id,
                temperature_entity_id=temperature_entity_id,
                humidity_entity_id=humidity_entity_id,
                blocked_sensor_kinds=self._detect_existing_derived_sensor_kinds(
                    candidates
                ),
            )

        return topology

    def _pick_best_entity(
        self,
        candidates: list[er.RegistryEntry],
        target_device_class: str,
    ) -> str | None:
        """Pick the most likely source entity of the requested device class."""
        normalized_candidates: list[SourceCandidate] = []

        for entry in candidates:
            if entry.domain != SOURCE_DOMAIN_SENSOR:
                continue
            if entry.platform == DOMAIN:
                continue
            if self._entry_device_class(entry) != target_device_class:
                continue

            normalized_candidates.append(
                SourceCandidate(
                    entity_id=entry.entity_id,
                    device_class=target_device_class,
                    unit_of_measurement=self._entry_unit_of_measurement(entry),
                    entity_category=self._entry_entity_category(entry),
                    value_valid=self._entry_value_valid(entry, target_device_class),
                    normalized_identifiers=frozenset(
                        self._normalized_entry_identifiers(entry)
                    ),
                )
            )

        return choose_best_entity_id(normalized_candidates, target_device_class)

    def _detect_existing_derived_sensor_kinds(
        self, candidates: list[er.RegistryEntry]
    ) -> frozenset[str]:
        """Detect foreign sensors on same device that would duplicate our helpers."""
        blocked: set[str] = set()

        for entry in candidates:
            if entry.domain != SOURCE_DOMAIN_SENSOR:
                continue
            if entry.platform == DOMAIN:
                continue

            detected_kind = self._detect_existing_derived_sensor_kind(entry)
            if detected_kind is not None:
                blocked.add(detected_kind)

        return frozenset(blocked)

    def _detect_existing_derived_sensor_kind(
        self, entry: er.RegistryEntry
    ) -> str | None:
        """Classify a foreign sensor as our derived helper kinds when possible."""
        entry_device_class = self._entry_device_class(entry)
        if entry_device_class == _ABSOLUTE_HUMIDITY_DEVICE_CLASS:
            return SENSOR_KIND_ABSOLUTE_HUMIDITY

        identifiers = self._normalized_entry_identifiers(entry)
        if identifiers & self._air_duplicate_aliases:
            return SENSOR_KIND_AIR
        if identifiers & self._leaf_duplicate_aliases:
            return SENSOR_KIND_LEAF
        if identifiers & self._absolute_humidity_duplicate_aliases:
            return SENSOR_KIND_ABSOLUTE_HUMIDITY
        if identifiers & self._dew_point_duplicate_aliases:
            return SENSOR_KIND_DEW_POINT
        return None

    @property
    def _air_duplicate_aliases(self) -> set[str]:
        return {
            normalize_identifier(DEFAULT_DISPLAY_NAME),
            normalize_identifier(self.options.display_name),
            "vpd",
            "vpdair",
            "airvpd",
            "vaporpressuredeficit",
            "vapourpressuredeficit",
            "vaporpressuredeficitair",
            "vapourpressuredeficitair",
        }

    @property
    def _leaf_duplicate_aliases(self) -> set[str]:
        return {
            normalize_identifier(DEFAULT_LEAF_DISPLAY_NAME),
            normalize_identifier(self.options.leaf_display_name),
            "leafvpd",
            "vpdleaf",
            "canopyvpd",
            "vaporpressuredeficitleaf",
            "vapourpressuredeficitleaf",
        }

    @property
    def _absolute_humidity_duplicate_aliases(self) -> set[str]:
        return {
            normalize_identifier(DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME),
            normalize_identifier(self.options.absolute_humidity_display_name),
            "absolutehumidity",
            "abshumidity",
        }

    @property
    def _dew_point_duplicate_aliases(self) -> set[str]:
        return {
            normalize_identifier(DEFAULT_DEW_POINT_DISPLAY_NAME),
            normalize_identifier(self.options.dew_point_display_name),
            "dewpoint",
            "dewpt",
            "dewpointtemperature",
        }

    def _normalized_entry_identifiers(self, entry: er.RegistryEntry) -> set[str]:
        """Collect normalized names and IDs for one registry entry."""
        identifiers = {normalize_identifier(entry.entity_id.split(".", 1)[1])}
        for value in (
            getattr(entry, "name", None),
            getattr(entry, "original_name", None),
            self._state_friendly_name(entry.entity_id),
        ):
            normalized = normalize_identifier(value)
            if normalized:
                identifiers.add(normalized)
        return identifiers

    def _state_friendly_name(self, entity_id: str) -> str | None:
        """Return the current friendly_name for one entity if available."""
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        friendly_name = state.attributes.get("friendly_name")
        return friendly_name if isinstance(friendly_name, str) else None

    def _entry_device_class(self, entry: er.RegistryEntry) -> str | None:
        """Resolve device class for source entity from state first, then registry."""
        state = self.hass.states.get(entry.entity_id)
        if state is not None:
            device_class = state.attributes.get("device_class")
            if isinstance(device_class, str):
                return device_class

        original_device_class = getattr(entry, "original_device_class", None)
        if isinstance(original_device_class, str):
            return original_device_class
        return None

    def _entry_unit_of_measurement(self, entry: er.RegistryEntry) -> str | None:
        """Resolve the current or original unit of measurement for one entity."""
        state = self.hass.states.get(entry.entity_id)
        if state is not None:
            unit = state.attributes.get("unit_of_measurement")
            if isinstance(unit, str):
                return unit

        original_unit = getattr(entry, "original_unit_of_measurement", None)
        if isinstance(original_unit, str):
            return original_unit
        return None

    def _entry_entity_category(self, entry: er.RegistryEntry) -> str | None:
        """Return the registry entity_category value as a string when present."""
        entity_category = getattr(entry, "entity_category", None)
        if entity_category is None:
            return None
        return str(entity_category)

    def _entry_value_valid(
        self, entry: er.RegistryEntry, target_device_class: str
    ) -> bool:
        """Return true when the current state can be parsed for the target kind."""
        state = self.hass.states.get(entry.entity_id)
        if target_device_class == TARGET_TEMPERATURE:
            return coerce_temperature_c(state) is not None
        return coerce_humidity_pct(state) is not None

    def _build_snapshot_for_topology(
        self, device_topology: DeviceTopology
    ) -> DeviceSnapshot:
        """Build the current snapshot for one Home Assistant device."""
        temp_state = self.hass.states.get(device_topology.temperature_entity_id)
        humidity_state = self.hass.states.get(device_topology.humidity_entity_id)

        temperature_c = coerce_temperature_c(temp_state)
        humidity_pct = coerce_humidity_pct(humidity_state)
        leaf_temperature_c = calculate_leaf_temperature_c(
            temperature_c, self.options.leaf_offset_c
        )
        dew_point_c = calculate_dew_point_c(temperature_c, humidity_pct)
        vpd_air_kpa = calculate_vpd_air_kpa(temperature_c, humidity_pct)
        vpd_leaf_kpa = calculate_vpd_leaf_kpa(
            temperature_c, humidity_pct, leaf_temperature_c
        )
        absolute_humidity_gm3 = calculate_absolute_humidity_gm3(
            temperature_c, humidity_pct
        )

        return DeviceSnapshot(
            device_id=device_topology.device_id,
            device_name=device_topology.device_name,
            temperature_entity_id=device_topology.temperature_entity_id,
            humidity_entity_id=device_topology.humidity_entity_id,
            temperature_c=temperature_c,
            humidity_pct=humidity_pct,
            leaf_offset_c=self.options.leaf_offset_c,
            leaf_temperature_c=leaf_temperature_c,
            dew_point_c=dew_point_c,
            vpd_air_kpa=vpd_air_kpa,
            vpd_leaf_kpa=vpd_leaf_kpa,
            absolute_humidity_gm3=absolute_humidity_gm3,
        )
