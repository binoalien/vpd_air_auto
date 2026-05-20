"""Tests for policy resolver precedence and effective values."""

from __future__ import annotations

from custom_components.vpd_air_auto.policy.repository import PolicyRepository
from custom_components.vpd_air_auto.policy.resolver import PolicyResolver


def test_resolver_uses_global_defaults_without_overrides() -> None:
    resolver = PolicyResolver(PolicyRepository({"global_policy": {"leaf_offset": -2.2}}))

    effective = resolver.resolve(device_id="device-1", area_id="area-1")

    assert effective.enable_air is True
    assert effective.enable_leaf is True
    assert effective.enable_absolute_humidity is True
    assert effective.enable_dew_point is True
    assert effective.leaf_offset_c == -2.2


def test_resolver_applies_device_over_area_over_global_priority() -> None:
    resolver = PolicyResolver(
        PolicyRepository(
            {
                "global_policy": {"enable_air": True, "leaf_offset": -2.0},
                "area_policies": {
                    "area-1": {"enable_air": False, "enable_leaf": False, "leaf_offset": -1.0}
                },
                "device_policies": {
                    "device-1": {"enable_air": True, "enable_dew_point": False, "leaf_offset": -0.5}
                },
            }
        )
    )

    effective = resolver.resolve(device_id="device-1", area_id="area-1")

    assert effective.enable_air is True
    assert effective.enable_leaf is False
    assert effective.enable_dew_point is False
    assert effective.enable_absolute_humidity is True
    assert effective.leaf_offset_c == -0.5


def test_resolver_attaches_source_override_for_device() -> None:
    resolver = PolicyResolver(
        PolicyRepository(
            {
                "source_overrides": {
                    "device-7": {
                        "temperature_entity_id": "sensor.temp_a",
                        "humidity_entity_id": "sensor.rh_a",
                    }
                }
            }
        )
    )

    effective = resolver.resolve(device_id="device-7")

    assert effective.source_override is not None
    assert effective.source_override.temperature_entity_id == "sensor.temp_a"
    assert effective.source_override.humidity_entity_id == "sensor.rh_a"
