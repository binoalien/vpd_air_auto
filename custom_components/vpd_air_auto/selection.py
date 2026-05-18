"""Backward-compatible re-export for source selection helpers."""

from .discovery.selection import (
    SOURCE_SELECTION_SEPARATOR,
    SourceCandidate,
    choose_best_entity_id,
    normalize_identifier,
)

__all__ = [
    "SOURCE_SELECTION_SEPARATOR",
    "SourceCandidate",
    "choose_best_entity_id",
    "normalize_identifier",
]
