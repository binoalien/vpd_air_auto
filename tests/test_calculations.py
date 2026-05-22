"""Tests for VPD Air Auto calculations."""

from __future__ import annotations

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import State

from custom_components.vpd_air_auto.calculations import (
    calculate_absolute_humidity_gm3,
    calculate_dew_point_c,
    calculate_leaf_temperature_c,
    calculate_vpd_air_kpa,
    calculate_vpd_leaf_kpa,
    coerce_humidity_pct,
    coerce_number,
    coerce_temperature_c,
    saturation_vapor_pressure_kpa,
)


def test_saturation_vapor_pressure_returns_expected_reference_value() -> None:
    """Test saturation vapor pressure returns expected reference value."""
    result = saturation_vapor_pressure_kpa(25.0)
    assert result is not None
    assert round(result, 3) == 3.168


def test_calculate_vpd_air_kpa() -> None:
    """Test calculate vpd air kpa."""
    assert calculate_vpd_air_kpa(25.0, 60.0) == 1.267


def test_calculate_leaf_temperature_c() -> None:
    """Test calculate leaf temperature c."""
    assert calculate_leaf_temperature_c(25.0, -2.0) == 23.0


def test_calculate_vpd_leaf_kpa() -> None:
    """Test calculate vpd leaf kpa."""
    assert calculate_vpd_leaf_kpa(25.0, 60.0, 23.0) == 0.909


def test_calculate_absolute_humidity_gm3() -> None:
    """Test calculate absolute humidity gm3."""
    assert calculate_absolute_humidity_gm3(25.0, 60.0) == 13.814


def test_calculate_dew_point_c() -> None:
    """Test calculate dew point c."""
    assert calculate_dew_point_c(25.0, 60.0) == 16.698


def test_coerce_number_handles_unknown_invalid_and_numeric_values() -> None:
    """Test coerce number handles unknown invalid and numeric values."""
    assert coerce_number(None) is None
    assert coerce_number(STATE_UNKNOWN) is None
    assert coerce_number(STATE_UNAVAILABLE) is None
    assert coerce_number("nan") is None
    assert coerce_number("inf") is None
    assert coerce_number("-inf") is None
    assert coerce_number("abc") is None
    assert coerce_number("12.5") == 12.5


def test_coerce_temperature_c_handles_supported_and_invalid_units(
) -> None:
    """Test coerce temperature c handles celsius fahrenheit kelvin and invalid units."""
    assert coerce_temperature_c(None) is None
    assert (
        coerce_temperature_c(
            State("sensor.temp_c", "25", {"unit_of_measurement": "°C"}, None)
        )
        == 25.0
    )
    result = coerce_temperature_c(
        State("sensor.temp_f", "77", {"unit_of_measurement": "°F"}, None)
    )
    assert result is not None
    assert round(result, 3) == 25.0
    result = coerce_temperature_c(
        State("sensor.temp_k_zero", "273.15", {"unit_of_measurement": "K"}, None)
    )
    assert result is not None
    assert round(result, 3) == 0.0
    result = coerce_temperature_c(
        State("sensor.temp_k", "298.15", {"unit_of_measurement": "K"}, None)
    )
    assert result is not None
    assert round(result, 3) == 25.0
    assert (
        coerce_temperature_c(
            State("sensor.temp_k_invalid", "-1", {"unit_of_measurement": "K"}, None)
        )
        is None
    )
    assert (
        coerce_temperature_c(
            State("sensor.temp_invalid", "12", {"unit_of_measurement": "R"}, None)
        )
        is None
    )
    assert coerce_temperature_c(State("sensor.temp_bad", "bad", {}, None)) is None


def test_coerce_humidity_pct_handles_none_invalid_and_out_of_range() -> None:
    """Test coerce humidity pct handles none invalid and out of range."""
    assert coerce_humidity_pct(None) is None
    assert (
        coerce_humidity_pct(State("sensor.humidity_unknown", STATE_UNKNOWN, {}, None))
        is None
    )
    assert (
        coerce_humidity_pct(State("sensor.humidity_negative", "-1", {}, None)) is None
    )
    assert coerce_humidity_pct(State("sensor.humidity_nan", "nan", {}, None)) is None
    assert coerce_humidity_pct(State("sensor.humidity_inf", "inf", {}, None)) is None
    assert coerce_humidity_pct(State("sensor.humidity_over", "101", {}, None)) is None
    assert coerce_humidity_pct(State("sensor.humidity_valid", "45", {}, None)) == 45.0


def test_calculation_helpers_return_none_for_missing_inputs() -> None:
    """Test calculation helpers return none for missing inputs."""
    assert saturation_vapor_pressure_kpa(None) is None
    assert calculate_dew_point_c(None, 60.0) is None
    assert calculate_dew_point_c(25.0, None) is None
    assert calculate_dew_point_c(25.0, 0.0) is None
    assert calculate_dew_point_c(25.0, 101.0) is None
    assert calculate_vpd_air_kpa(None, 60.0) is None
    assert calculate_vpd_air_kpa(25.0, None) is None
    assert calculate_vpd_leaf_kpa(None, 60.0, 23.0) is None
    assert calculate_vpd_leaf_kpa(25.0, None, 23.0) is None
    assert calculate_vpd_leaf_kpa(25.0, 60.0, None) is None
    assert calculate_absolute_humidity_gm3(None, 60.0) is None
    assert calculate_absolute_humidity_gm3(25.0, None) is None


def test_calculate_absolute_humidity_returns_none_for_non_physical_kelvin() -> None:
    """Test calculate absolute humidity returns none for non physical kelvin."""
    assert calculate_absolute_humidity_gm3(-274.0, 50.0) is None
