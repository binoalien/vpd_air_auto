"""Sensor platform for VPD Air Auto."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import VpdAirConfigEntry
from .const import (
    DOMAIN,
    SENSOR_KIND_ABSOLUTE_HUMIDITY,
    SENSOR_KIND_AIR,
    SENSOR_KIND_DEW_POINT,
    SENSOR_KIND_LEAF,
    UNIQUE_ID_SUFFIX_ABSOLUTE_HUMIDITY,
    UNIQUE_ID_SUFFIX_AIR,
    UNIQUE_ID_SUFFIX_DEW_POINT,
    UNIQUE_ID_SUFFIX_LEAF,
    UNIT_GM3,
    UNIT_KPA,
    UNRECORDED_ATTRIBUTE_HUMIDITY_ENTITY_ID,
    UNRECORDED_ATTRIBUTE_LEAF_TEMPERATURE_OFFSET_C,
    UNRECORDED_ATTRIBUTE_TEMPERATURE_ENTITY_ID,
    device_id_from_unique_id,
    make_absolute_humidity_unique_id,
    make_dew_point_unique_id,
    make_vpdair_unique_id,
    make_vpdleaf_unique_id,
)
from .coordinator import VpdAirCoordinator
from .models import DeviceSnapshot

PARALLEL_UPDATES = 0


def _registry_entry_kind(unique_id: str) -> str | None:
    """Determine the sensor kind from a registry unique ID."""
    if unique_id.endswith(f"_{UNIQUE_ID_SUFFIX_AIR}"):
        return SENSOR_KIND_AIR
    if unique_id.endswith(f"_{UNIQUE_ID_SUFFIX_LEAF}"):
        return SENSOR_KIND_LEAF
    if unique_id.endswith(f"_{UNIQUE_ID_SUFFIX_ABSOLUTE_HUMIDITY}"):
        return SENSOR_KIND_ABSOLUTE_HUMIDITY
    if unique_id.endswith(f"_{UNIQUE_ID_SUFFIX_DEW_POINT}"):
        return SENSOR_KIND_DEW_POINT
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VpdAirConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data
    entity_registry = er.async_get(hass)
    known_entities: set[tuple[str, str]] = set()

    @callback
    def _remove_stale_registry_entities(current_entities: set[tuple[str, str]]) -> None:
        for registry_entry in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
            if registry_entry.domain != "sensor" or registry_entry.platform != DOMAIN:
                continue

            device_id = device_id_from_unique_id(registry_entry.unique_id)
            kind = _registry_entry_kind(registry_entry.unique_id)
            entity_key = (device_id, kind) if device_id is not None and kind is not None else None
            if entity_key is not None and entity_key in current_entities:
                continue

            entity_registry.async_remove(registry_entry.entity_id)

    @callback
    def _sync_entities() -> None:
        current_entities = {
            (device_id, kind)
            for device_id in (coordinator.data or {})
            for kind in coordinator.creatable_kinds_for_device(device_id)
        }
        _remove_stale_registry_entities(current_entities)

        removed_entities = known_entities - current_entities
        if removed_entities:
            known_entities.difference_update(removed_entities)

        new_entity_keys = current_entities - known_entities
        if not new_entity_keys:
            return

        async_add_entities(
            [DerivedValueSensor(hass, coordinator, device_id, kind) for device_id, kind in sorted(new_entity_keys)]
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
        kind: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, context=device_id)
        self._device_id = device_id
        self._kind = kind
        self._attr_unique_id = self._build_unique_id(device_id, kind)
        self.device_entry = dr.async_get(hass).async_get(device_id)

    @staticmethod
    def _build_unique_id(device_id: str, kind: str) -> str:
        if kind == SENSOR_KIND_AIR:
            return make_vpdair_unique_id(device_id)
        if kind == SENSOR_KIND_LEAF:
            return make_vpdleaf_unique_id(device_id)
        if kind == SENSOR_KIND_ABSOLUTE_HUMIDITY:
            return make_absolute_humidity_unique_id(device_id)
        return make_dew_point_unique_id(device_id)

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
        if self._kind == SENSOR_KIND_LEAF:
            return self.coordinator.options.leaf_display_name
        if self._kind == SENSOR_KIND_ABSOLUTE_HUMIDITY:
            return self.coordinator.options.absolute_humidity_display_name
        if self._kind == SENSOR_KIND_DEW_POINT:
            return self.coordinator.options.dew_point_display_name
        return self.coordinator.options.display_name

    @property
    def icon(self) -> str:
        """Return the globally configured icon for this sensor kind."""
        if self._kind == SENSOR_KIND_LEAF:
            return self.coordinator.options.leaf_icon
        if self._kind == SENSOR_KIND_ABSOLUTE_HUMIDITY:
            return self.coordinator.options.absolute_humidity_icon
        if self._kind == SENSOR_KIND_DEW_POINT:
            return self.coordinator.options.dew_point_icon
        return self.coordinator.options.icon

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the Home Assistant device class for the sensor kind."""
        if self._kind == SENSOR_KIND_ABSOLUTE_HUMIDITY:
            return SensorDeviceClass.ABSOLUTE_HUMIDITY
        if self._kind == SENSOR_KIND_DEW_POINT:
            return SensorDeviceClass.TEMPERATURE
        return None

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the native unit for this sensor kind."""
        if self._kind == SENSOR_KIND_ABSOLUTE_HUMIDITY:
            return UNIT_GM3
        if self._kind == SENSOR_KIND_DEW_POINT:
            return UnitOfTemperature.CELSIUS
        return UNIT_KPA

    @property
    def available(self) -> bool:
        """Return true if the value can currently be computed."""
        snapshot = self._snapshot
        if snapshot is None:
            return False
        if self._kind == SENSOR_KIND_LEAF:
            return snapshot.vpd_leaf_kpa is not None
        if self._kind == SENSOR_KIND_ABSOLUTE_HUMIDITY:
            return snapshot.absolute_humidity_gm3 is not None
        if self._kind == SENSOR_KIND_DEW_POINT:
            return snapshot.dew_point_c is not None
        return snapshot.vpd_air_kpa is not None

    @property
    def native_value(self) -> float | None:
        """Return the current derived value."""
        snapshot = self._snapshot
        if snapshot is None:
            return None
        if self._kind == SENSOR_KIND_LEAF:
            return snapshot.vpd_leaf_kpa
        if self._kind == SENSOR_KIND_ABSOLUTE_HUMIDITY:
            return snapshot.absolute_humidity_gm3
        if self._kind == SENSOR_KIND_DEW_POINT:
            return snapshot.dew_point_c
        return snapshot.vpd_air_kpa

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
        if self._kind == SENSOR_KIND_LEAF:
            attributes[UNRECORDED_ATTRIBUTE_LEAF_TEMPERATURE_OFFSET_C] = snapshot.leaf_offset_c
        return attributes

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
