"""Declarative definitions for derived sensor kinds."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTemperature

from ..const import (
    DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
    DEFAULT_ABSOLUTE_HUMIDITY_ICON,
    DEFAULT_DEW_POINT_DISPLAY_NAME,
    DEFAULT_DEW_POINT_ICON,
    DEFAULT_DISPLAY_NAME,
    DEFAULT_ICON,
    DEFAULT_LEAF_DISPLAY_NAME,
    DEFAULT_LEAF_ICON,
    UNIQUE_ID_SUFFIX_ABSOLUTE_HUMIDITY,
    UNIQUE_ID_SUFFIX_AIR,
    UNIQUE_ID_SUFFIX_DEW_POINT,
    UNIQUE_ID_SUFFIX_LEAF,
    UNIT_GM3,
    UNIT_KPA,
)
from ..models import DeviceSnapshot
from .enums import SensorKind


@dataclass(frozen=True, slots=True)
class SensorDefinition:
    """Declarative metadata and accessors for a derived sensor kind."""

    kind: SensorKind
    unique_id_suffix: str
    default_name: str
    default_icon: str
    native_unit_of_measurement: str
    device_class: SensorDeviceClass | None
    snapshot_getter: Callable[[DeviceSnapshot], float | None]


def _get_air_value(snapshot: DeviceSnapshot) -> float | None:
    return snapshot.vpd_air_kpa


def _get_leaf_value(snapshot: DeviceSnapshot) -> float | None:
    return snapshot.vpd_leaf_kpa


def _get_absolute_humidity_value(snapshot: DeviceSnapshot) -> float | None:
    return snapshot.absolute_humidity_gm3


def _get_dew_point_value(snapshot: DeviceSnapshot) -> float | None:
    return snapshot.dew_point_c


SENSOR_DEFINITIONS: dict[SensorKind, SensorDefinition] = {
    SensorKind.AIR: SensorDefinition(
        kind=SensorKind.AIR,
        unique_id_suffix=UNIQUE_ID_SUFFIX_AIR,
        default_name=DEFAULT_DISPLAY_NAME,
        default_icon=DEFAULT_ICON,
        native_unit_of_measurement=UNIT_KPA,
        device_class=None,
        snapshot_getter=_get_air_value,
    ),
    SensorKind.LEAF: SensorDefinition(
        kind=SensorKind.LEAF,
        unique_id_suffix=UNIQUE_ID_SUFFIX_LEAF,
        default_name=DEFAULT_LEAF_DISPLAY_NAME,
        default_icon=DEFAULT_LEAF_ICON,
        native_unit_of_measurement=UNIT_KPA,
        device_class=None,
        snapshot_getter=_get_leaf_value,
    ),
    SensorKind.ABSOLUTE_HUMIDITY: SensorDefinition(
        kind=SensorKind.ABSOLUTE_HUMIDITY,
        unique_id_suffix=UNIQUE_ID_SUFFIX_ABSOLUTE_HUMIDITY,
        default_name=DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME,
        default_icon=DEFAULT_ABSOLUTE_HUMIDITY_ICON,
        native_unit_of_measurement=UNIT_GM3,
        device_class=SensorDeviceClass.ABSOLUTE_HUMIDITY,
        snapshot_getter=_get_absolute_humidity_value,
    ),
    SensorKind.DEW_POINT: SensorDefinition(
        kind=SensorKind.DEW_POINT,
        unique_id_suffix=UNIQUE_ID_SUFFIX_DEW_POINT,
        default_name=DEFAULT_DEW_POINT_DISPLAY_NAME,
        default_icon=DEFAULT_DEW_POINT_ICON,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        snapshot_getter=_get_dew_point_value,
    ),
}
