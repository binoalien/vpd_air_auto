"""Tests for policy resolution priority and display behavior."""

from __future__ import annotations

from custom_components.vpd_air_auto.policy.repository import (
    AREA_POLICIES_KEY,
    DEVICE_POLICIES_KEY,
    GLOBAL_POLICY_KEY,
    SOURCE_OVERRIDES_KEY,
    PolicyRepository,
)
from custom_components.vpd_air_auto.policy.resolver import PolicyResolver


def test_policy_resolver_uses_global_defaults_without_overrides() -> None:
    """Resolver should fall back to global defaults when no scoped overrides exist."""
    resolver = PolicyResolver(PolicyRepository())

    effective = resolver.resolve_for_device("device-1")

    assert effective.enable_air is True
    assert effective.enable_leaf is True
    assert effective.enable_absolute_humidity is True
    assert effective.enable_dew_point is True
    assert effective.leaf_offset_c == -2.0


def test_policy_resolver_applies_device_over_area_over_global_priority() -> None:
    """Resolver should apply Device > Area > Global precedence consistently."""
    resolver = PolicyResolver(
        PolicyRepository(
            {
                GLOBAL_POLICY_KEY: {"enable_leaf": True, "leaf_offset": -2.0},
                AREA_POLICIES_KEY: {
                    "area-1": {"enable_leaf": False, "leaf_offset": -1.0}
                },
                DEVICE_POLICIES_KEY: {
                    "device-1": {"enable_leaf": True, "leaf_offset": -0.2}
                },
            }
        )
    )

    effective = resolver.resolve_for_device("device-1", "area-1")

    assert effective.enable_leaf is True
    assert effective.leaf_offset_c == -0.2


def test_policy_resolver_exposes_source_override_without_runtime_activation() -> None:
    """Resolver should return source override model only as policy output."""
    resolver = PolicyResolver(
        PolicyRepository(
            {
                SOURCE_OVERRIDES_KEY: {
                    "device-1": {
                        "temperature_entity_id": "sensor.temp",
                        "humidity_entity_id": "sensor.hum",
                    }
                }
            }
        )
    )

    effective = resolver.resolve_for_device("device-1")

    assert effective.source_override is not None
    assert effective.source_override.temperature_entity_id == "sensor.temp"
