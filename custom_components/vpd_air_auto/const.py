"""Constants for the VPD Air Auto integration."""

from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "vpd_air_auto"
PLATFORMS: list[str] = ["sensor"]

CONF_SCAN_INTERVAL = "scan_interval"
CONF_ENABLE_AIR = "enable_air"
CONF_ENABLE_LEAF = "enable_leaf"
CONF_ENABLE_ABSOLUTE_HUMIDITY = "enable_absolute_humidity"
CONF_ENABLE_DEW_POINT = "enable_dew_point"
CONF_ICON = "icon"
CONF_DISPLAY_NAME = "display_name"
CONF_LEAF_ICON = "leaf_icon"
CONF_LEAF_DISPLAY_NAME = "leaf_display_name"
CONF_LEAF_OFFSET = "leaf_offset"
CONF_ABSOLUTE_HUMIDITY_ICON = "absolute_humidity_icon"
CONF_ABSOLUTE_HUMIDITY_DISPLAY_NAME = "absolute_humidity_display_name"
CONF_DEW_POINT_ICON = "dew_point_icon"
CONF_DEW_POINT_DISPLAY_NAME = "dew_point_display_name"

DEFAULT_NAME = "VPD Air Auto"
DEFAULT_SCAN_INTERVAL = 300
MIN_SCAN_INTERVAL = 30
MAX_SCAN_INTERVAL = 86_400

DEFAULT_ENABLE_AIR = True
DEFAULT_ENABLE_LEAF = True
DEFAULT_ENABLE_ABSOLUTE_HUMIDITY = True
DEFAULT_ENABLE_DEW_POINT = True

DEFAULT_ICON = "mdi:water-opacity"
DEFAULT_DISPLAY_NAME = "VPDair"
DEFAULT_LEAF_ICON = "mdi:leaf"
DEFAULT_LEAF_DISPLAY_NAME = "VPDleaf"
DEFAULT_LEAF_OFFSET = -2.0
DEFAULT_ABSOLUTE_HUMIDITY_ICON = "mdi:water"
DEFAULT_ABSOLUTE_HUMIDITY_DISPLAY_NAME = "Absolute Humidity"
DEFAULT_DEW_POINT_ICON = "mdi:thermometer-water"
DEFAULT_DEW_POINT_DISPLAY_NAME = "Dew Point"
MIN_LEAF_OFFSET = -20.0
MAX_LEAF_OFFSET = 20.0

UNIT_KPA = "kPa"
UNIT_GM3 = "g/m³"
UNIT_C = "°C"

SENSOR_KIND_AIR = "air"
SENSOR_KIND_LEAF = "leaf"
SENSOR_KIND_ABSOLUTE_HUMIDITY = "absolute_humidity"
SENSOR_KIND_DEW_POINT = "dew_point"
UNIQUE_ID_SUFFIX_AIR = "vpdair"
UNIQUE_ID_SUFFIX_LEAF = "vpdleaf"
UNIQUE_ID_SUFFIX_ABSOLUTE_HUMIDITY = "absolute_humidity"
UNIQUE_ID_SUFFIX_DEW_POINT = "dew_point"

SOURCE_DOMAIN_SENSOR = "sensor"
SOURCE_DEVICE_CLASS_TEMPERATURE = "temperature"
SOURCE_DEVICE_CLASS_HUMIDITY = "humidity"

UNRECORDED_ATTRIBUTE_TEMPERATURE_ENTITY_ID = "temperature_entity_id"
UNRECORDED_ATTRIBUTE_HUMIDITY_ENTITY_ID = "humidity_entity_id"
UNRECORDED_ATTRIBUTE_LEAF_TEMPERATURE_OFFSET_C = "leaf_temperature_offset_c"


@dataclass(frozen=True, slots=True)  # pylint: disable=too-many-instance-attributes
class IntegrationOptions:  # pylint: disable=too-many-instance-attributes
    """Resolved options for one loaded config entry."""

    scan_interval_seconds: int
    enable_air: bool
    enable_leaf: bool
    enable_absolute_humidity: bool
    enable_dew_point: bool
    icon: str
    display_name: str
    leaf_icon: str
    leaf_display_name: str
    leaf_offset_c: float
    absolute_humidity_icon: str
    absolute_humidity_display_name: str
    dew_point_icon: str
    dew_point_display_name: str


def make_vpdair_unique_id(device_id: str) -> str:
    """Build the unique_id for a VPDair sensor bound to a Home Assistant device."""
    return f"{DOMAIN}_{device_id}_{UNIQUE_ID_SUFFIX_AIR}"


def make_vpdleaf_unique_id(device_id: str) -> str:
    """Build the unique_id for a VPDleaf sensor bound to a device."""
    return f"{DOMAIN}_{device_id}_{UNIQUE_ID_SUFFIX_LEAF}"


def make_absolute_humidity_unique_id(device_id: str) -> str:
    """Build the unique_id for an absolute humidity sensor bound to a device."""
    return f"{DOMAIN}_{device_id}_{UNIQUE_ID_SUFFIX_ABSOLUTE_HUMIDITY}"


def make_dew_point_unique_id(device_id: str) -> str:
    """Build the unique_id for a dew point sensor bound to a device."""
    return f"{DOMAIN}_{device_id}_{UNIQUE_ID_SUFFIX_DEW_POINT}"


def device_id_from_unique_id(unique_id: str) -> str | None:
    """Extract a Home Assistant device_id from a helper unique_id."""
    prefix = f"{DOMAIN}_"
    if not unique_id.startswith(prefix):
        return None

    for suffix in (
        f"_{UNIQUE_ID_SUFFIX_AIR}",
        f"_{UNIQUE_ID_SUFFIX_LEAF}",
        f"_{UNIQUE_ID_SUFFIX_ABSOLUTE_HUMIDITY}",
        f"_{UNIQUE_ID_SUFFIX_DEW_POINT}",
    ):
        if unique_id.endswith(suffix):
            device_id = unique_id[len(prefix) : -len(suffix)]
            return device_id or None

    return None
