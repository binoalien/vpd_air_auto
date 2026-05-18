"""Backward-compatible exports for source selection helpers."""

from .discovery.selection import (  # noqa: F401
    TARGET_HUMIDITY,
    TARGET_TEMPERATURE,
    SourceCandidate,
    choose_best_entity_id,
    normalize_identifier,
)
