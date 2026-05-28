"""Tests for VPD Air Auto source selection."""

from __future__ import annotations

from custom_components.vpd_air_auto.discovery.selection import (
    TARGET_HUMIDITY,
    TARGET_TEMPERATURE,
    SourceCandidate,
    candidate_score,
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


def test_temperature_unit_score_does_not_prefer_kelvin_over_celsius() -> None:
    """Kelvin should not receive unit-score preference over Celsius/Fahrenheit."""
    candidates = [
        SourceCandidate(
            entity_id="sensor.grow_tent_temperature",
            device_class=TARGET_TEMPERATURE,
            unit_of_measurement="K",
            entity_category=None,
            value_valid=True,
            normalized_identifiers=frozenset({"temperature"}),
        ),
        SourceCandidate(
            entity_id="sensor.grow_tent_air_temperature",
            device_class=TARGET_TEMPERATURE,
            unit_of_measurement="°C",
            entity_category=None,
            value_valid=True,
            normalized_identifiers=frozenset({"temperature"}),
        ),
    ]

    assert (
        choose_best_entity_id(candidates, TARGET_TEMPERATURE)
        == "sensor.grow_tent_air_temperature"
    )


def _humidity_candidate(unit: str | None) -> SourceCandidate:
    """Build an otherwise equivalent humidity candidate with the given unit."""
    return SourceCandidate(
        entity_id="sensor.grow_tent_humidity",
        device_class=TARGET_HUMIDITY,
        unit_of_measurement=unit,
        entity_category=None,
        value_valid=True,
        normalized_identifiers=frozenset({"humidity"}),
    )


def test_humidity_unit_variants_receive_preferred_unit_score() -> None:
    """Supported humidity unit variants receive the same positive unit score."""
    supported_units = [
        "%",
        "%RH",
        "RH%",
        "percent",
        "percentage",
        "relative humidity",
    ]

    scores = [
        candidate_score(_humidity_candidate(unit), TARGET_HUMIDITY)[2]
        for unit in supported_units
    ]

    assert scores == [25] * len(supported_units)


def test_unsupported_humidity_units_receive_no_unit_score() -> None:
    """Unsupported humidity units should not receive preferred unit score."""
    unsupported_scores = [
        candidate_score(_humidity_candidate(unit), TARGET_HUMIDITY)[2]
        for unit in ("g/m³", "foo")
    ]

    assert unsupported_scores == [0, 0]


def test_supported_humidity_unit_beats_unsupported_unit() -> None:
    """A supported RH unit should beat an otherwise equivalent unsupported unit."""
    supported = _humidity_candidate("%RH")
    unsupported = SourceCandidate(
        entity_id="sensor.grow_tent_humidity_unsupported",
        device_class=TARGET_HUMIDITY,
        unit_of_measurement="foo",
        entity_category=None,
        value_valid=True,
        normalized_identifiers=frozenset({"humidity"}),
    )

    assert candidate_score(supported, TARGET_HUMIDITY) > candidate_score(
        unsupported, TARGET_HUMIDITY
    )
