"""Domain enums for VPD Air Auto."""

from __future__ import annotations

from enum import StrEnum


class SensorKind(StrEnum):
    """Supported derived sensor kinds."""

    AIR = "air"
    LEAF = "leaf"
    ABSOLUTE_HUMIDITY = "absolute_humidity"
    DEW_POINT = "dew_point"
