"""Tests for policy repository parsing."""

from __future__ import annotations

from custom_components.vpd_air_auto.const import DEFAULT_LEAF_OFFSET
from custom_components.vpd_air_auto.policy.repository import PolicyRepository


def test_repository_defaults_when_raw_missing() -> None:
    repo = PolicyRepository()

    assert repo.global_policy.enable_air is True
    assert repo.global_policy.leaf_offset_c == DEFAULT_LEAF_OFFSET
    assert repo.area_policies == {}
    assert repo.device_policies == {}
    assert repo.source_overrides == {}


def test_repository_parses_global_scoped_and_source_overrides() -> None:
    repo = PolicyRepository(
        {
            "global_policy": {
                "enable_air": False,
                "enable_leaf": True,
                "enable_absolute_humidity": False,
                "enable_dew_point": True,
                "leaf_offset": -1.5,
                "icon": "mdi:test-air",
                "display_name": "Air",
                "leaf_icon": "mdi:test-leaf",
                "leaf_display_name": "Leaf",
                "absolute_humidity_icon": "mdi:test-ah",
                "absolute_humidity_display_name": "AH",
                "dew_point_icon": "mdi:test-dew",
                "dew_point_display_name": "Dew",
            },
            "area_policies": {
                "area-1": {"enable_leaf": False, "leaf_offset": -0.5},
            },
            "device_policies": {
                "device-1": {"enable_air": True, "enable_dew_point": False},
            },
            "source_overrides": {
                "device-1": {
                    "temperature_entity_id": "sensor.temp_manual",
                    "humidity_entity_id": "sensor.humidity_manual",
                }
            },
        }
    )

    assert repo.global_policy.enable_air is False
    assert repo.global_policy.enable_absolute_humidity is False
    assert repo.global_policy.leaf_offset_c == -1.5
    assert repo.global_policy.display.icon == "mdi:test-air"
    assert repo.area_policies["area-1"].enable_leaf is False
    assert repo.area_policies["area-1"].leaf_offset_c == -0.5
    assert repo.device_policies["device-1"].enable_air is True
    assert repo.device_policies["device-1"].enable_dew_point is False
    assert (
        repo.source_overrides["device-1"].temperature_entity_id == "sensor.temp_manual"
    )


def test_repository_as_dict_returns_normalized_tree() -> None:
    raw = {
        "global_policy": {"enable_air": False, "leaf_offset": -1.0},
        "area_policies": {"area-1": {"enable_leaf": False}},
    }
    repo = PolicyRepository(raw)

    output = repo.as_dict()

    assert output["global_policy"]["enable_air"] is False
    assert output["global_policy"]["leaf_offset_c"] == -1.0
    assert output["area_policies"]["area-1"]["enable_leaf"] is False
    assert "display" in output["global_policy"]
