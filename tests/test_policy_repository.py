from custom_components.vpd_air_auto.const import DEFAULT_ICON, DEFAULT_LEAF_OFFSET
from custom_components.vpd_air_auto.policy.repository import PolicyRepository


def test_policy_repository_defaults_when_raw_missing() -> None:
    repo = PolicyRepository()
    assert repo.global_policy.enable_air is True
    assert repo.global_policy.display.icon == DEFAULT_ICON
    assert repo.global_policy.leaf_offset_c == DEFAULT_LEAF_OFFSET
    assert repo.area_policies == {}
    assert repo.device_policies == {}
    assert repo.source_overrides == {}


def test_policy_repository_parses_full_payload() -> None:
    repo = PolicyRepository(
        {
            "enable_air": False,
            "leaf_offset_c": -1.5,
            "icon": "mdi:custom",
            "area_policies": {"area_1": {"enable_leaf": False, "leaf_offset_c": -3}},
            "device_policies": {"dev_1": {"enable_air": True, "enable_dew_point": False}},
            "source_overrides": {
                "dev_1": {"temperature_entity_id": "sensor.temp", "humidity_entity_id": "sensor.hum"}
            },
        }
    )

    assert repo.global_policy.enable_air is False
    assert repo.global_policy.display.icon == "mdi:custom"
    assert repo.area_policies["area_1"].enable_leaf is False
    assert repo.area_policies["area_1"].leaf_offset_c == -3.0
    assert repo.device_policies["dev_1"].enable_dew_point is False
    assert repo.source_overrides["dev_1"].temperature_entity_id == "sensor.temp"


def test_policy_repository_as_dict_returns_copy() -> None:
    repo = PolicyRepository({"enable_air": False})
    data = repo.as_dict()
    data["enable_air"] = True
    assert repo.as_dict()["enable_air"] is False
