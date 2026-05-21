"""Tests for the V2 policy repository."""

import json

from custom_components.vpd_air_auto.const import DEFAULT_DISPLAY_NAME
from custom_components.vpd_air_auto.policy.repository import PolicyRepository


def test_repository_defaults_when_raw_missing() -> None:
    """Repository falls back to global defaults with no input data."""
    repository = PolicyRepository()

    assert repository.global_policy.enable_air is True
    assert repository.global_policy.enable_leaf is True
    assert repository.global_policy.enable_absolute_humidity is True
    assert repository.global_policy.enable_dew_point is True
    assert repository.global_policy.leaf_offset_c == -2.0
    assert not repository.area_policies
    assert not repository.device_policies
    assert not repository.source_overrides


def test_repository_parses_nested_policy_maps() -> None:
    """Repository parses global, scoped, and source override sections."""
    repository = PolicyRepository(
        {
            "global_policy": {
                "enable_air": False,
                "leaf_offset": -1.5,
                "display_name": "AirX",
            },
            "area_policies": {
                "area_1": {"enable_leaf": False, "leaf_offset": -0.5},
            },
            "device_policies": {
                "dev_1": {"enable_air": True, "enable_dew_point": False},
            },
            "source_overrides": {
                "dev_1": {
                    "temperature_entity_id": "sensor.temp",
                    "humidity_entity_id": "sensor.hum",
                }
            },
        }
    )

    assert repository.global_policy.enable_air is False
    assert repository.global_policy.leaf_offset_c == -1.5
    assert repository.global_policy.display.display_name == "AirX"
    assert repository.area_policies["area_1"].enable_leaf is False
    assert repository.area_policies["area_1"].leaf_offset_c == -0.5
    assert repository.device_policies["dev_1"].enable_air is True
    assert repository.device_policies["dev_1"].enable_dew_point is False
    assert repository.source_overrides["dev_1"].temperature_entity_id == "sensor.temp"


def test_repository_roundtrip_as_dict() -> None:
    """Repository serializes back to dictionary format."""
    repository = PolicyRepository({"area_policies": {"a": {"enable_leaf": False}}})

    data = repository.as_dict()

    assert "global_policy" in data
    assert data["area_policies"]["a"]["enable_leaf"] is False
    assert data["device_policies"] == {}


def test_repository_ignores_non_bool_values() -> None:
    """String values must not be coerced into booleans."""
    repository = PolicyRepository(
        {
            "global_policy": {"enable_air": "false"},
            "area_policies": {"a1": {"enable_air": "false"}},
        }
    )

    assert repository.global_policy.enable_air is True
    assert repository.area_policies["a1"].enable_air is None


def test_repository_scoped_missing_bool_fields_stay_none() -> None:
    """Missing optional scoped bool fields remain None."""
    repository = PolicyRepository({"device_policies": {"d1": {"leaf_offset": -1.0}}})

    scoped = repository.device_policies["d1"]
    assert scoped.enable_air is None
    assert scoped.enable_leaf is None
    assert scoped.enable_absolute_humidity is None
    assert scoped.enable_dew_point is None


def test_repository_tolerates_malformed_values() -> None:
    """Malformed and future-shaped values should not raise or coerce unsafely."""
    repository = PolicyRepository(
        {
            "global_policy": {
                "enable_air": "true",
                "leaf_offset": "bad-float",
                "icon": "   ",
            },
            "area_policies": {
                "a1": {"leaf_offset": "bad"},
                "": {"enable_air": True},
                "   ": {"enable_air": True},
                123: {"enable_air": True},
            },
            "device_policies": {
                "d1": {"enable_leaf": "false", "leaf_offset": "2.2"},
                "  d2  ": {"enable_air": True},
            },
            "source_overrides": {
                "d1": {
                    "temperature_entity_id": " climate.room ",
                    "humidity_entity_id": "sensor.h1",
                },
                "d2": "invalid-shape",
                "": {"temperature_entity_id": "sensor.t"},
                "   ": {"humidity_entity_id": "sensor.h"},
                42: {"temperature_entity_id": "sensor.t"},
                "d3": {"temperature_entity_id": None, "humidity_entity_id": "   "},
                "  d4 ": {"temperature_entity_id": "sensor.t4"},
            },
        }
    )

    assert repository.global_policy.enable_air is True
    assert repository.global_policy.leaf_offset_c == -2.0
    assert repository.global_policy.display.display_name == DEFAULT_DISPLAY_NAME
    assert repository.area_policies["a1"].leaf_offset_c is None
    assert "" not in repository.area_policies
    assert "   " not in repository.area_policies
    assert "123" not in repository.area_policies
    assert repository.device_policies["d1"].enable_leaf is None
    assert repository.device_policies["d1"].leaf_offset_c == 2.2
    assert "d2" in repository.device_policies
    assert repository.source_overrides["d1"].temperature_entity_id is None
    assert repository.source_overrides["d1"].humidity_entity_id == "sensor.h1"
    assert "d2" not in repository.source_overrides
    assert "d3" not in repository.source_overrides
    assert repository.source_overrides["d4"].temperature_entity_id == "sensor.t4"


def test_repository_rejects_non_finite_leaf_offsets() -> None:
    """Nan/inf leaf offsets must fall back safely."""
    repository = PolicyRepository(
        {
            "global_policy": {"leaf_offset": "nan"},
            "area_policies": {"a1": {"leaf_offset": "nan"}},
            "device_policies": {"d1": {"leaf_offset": "inf"}},
        }
    )

    assert repository.global_policy.leaf_offset_c == -2.0
    assert repository.area_policies["a1"].leaf_offset_c is None
    assert repository.device_policies["d1"].leaf_offset_c is None


def test_repository_global_leaf_offset_inf_uses_default() -> None:
    """Global inf leaf offset must use default value."""
    repository = PolicyRepository({"global_policy": {"leaf_offset": "inf"}})

    assert repository.global_policy.leaf_offset_c == -2.0


def test_repository_as_dict_is_json_serializable() -> None:
    """Repository as_dict output should remain JSON serializable."""
    repository = PolicyRepository(
        {
            "source_overrides": {
                "bad": {"temperature_entity_id": " "},
                "good_temp": {"temperature_entity_id": "sensor.temp"},
                "good_hum": {"humidity_entity_id": "sensor.hum"},
            }
        }
    )

    data = repository.as_dict()
    json.dumps(data)

    assert "bad" not in data["source_overrides"]
    assert (
        data["source_overrides"]["good_temp"]["temperature_entity_id"]
        == "sensor.temp"
    )
    assert data["source_overrides"]["good_hum"]["humidity_entity_id"] == "sensor.hum"
