"""Release-readiness checks for changelog metadata."""

from __future__ import annotations

from pathlib import Path


def test_changelog_has_release_ready_200_heading() -> None:
    """2.0.0 changelog heading should not remain unreleased."""
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")

    assert "## 2.0.0\n" in changelog
    assert "## 2.0.0 (unreleased)" not in changelog
