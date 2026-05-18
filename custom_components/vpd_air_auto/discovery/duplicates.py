"""Duplicate detection service for derived VPD helper sensors."""

from __future__ import annotations

from homeassistant.helpers import entity_registry as er

from ..const import (
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
from .selection import normalize_identifier

_ABSOLUTE_HUMIDITY_DEVICE_CLASS = "absolute_humidity"


class DuplicateDetectionService:
    """Detect foreign duplicate sensors for one device."""

    def __init__(self, hass, options: IntegrationOptions) -> None:
        """Initialize duplicate detection dependencies."""
        self.hass = hass
        self.options = options

    def detect_existing_derived_sensor_kinds(
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
