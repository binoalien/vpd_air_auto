"""Build device snapshots from source entities and options."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from ..calculations import (
    calculate_absolute_humidity_gm3,
    calculate_dew_point_c,
    calculate_leaf_temperature_c,
    calculate_vpd_air_kpa,
    calculate_vpd_leaf_kpa,
    coerce_humidity_pct,
    coerce_temperature_c,
)
from ..const import IntegrationOptions
from ..models import DeviceSnapshot, DeviceTopology


class SnapshotBuilder:
    """Build current snapshots for discovered device topologies."""

    def __init__(self, hass: HomeAssistant, options: IntegrationOptions) -> None:
        """Store Home Assistant state access and integration options."""
        self._hass = hass
        self._options = options

    def build(self, device_topology: DeviceTopology) -> DeviceSnapshot:
        """Build the current snapshot for one Home Assistant device."""
        temp_state = self._hass.states.get(device_topology.temperature_entity_id)
        humidity_state = self._hass.states.get(device_topology.humidity_entity_id)

        temperature_c = coerce_temperature_c(temp_state)
        humidity_pct = coerce_humidity_pct(humidity_state)
        leaf_temperature_c = calculate_leaf_temperature_c(
            temperature_c, self._options.leaf_offset_c
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
            leaf_offset_c=self._options.leaf_offset_c,
            leaf_temperature_c=leaf_temperature_c,
            dew_point_c=dew_point_c,
            vpd_air_kpa=vpd_air_kpa,
            vpd_leaf_kpa=vpd_leaf_kpa,
            absolute_humidity_gm3=absolute_humidity_gm3,
        )
