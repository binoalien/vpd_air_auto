"""Tests for the V2 policy repository."""

from custom_components.vpd_air_auto.policy.repository import PolicyRepository


def test_repository_defaults_when_raw_missing() -> None:
    """Repository falls back to global defaults with no input data."""
    repository = PolicyRepository()

    assert repository.global_policy.enable_air is True
    assert repository.global_policy.enable_leaf is True
    assert repository.global_policy.enable_absolute_humidity is True
    assert repository.global_policy.enable_dew_point is True
    assert repository.global_policy.leaf_offset_c == -2.0
    assert repository.area_policies == {}
    assert repository.device_policies == {}
    assert repository.source_overrides == {}


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
