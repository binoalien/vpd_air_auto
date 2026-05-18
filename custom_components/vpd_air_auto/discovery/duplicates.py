"""Duplicate-detection helpers for VPD Air Auto discovery."""

from __future__ import annotations

from collections.abc import Callable

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
    """Detect foreign sensors that duplicate derived helper sensors."""

    def __init__(self, options: IntegrationOptions) -> None:
        """Initialize duplicate detection service."""
        self._options = options

    def detect_existing_derived_sensor_kinds(
        self,
        candidates: list[er.RegistryEntry],
        state_friendly_name_getter: Callable[[str], str | None],
        entry_device_class_getter: Callable[[er.RegistryEntry], str | None],
    ) -> frozenset[str]:
        """Detect foreign sensors on same device that would duplicate our helpers."""
        blocked: set[str] = set()

        for entry in candidates:
            if entry.domain != SOURCE_DOMAIN_SENSOR:
                continue
            if entry.platform == DOMAIN:
                continue

            detected_kind = self._detect_existing_derived_sensor_kind(
                entry,
                state_friendly_name_getter,
                entry_device_class_getter,
            )
            if detected_kind is not None:
                blocked.add(detected_kind)

        return frozenset(blocked)

    def _detect_existing_derived_sensor_kind(
        self,
        entry: er.RegistryEntry,
        state_friendly_name_getter: Callable[[str], str | None],
        entry_device_class_getter: Callable[[er.RegistryEntry], str | None],
    ) -> str | None:
        """Classify a foreign sensor as our derived helper kinds when possible."""
        entry_device_class = entry_device_class_getter(entry)
        if entry_device_class == _ABSOLUTE_HUMIDITY_DEVICE_CLASS:
            return SENSOR_KIND_ABSOLUTE_HUMIDITY

        identifiers = self._normalized_entry_identifiers(
            entry, state_friendly_name_getter
        )
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
            normalize_identifier(self._options.display_name),
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
            normalize_identifier(self._options.leaf_display_name),
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
            normalize_identifier(self._options.absolute_humidity_display_name),
            "absolutehumidity",
            "abshumidity",
        }

    @property
    def _dew_point_duplicate_aliases(self) -> set[str]:
        return {
            normalize_identifier(DEFAULT_DEW_POINT_DISPLAY_NAME),
            normalize_identifier(self._options.dew_point_display_name),
            "dewpoint",
            "dewpt",
            "dewpointtemperature",
        }

    def _normalized_entry_identifiers(
        self,
        entry: er.RegistryEntry,
        state_friendly_name_getter: Callable[[str], str | None],
    ) -> set[str]:
        """Collect normalized names and IDs for one registry entry."""
        identifiers = {normalize_identifier(entry.entity_id.split(".", 1)[1])}
        for value in (
            getattr(entry, "name", None),
            getattr(entry, "original_name", None),
            state_friendly_name_getter(entry.entity_id),
        ):
            normalized = normalize_identifier(value)
            if normalized:
                identifiers.add(normalized)
        return identifiers
