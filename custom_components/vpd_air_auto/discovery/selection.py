"""Source-sensor selection helpers for VPD Air Auto."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

TARGET_TEMPERATURE = "temperature"
TARGET_HUMIDITY = "humidity"

_NORMALIZE_PATTERN = re.compile(r"[^a-z0-9]+")

_TEMPERATURE_SUFFIXES: tuple[str, ...] = (
    "_temperature",
    "_air_temperature",
    "_temp",
)
_HUMIDITY_SUFFIXES: tuple[str, ...] = (
    "_humidity",
    "_relative_humidity",
    "_rh",
)

_TEMPERATURE_TOKENS = {
    "temperature",
    "airtemperature",
    "roomtemperature",
    "ambienttemperature",
    "temp",
}
_HUMIDITY_TOKENS = {
    "humidity",
    "relativehumidity",
    "rh",
}


@dataclass(frozen=True, slots=True)
class SourceCandidate:
    """A normalized source-entity candidate for one target metric."""

    entity_id: str
    device_class: str | None
    unit_of_measurement: str | None
    entity_category: str | None
    value_valid: bool
    normalized_identifiers: frozenset[str] = field(default_factory=frozenset)


def normalize_identifier(value: str | None) -> str:
    """Normalize text for stable comparisons."""
    if not isinstance(value, str):
        return ""
    return _NORMALIZE_PATTERN.sub("", value.lower())


def choose_best_entity_id(
    candidates: list[SourceCandidate],
    target_device_class: str,
) -> str | None:
    """Choose the most likely source entity for one target device class."""
    if not candidates:
        return None

    best = max(
        candidates,
        key=lambda candidate: candidate_score(candidate, target_device_class),
    )
    return best.entity_id


def candidate_score(
    candidate: SourceCandidate,
    target_device_class: str,
) -> tuple[int, int, int, int, int, int, int, str]:
    """Return a stable sortable score for one source candidate."""
    expected_tokens = (
        _TEMPERATURE_TOKENS
        if (target_device_class == TARGET_TEMPERATURE)
        else _HUMIDITY_TOKENS
    )
    unit_score = _unit_score(candidate.unit_of_measurement, target_device_class)
    suffix_score = _suffix_score(candidate.entity_id, target_device_class)
    token_score = _token_score(candidate.normalized_identifiers, expected_tokens)
    category_score = _category_score(candidate.entity_category)
    validity_score = 50 if candidate.value_valid else 0
    exact_class_score = 100 if candidate.device_class == target_device_class else 0
    shorter_entity_id_score = max(0, 20 - len(candidate.entity_id))
    return (
        exact_class_score,
        validity_score,
        unit_score,
        suffix_score,
        token_score,
        category_score,
        shorter_entity_id_score,
        candidate.entity_id,
    )


def _unit_score(unit: str | None, target_device_class: str) -> int:
    normalized = normalize_identifier(unit)
    if target_device_class == TARGET_TEMPERATURE:
        if normalized in {"c", "f"}:
            return 25
        return 0

    return 25 if unit == "%" else 0


def _suffix_score(entity_id: str, target_device_class: str) -> int:
    entity_name = entity_id.split(".", 1)[1] if "." in entity_id else entity_id
    suffixes = (
        _TEMPERATURE_SUFFIXES
        if (target_device_class == TARGET_TEMPERATURE)
        else _HUMIDITY_SUFFIXES
    )
    for index, suffix in enumerate(suffixes):
        if entity_name.endswith(suffix):
            return 30 - index
    return 0


def _token_score(identifiers: frozenset[str], expected_tokens: set[str]) -> int:
    return len(identifiers.intersection(expected_tokens)) * 10


def _category_score(entity_category: str | None) -> int:
    if entity_category is None:
        return 15
    if entity_category == "diagnostic":
        return 5
    return 0
