"""Topology discovery service for VPD Air Auto."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from ..calculations import coerce_humidity_pct, coerce_temperature_c
from ..const import DOMAIN, SOURCE_DOMAIN_SENSOR
from ..models import DeviceTopology
from .duplicates import DuplicateDetectionService
from .selection import (
    TARGET_HUMIDITY,
    TARGET_TEMPERATURE,
    SourceCandidate,
    choose_best_entity_id,
    normalize_identifier,
)


class TopologyDiscoveryService:  # pylint: disable=too-few-public-methods
    """Discover device source topology from Home Assistant registries."""

    def __init__(
        self,
        hass: HomeAssistant,
        duplicate_detection_service: DuplicateDetectionService,
    ) -> None:
        """Initialize topology discovery service."""
        self._hass = hass
        self._duplicate_detection_service = duplicate_detection_service

    def discover(self) -> dict[str, DeviceTopology]:
        """Build the source-entity topology for all matching Home Assistant devices."""
        entity_registry = er.async_get(self._hass)
        device_registry = dr.async_get(self._hass)

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

            blocked_sensor_kinds = self._duplicate_detection_service.detect_existing_derived_sensor_kinds(
                candidates
            )
            topology[device.id] = DeviceTopology(
                device_id=device.id,
                device_name=device.name_by_user or device.name or device.id,
                temperature_entity_id=temperature_entity_id,
                humidity_entity_id=humidity_entity_id,
                blocked_sensor_kinds=blocked_sensor_kinds,
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

    def _normalized_entry_identifiers(self, entry: er.RegistryEntry) -> set[str]:
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
        state = self._hass.states.get(entity_id)
        if state is None:
            return None
        friendly_name = state.attributes.get("friendly_name")
        return friendly_name if isinstance(friendly_name, str) else None

    def _entry_device_class(self, entry: er.RegistryEntry) -> str | None:
        state = self._hass.states.get(entry.entity_id)
        if state is not None:
            device_class = state.attributes.get("device_class")
            if isinstance(device_class, str):
                return device_class

        original_device_class = getattr(entry, "original_device_class", None)
        if isinstance(original_device_class, str):
            return original_device_class
        return None

    def _entry_unit_of_measurement(self, entry: er.RegistryEntry) -> str | None:
        state = self._hass.states.get(entry.entity_id)
        if state is not None:
            unit = state.attributes.get("unit_of_measurement")
            if isinstance(unit, str):
                return unit

        original_unit = getattr(entry, "original_unit_of_measurement", None)
        if isinstance(original_unit, str):
            return original_unit
        return None

    @staticmethod
    def _entry_entity_category(entry: er.RegistryEntry) -> str | None:
        entity_category = getattr(entry, "entity_category", None)
        if entity_category is None:
            return None
        return str(entity_category)

    def _entry_value_valid(
        self, entry: er.RegistryEntry, target_device_class: str
    ) -> bool:
        state = self._hass.states.get(entry.entity_id)
        if target_device_class == TARGET_TEMPERATURE:
            return coerce_temperature_c(state) is not None
        return coerce_humidity_pct(state) is not None
