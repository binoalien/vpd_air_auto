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
    """Build a humidity candidate for unit-scoring tests."""
    return SourceCandidate(
        entity_id="sensor.grow_tent_humidity",
        device_class=TARGET_HUMIDITY,
        unit_of_measurement=unit,
        entity_category=None,
        value_valid=True,
        normalized_identifiers=frozenset({"humidity"}),
    )


def test_humidity_unit_score_accepts_supported_relative_humidity_units() -> None:
    """Supported humidity unit variants should receive the same unit score."""
    percent_score = candidate_score(_humidity_candidate("%"), TARGET_HUMIDITY)

    for unit in ("%RH", "RH%", "percent", "percentage", "relative humidity"):
        assert (
            candidate_score(_humidity_candidate(unit), TARGET_HUMIDITY)
            == percent_score
        )


def test_humidity_unit_score_rejects_unsupported_units() -> None:
    """Unsupported humidity units should not receive preferred unit score."""
    percent_score = candidate_score(_humidity_candidate("%"), TARGET_HUMIDITY)

    for unit in ("g/m³", "foo"):
        unsupported_score = candidate_score(_humidity_candidate(unit), TARGET_HUMIDITY)
        assert unsupported_score[2] == 0
        assert percent_score[2] > unsupported_score[2]


def test_humidity_percent_rh_candidate_beats_unsupported_unit() -> None:
    """A %RH humidity candidate should outrank an otherwise equal unsupported unit."""
    candidates = [
        SourceCandidate(
            entity_id="sensor.grow_tent_humidity_a",
            device_class=TARGET_HUMIDITY,
            unit_of_measurement="foo",
            entity_category=None,
            value_valid=True,
            normalized_identifiers=frozenset({"humidity"}),
        ),
        SourceCandidate(
            entity_id="sensor.grow_tent_humidity_b",
            device_class=TARGET_HUMIDITY,
            unit_of_measurement="%RH",
            entity_category=None,
            value_valid=True,
            normalized_identifiers=frozenset({"humidity"}),
        ),
    ]

    assert (
        choose_best_entity_id(candidates, TARGET_HUMIDITY)
        == "sensor.grow_tent_humidity_b"
    )
