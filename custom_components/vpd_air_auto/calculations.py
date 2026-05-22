"""Calculation and state-conversion helpers for VPD Air Auto."""

from __future__ import annotations

import math

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import State

_DEW_POINT_A = 17.625
_DEW_POINT_B = 243.04


def coerce_number(value: str | None) -> float | None:
    """Convert a Home Assistant state string to a float."""
    if value in (None, STATE_UNKNOWN, STATE_UNAVAILABLE):
        return None

    try:
        number = float(value)
    except TypeError, ValueError:
        return None
    return number if math.isfinite(number) else None


def coerce_temperature_c(state: State | None) -> float | None:
    """Convert a temperature state to Celsius."""
    if state is None:
        return None

    value = coerce_number(state.state)
    if value is None:
        return None

    unit = state.attributes.get("unit_of_measurement")
    if unit in (None, "°C", "°c", "C", "c"):
        return value
    if unit in ("°F", "°f", "F", "f"):
        return (value - 32.0) * 5.0 / 9.0
    if unit in ("K", "k", "°K", "°k"):
        if value < 0:
            return None
        return value - 273.15
    return None


def coerce_humidity_pct(state: State | None) -> float | None:
    """Convert a humidity state to relative humidity in percent."""
    if state is None:
        return None

    humidity_pct = coerce_number(state.state)
    if humidity_pct is None:
        return None

    if humidity_pct < 0 or humidity_pct > 100:
        return None

    return humidity_pct


def calculate_leaf_temperature_c(
    temperature_c: float | None,
    leaf_offset_c: float,
) -> float | None:
    """Calculate the inferred leaf temperature in Celsius."""
    if temperature_c is None:
        return None
    return round(temperature_c + leaf_offset_c, 3)


def saturation_vapor_pressure_kpa(temperature_c: float | None) -> float | None:
    """Calculate saturation vapor pressure in kPa from Celsius."""
    if temperature_c is None:
        return None

    return 0.6108 * math.exp((17.27 * temperature_c) / (temperature_c + 237.3))


def calculate_dew_point_c(
    temperature_c: float | None,
    humidity_pct: float | None,
) -> float | None:
    """Calculate dew point in °C from air temperature in °C and RH in %."""
    if temperature_c is None or humidity_pct is None:
        return None
    if humidity_pct <= 0 or humidity_pct > 100:
        return None

    gamma = math.log(humidity_pct / 100.0) + (_DEW_POINT_A * temperature_c) / (
        _DEW_POINT_B + temperature_c
    )
    return round((_DEW_POINT_B * gamma) / (_DEW_POINT_A - gamma), 3)


def calculate_vpd_air_kpa(
    temperature_c: float | None,
    humidity_pct: float | None,
) -> float | None:
    """Calculate VPDair in kPa from air temperature in °C and RH in %."""
    if temperature_c is None or humidity_pct is None:
        return None

    saturation_vapor_pressure = saturation_vapor_pressure_kpa(temperature_c)
    if saturation_vapor_pressure is None:
        return None

    return round(saturation_vapor_pressure * (1 - humidity_pct / 100), 3)


def calculate_vpd_leaf_kpa(
    temperature_c: float | None,
    humidity_pct: float | None,
    leaf_temperature_c: float | None,
) -> float | None:
    """Calculate VPDleaf in kPa using leaf temperature and air RH."""
    if temperature_c is None or humidity_pct is None or leaf_temperature_c is None:
        return None

    leaf_svp = saturation_vapor_pressure_kpa(leaf_temperature_c)
    air_svp = saturation_vapor_pressure_kpa(temperature_c)
    if leaf_svp is None or air_svp is None:
        return None

    actual_vapor_pressure = air_svp * (humidity_pct / 100)
    return round(leaf_svp - actual_vapor_pressure, 3)


def calculate_absolute_humidity_gm3(
    temperature_c: float | None,
    humidity_pct: float | None,
) -> float | None:
    """Calculate absolute humidity in g/m³ from air temperature in °C and RH in %."""
    if temperature_c is None or humidity_pct is None:
        return None

    saturation_vapor_pressure = saturation_vapor_pressure_kpa(temperature_c)
    if saturation_vapor_pressure is None:
        return None

    vapor_pressure_hpa = saturation_vapor_pressure * (humidity_pct / 100) * 10.0
    temperature_k = temperature_c + 273.15
    if temperature_k <= 0:
        return None

    return round((216.7 * vapor_pressure_hpa) / temperature_k, 3)
