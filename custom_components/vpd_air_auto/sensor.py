"""Sensor platform for VPD Air Auto."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import VpdAirConfigEntry
from .const import (
    UNRECORDED_ATTRIBUTE_HUMIDITY_ENTITY_ID,
    UNRECORDED_ATTRIBUTE_LEAF_TEMPERATURE_OFFSET_C,
    UNRECORDED_ATTRIBUTE_TEMPERATURE_ENTITY_ID,
    make_absolute_humidity_unique_id,
    make_dew_point_unique_id,
    make_vpdair_unique_id,
    make_vpdleaf_unique_id,
)
from .coordinator import VpdAirCoordinator
from .domain.enums import SensorKind
from .domain.sensor_definitions import get_sensor_definition
from .models import DeviceSnapshot

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VpdAirConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data
    known_entities: set[tuple[str, SensorKind]] = set()

    @callback
    def _sync_entities() -> None:
        current_entities = {
            (device_id, SensorKind(kind))
            for device_id in (coordinator.data or {})
            for kind in coordinator.creatable_kinds_for_device(device_id)
        }
        removed_entities = known_entities - current_entities
        if removed_entities:
            known_entities.difference_update(removed_entities)

        new_entity_keys = current_entities - known_entities
        if not new_entity_keys:
            return

        async_add_entities(
            [
                DerivedValueSensor(hass, coordinator, device_id, kind)
                for device_id, kind in sorted(new_entity_keys)
            ]
        )
        known_entities.update(new_entity_keys)

    _sync_entities()
    entry.async_on_unload(coordinator.async_add_listener(_sync_entities))


class DerivedValueSensor(CoordinatorEntity[VpdAirCoordinator], SensorEntity):
    """Derived sensor linked to an existing Home Assistant device."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2
    _unrecorded_attributes = frozenset(
        {
            UNRECORDED_ATTRIBUTE_TEMPERATURE_ENTITY_ID,
            UNRECORDED_ATTRIBUTE_HUMIDITY_ENTITY_ID,
            UNRECORDED_ATTRIBUTE_LEAF_TEMPERATURE_OFFSET_C,
        }
    )

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: VpdAirCoordinator,
        device_id: str,
        kind: SensorKind | str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, context=device_id)
        self._device_id = device_id
        self._kind = SensorKind(kind)
        self._definition = get_sensor_definition(self._kind)
        self._attr_unique_id = self._build_unique_id(device_id, self._kind)
        self.device_entry = dr.async_get(hass).async_get(device_id)

    @staticmethod
    def _build_unique_id(device_id: str, kind: SensorKind) -> str:
        if kind is SensorKind.AIR:
            return make_vpdair_unique_id(device_id)
        if kind is SensorKind.LEAF:
            return make_vpdleaf_unique_id(device_id)
        if kind is SensorKind.ABSOLUTE_HUMIDITY:
            return make_absolute_humidity_unique_id(device_id)
        if kind is SensorKind.DEW_POINT:
            return make_dew_point_unique_id(device_id)
        raise ValueError(f"Unsupported sensor kind: {kind!r}")

    @property
    def _snapshot(self) -> DeviceSnapshot | None:
        """Return the current coordinator snapshot for this device."""
        return (self.coordinator.data or {}).get(self._device_id)

    async def async_added_to_hass(self) -> None:
        """Register the entity with the coordinator context tracking."""
        await super().async_added_to_hass()
        self.coordinator.async_note_context_change()

    async def async_will_remove_from_hass(self) -> None:
        """Unregister the entity from the coordinator context tracking."""
        await super().async_will_remove_from_hass()
        self.coordinator.async_note_context_change()

    @property
    def name(self) -> str:
        """Return the configured display name for this sensor."""
        if self._kind is SensorKind.LEAF:
            return self.coordinator.options.leaf_display_name
        if self._kind is SensorKind.ABSOLUTE_HUMIDITY:
            return self.coordinator.options.absolute_humidity_display_name
        if self._kind is SensorKind.DEW_POINT:
            return self.coordinator.options.dew_point_display_name
        return self.coordinator.options.display_name

    @property
    def icon(self) -> str:
        """Return the globally configured icon for this sensor kind."""
        if self._kind is SensorKind.LEAF:
            return self.coordinator.options.leaf_icon
        if self._kind is SensorKind.ABSOLUTE_HUMIDITY:
            return self.coordinator.options.absolute_humidity_icon
        if self._kind is SensorKind.DEW_POINT:
            return self.coordinator.options.dew_point_icon
        return self.coordinator.options.icon

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the Home Assistant device class for the sensor kind."""
        return self._definition.device_class

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the native unit for this sensor kind."""
        return self._definition.native_unit_of_measurement

    @property
    def available(self) -> bool:
        """Return true if the value can currently be computed."""
        snapshot = self._snapshot
        if snapshot is None:
            return False
        return self._definition.snapshot_value_getter(snapshot) is not None

    @property
    def native_value(self) -> float | None:
        """Return the current derived value."""
        snapshot = self._snapshot
        if snapshot is None:
            return None
        return self._definition.snapshot_value_getter(snapshot)

    @property
    def extra_state_attributes(self) -> dict[str, str | float]:
        """Expose the source entities used for the current calculation."""
        snapshot = self._snapshot
        if snapshot is None:
            return {}

        attributes: dict[str, str | float] = {
            UNRECORDED_ATTRIBUTE_TEMPERATURE_ENTITY_ID: snapshot.temperature_entity_id,
            UNRECORDED_ATTRIBUTE_HUMIDITY_ENTITY_ID: snapshot.humidity_entity_id,
        }
        if self._definition.include_leaf_offset_attribute:
            attributes[UNRECORDED_ATTRIBUTE_LEAF_TEMPERATURE_OFFSET_C] = (
                snapshot.leaf_offset_c
            )
        return attributes

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
