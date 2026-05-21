"""Tests for effective policy resolution ordering."""

from custom_components.vpd_air_auto.policy.repository import PolicyRepository
from custom_components.vpd_air_auto.policy.resolver import PolicyResolver


def test_resolver_uses_global_when_no_scope_overrides() -> None:
    """Resolver returns global values when no scoped data exists."""
    resolver = PolicyResolver(PolicyRepository())

    effective = resolver.resolve_for_device(device_id="d1", area_id="a1")

    assert effective.enable_air is True
    assert effective.enable_leaf is True
    assert effective.leaf_offset_c == -2.0
    assert effective.behavior_source == "global"
    assert effective.leaf_offset_source == "global"


def test_resolver_applies_area_override_over_global() -> None:
    """Area-level values override global defaults when device has no override."""
    repository = PolicyRepository(
        {
            "global_policy": {"enable_leaf": True, "leaf_offset": -2.0},
            "area_policies": {"grow": {"enable_leaf": False, "leaf_offset": -0.7}},
        }
    )
    effective = PolicyResolver(repository).resolve_for_device(
        device_id="d1",
        area_id="grow",
    )

    assert effective.enable_leaf is False
    assert effective.leaf_offset_c == -0.7
    assert effective.behavior_source == "area"
    assert effective.leaf_offset_source == "area"


def test_resolver_applies_device_override_with_highest_priority() -> None:
    """Device-level values override area and global levels."""
    repository = PolicyRepository(
        {
            "global_policy": {"enable_air": True, "leaf_offset": -2.0},
            "area_policies": {"grow": {"enable_air": False, "leaf_offset": -0.5}},
            "device_policies": {"device-1": {"enable_air": True, "leaf_offset": -1.2}},
            "source_overrides": {
                "device-1": {
                    "temperature_entity_id": "sensor.t",
                }
            },
        }
    )
    effective = PolicyResolver(repository).resolve_for_device(
        device_id="device-1",
        area_id="grow",
    )

    assert effective.enable_air is True
    assert effective.leaf_offset_c == -1.2
    assert effective.leaf_offset_source == "device"
    assert effective.behavior_source == "device"
    assert effective.source_override is not None
    assert effective.source_override.temperature_entity_id == "sensor.t"


def test_resolver_can_ignore_device_overrides_when_disabled() -> None:
    """Runtime can intentionally defer device policy activation."""
    repository = PolicyRepository(
        {
            "global_policy": {"enable_air": True, "leaf_offset": -2.0},
            "area_policies": {"grow": {"enable_air": False, "leaf_offset": -0.5}},
            "device_policies": {"device-1": {"enable_air": True, "leaf_offset": -1.2}},
        }
    )
    effective = PolicyResolver(repository).resolve_for_device(
        device_id="device-1",
        area_id="grow",
        allow_device_policies=False,
    )

    assert effective.enable_air is False
    assert effective.leaf_offset_c == -0.5
    assert effective.behavior_source == "area"
    assert effective.leaf_offset_source == "area"
