"""Tests for policy repository parsing and serialization."""

from __future__ import annotations

from custom_components.vpd_air_auto.const import (
    CONF_ENABLE_AIR,
    CONF_LEAF_OFFSET,
    DEFAULT_ENABLE_LEAF,
)
from custom_components.vpd_air_auto.policy.repository import (
    AREA_POLICIES_KEY,
    DEVICE_POLICIES_KEY,
    DISPLAY_POLICY_KEY,
    GLOBAL_POLICY_KEY,
    SOURCE_OVERRIDES_KEY,
    PolicyRepository,
)


def test_policy_repository_defaults_when_raw_is_missing() -> None:
    """Repository should resolve stable defaults for empty input."""
    repo = PolicyRepository()

    assert repo.global_policy.enable_air is True
    assert repo.global_policy.enable_leaf is DEFAULT_ENABLE_LEAF
    assert repo.area_policies == {}
    assert repo.device_policies == {}
    assert repo.source_overrides == {}


def test_policy_repository_parses_nested_policy_data() -> None:
    """Repository should parse all supported nested scopes."""
    repo = PolicyRepository(
        {
            GLOBAL_POLICY_KEY: {CONF_ENABLE_AIR: False, CONF_LEAF_OFFSET: -1.5},
            DISPLAY_POLICY_KEY: {"icon": "mdi:test", "display_name": "Air"},
            AREA_POLICIES_KEY: {
                "area-1": {"enable_leaf": False, "leaf_offset": -0.5}
            },
            DEVICE_POLICIES_KEY: {
                "device-1": {"enable_leaf": True, "leaf_offset": -1.2}
            },
            SOURCE_OVERRIDES_KEY: {
                "device-1": {
                    "temperature_entity_id": "sensor.temp",
                    "humidity_entity_id": "sensor.hum",
                }
            },
        }
    )

    assert repo.global_policy.enable_air is False
    assert repo.global_policy.leaf_offset_c == -1.5
    assert repo.global_policy.display.icon == "mdi:test"
    assert repo.global_policy.display.display_name == "Air"
    assert repo.area_policies["area-1"].enable_leaf is False
    assert repo.device_policies["device-1"].leaf_offset_c == -1.2
    assert repo.source_overrides["device-1"].temperature_entity_id == "sensor.temp"


def test_policy_repository_as_dict_returns_v2_shape() -> None:
    """Repository should round-trip to expected V2 dictionary shape."""
    repo = PolicyRepository({GLOBAL_POLICY_KEY: {CONF_ENABLE_AIR: False}})

    data = repo.as_dict()

    assert GLOBAL_POLICY_KEY in data
    assert DISPLAY_POLICY_KEY in data
    assert AREA_POLICIES_KEY in data
    assert DEVICE_POLICIES_KEY in data
    assert SOURCE_OVERRIDES_KEY in data
    assert data[GLOBAL_POLICY_KEY][CONF_ENABLE_AIR] is False
