from custom_components.vpd_air_auto.policy.repository import PolicyRepository
from custom_components.vpd_air_auto.policy.resolver import PolicyResolver


def test_policy_resolver_global_default() -> None:
    result = PolicyResolver(PolicyRepository({"enable_air": False})).resolve_for_device("dev")
    assert result.enable_air is False


def test_policy_resolver_priority() -> None:
    resolver = PolicyResolver(
        PolicyRepository(
            {
                "enable_air": True,
                "leaf_offset_c": -2.0,
                "area_policies": {"area": {"enable_air": False, "leaf_offset_c": -1.0}},
                "device_policies": {"dev": {"enable_air": True, "leaf_offset_c": -3.0}},
            }
        )
    )
    result = resolver.resolve_for_device("dev", "area")
    assert result.enable_air is True
    assert result.leaf_offset_c == -3.0


def test_policy_resolver_area_fallback() -> None:
    resolver = PolicyResolver(
        PolicyRepository(
            {
                "enable_leaf": True,
                "area_policies": {"area": {"enable_leaf": False}},
                "device_policies": {"dev": {}},
            }
        )
    )
    assert resolver.resolve_for_device("dev", "area").enable_leaf is False


def test_policy_resolver_source_override_passthrough() -> None:
    resolver = PolicyResolver(
        PolicyRepository(
            {
                "source_overrides": {
                    "dev": {
                        "temperature_entity_id": "sensor.t",
                        "humidity_entity_id": "sensor.h",
                    }
                }
            }
        )
    )
    result = resolver.resolve_for_device("dev")
    assert result.source_override is not None
    assert result.source_override.humidity_entity_id == "sensor.h"
