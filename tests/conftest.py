"""Shared pytest fixtures for the VPD Air Auto custom integration."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading integrations from ``custom_components`` for all tests."""
