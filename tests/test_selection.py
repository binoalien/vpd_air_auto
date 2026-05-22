"""Tests for VPD Air Auto source selection."""

from __future__ import annotations

from custom_components.vpd_air_auto.discovery.selection import (
    TARGET_HUMIDITY,
    TARGET_TEMPERATURE,
    SourceCandidate,
    choose_best_entity_id,
    normalize_identifier,
)


def test_normalize_identifier() -> None:
    """Test normalize identifier."""
    assert normalize_identifier("Air Temperature") == "airtemperature"


def test_prefers_temperature_suffix_and_valid_value() -> None:
    """Test prefers temperature suffix and valid value."""
    candidates = [
        SourceCandidate(
            entity_id="sensor.device_temp",
            device_class=TARGET_TEMPERATURE,
            unit_of_measurement="°C",
            entity_category="diagnostic",
            value_valid=False,
            normalized_identifiers=frozenset({"temp"}),
        ),
        SourceCandidate(
            entity_id="sensor.device_temperature",
            device_class=TARGET_TEMPERATURE,
            unit_of_measurement="°C",
            entity_category=None,
            value_valid=True,
            normalized_identifiers=frozenset({"temperature"}),
        ),
    ]

    assert (
        choose_best_entity_id(candidates, TARGET_TEMPERATURE)
        == "sensor.device_temperature"
    )


def test_prefers_humidity_suffix_over_generic_name() -> None:
    """Test prefers humidity suffix over generic name."""
    candidates = [
        SourceCandidate(
            entity_id="sensor.device_sensor",
            device_class=TARGET_HUMIDITY,
            unit_of_measurement="%",
            entity_category=None,
            value_valid=True,
            normalized_identifiers=frozenset({"humidity"}),
        ),
        SourceCandidate(
            entity_id="sensor.device_relative_humidity",
            device_class=TARGET_HUMIDITY,
            unit_of_measurement="%",
            entity_category=None,
            value_valid=True,
            normalized_identifiers=frozenset({"relativehumidity", "humidity"}),
        ),
    ]

    assert (
        choose_best_entity_id(candidates, TARGET_HUMIDITY)
        == "sensor.device_relative_humidity"
    )


def test_temperature_selection_does_not_prefer_kelvin_unit() -> None:
    """Temperature selection should not treat Kelvin as a supported temperature unit."""
    candidates = [
        SourceCandidate(
            entity_id="sensor.tent_temperature",
            device_class=TARGET_TEMPERATURE,
            unit_of_measurement="K",
            entity_category=None,
            value_valid=True,
            normalized_identifiers=frozenset({"temperature"}),
        ),
        SourceCandidate(
            entity_id="sensor.tent_air_temp",
            device_class=TARGET_TEMPERATURE,
            unit_of_measurement="°C",
            entity_category=None,
            value_valid=True,
            normalized_identifiers=frozenset({"temperature", "temp"}),
        ),
    ]

    assert choose_best_entity_id(candidates, TARGET_TEMPERATURE) == "sensor.tent_air_temp"
