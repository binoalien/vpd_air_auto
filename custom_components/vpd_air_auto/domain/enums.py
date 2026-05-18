"""Domain enums for VPD Air Auto."""

from __future__ import annotations

from enum import StrEnum


class SensorKind(StrEnum):
    """Canonical sensor kinds supported by the integration."""

    AIR = "air"
    LEAF = "leaf"
    ABSOLUTE_HUMIDITY = "absolute_humidity"
    DEW_POINT = "dew_point"
