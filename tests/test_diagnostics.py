"""Tests for VPD Air Auto diagnostics."""

from __future__ import annotations

from types import SimpleNamespace

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vpd_air_auto.const import DOMAIN
from custom_components.vpd_air_auto.diagnostics import (
    async_get_config_entry_diagnostics,
    async_get_device_diagnostics,
)
from custom_components.vpd_air_auto.models import DeviceSnapshot, DeviceTopology


async def test_config_entry_diagnostics_contains_entry_and_coordinator_data(
    hass: HomeAssistant,
) -> None:
    """Test config entry diagnostics contains entry and coordinator data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="VPD Air Auto",
        data={"scan_interval": 300},
        options={"display_name": "VPDair"},
        version=1,
        minor_version=1,
    )
    entry.add_to_hass(hass)
    entry.runtime_data = SimpleNamespace(
        diagnostics_payload=lambda: {
            "options": {"display_name": "VPDair"},
            "tracked_entity_ids": ["sensor.grow_tent_temperature"],
        }
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["entry"]["entry_id"] == entry.entry_id
    assert diagnostics["entry"]["title"] == "VPD Air Auto"
    assert diagnostics["entry"]["data"] == {"scan_interval": 300}
    assert diagnostics["entry"]["options"] == {"display_name": "VPDair"}
    assert diagnostics["coordinator"]["tracked_entity_ids"] == [
        "sensor.grow_tent_temperature"
    ]


async def test_device_diagnostics_contains_topology_snapshot_and_creatable_kinds(
    hass: HomeAssistant,
) -> None:
    """Test device diagnostics contains topology snapshot and creatable kinds."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)

    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("test", "grow-tent")},
        name="Grow Tent",
    )

    topology = DeviceTopology(
        device_id=device.id,
        device_name="Grow Tent",
        temperature_entity_id="sensor.grow_tent_temperature",
        humidity_entity_id="sensor.grow_tent_humidity",
        blocked_sensor_kinds=frozenset({"leaf"}),
        area_id="area-1",
        area_name="Grow Room",
    )
    snapshot = DeviceSnapshot(
        device_id=device.id,
        device_name="Grow Tent",
        temperature_entity_id="sensor.grow_tent_temperature",
        humidity_entity_id="sensor.grow_tent_humidity",
        temperature_c=25.0,
        humidity_pct=60.0,
        leaf_offset_c=-2.0,
        leaf_temperature_c=23.0,
        dew_point_c=16.68,
        vpd_air_kpa=1.27,
        vpd_leaf_kpa=1.58,
        absolute_humidity_gm3=13.8,
    )

    entry.runtime_data = SimpleNamespace(
        device_diagnostics_payload=lambda device_id: {
            "topology": {
                "device_id": topology.device_id,
                "device_name": topology.device_name,
                "temperature_entity_id": topology.temperature_entity_id,
                "humidity_entity_id": topology.humidity_entity_id,
                "blocked_sensor_kinds": sorted(topology.blocked_sensor_kinds),
            },
            "snapshot": {
                "device_id": snapshot.device_id,
                "device_name": snapshot.device_name,
                "temperature_entity_id": snapshot.temperature_entity_id,
                "humidity_entity_id": snapshot.humidity_entity_id,
                "temperature_c": snapshot.temperature_c,
                "humidity_pct": snapshot.humidity_pct,
                "leaf_offset_c": snapshot.leaf_offset_c,
                "leaf_temperature_c": snapshot.leaf_temperature_c,
                "dew_point_c": snapshot.dew_point_c,
                "vpd_air_kpa": snapshot.vpd_air_kpa,
                "vpd_leaf_kpa": snapshot.vpd_leaf_kpa,
                "absolute_humidity_gm3": snapshot.absolute_humidity_gm3,
            },
            "area": {"area_id": "area-1", "area_name": "Grow Room"},
            "creatable_kinds": ["absolute_humidity", "air", "dew_point"],
            "blocked_sensor_kinds": ["leaf"],
            "enabled_kinds": ["absolute_humidity", "air", "dew_point", "leaf"],
            "effective_policy": {
                "enable_air": True,
                "enable_leaf": True,
                "enable_absolute_humidity": True,
                "enable_dew_point": True,
                "leaf_offset_c": -2.0,
                "behavior_source": "global",
                "leaf_offset_source": "global",
                "display": {"display_name": "VPDair"},
                "source_override": None,
            },
            "entity_plan": {
                "creatable_kinds": ["absolute_humidity", "air", "dew_point"],
                "blocked_sensor_kinds": ["leaf"],
                "enabled_kinds": ["absolute_humidity", "air", "dew_point", "leaf"],
            },
        }
    )

    diagnostics = await async_get_device_diagnostics(hass, entry, device)

    assert diagnostics["entry_id"] == entry.entry_id
    assert diagnostics["device"]["id"] == device.id
    assert diagnostics["device"]["name"] == "Grow Tent"
    assert (
        diagnostics["topology"]["temperature_entity_id"]
        == "sensor.grow_tent_temperature"
    )
    assert diagnostics["topology"]["blocked_sensor_kinds"] == ["leaf"]
    assert diagnostics["snapshot"]["vpd_air_kpa"] == 1.27
    assert diagnostics["snapshot"]["absolute_humidity_gm3"] == 13.8
    assert diagnostics["snapshot"]["dew_point_c"] == 16.68
    assert diagnostics["creatable_kinds"] == ["absolute_humidity", "air", "dew_point"]
    assert diagnostics["area"] == {"area_id": "area-1", "area_name": "Grow Room"}
    assert diagnostics["blocked_sensor_kinds"] == ["leaf"]
    assert diagnostics["effective_policy"]["behavior_source"] == "global"
    assert diagnostics["entity_plan"]["enabled_kinds"] == ["absolute_humidity", "air", "dew_point", "leaf"]
