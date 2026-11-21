"""Test for localtuya."""

import voluptuous as vol

from . import *
from custom_components.localtuya.vacuum import (
    flow_schema,
    LocalTuyaVacuum,
    DOMAIN as PLATFORM_DOMAIN,
    VacuumActivity,
    CONF_MODE_DP,
    CONF_PAUSE_DP,
    CONF_RETURN_HOME_DP,
    CONF_RETURN_MODE,
    VacuumEntityFeature,
)

CONFIG = {
    DEVICE_NAME: {
        **DEVICE_CONFIG,
        "entities": [
            {
                "entity_category": "None",
                "powergo_dp": "2",
                "idle_status_value": "standby,sleep",
                "docked_status_value": "charging,chargecompleted,charge_done",
                "returning_status_value": "docking,to_charge,goto_charge",
                "paused_state": "paused",
                "stop_status": "standby",
                "pause_dp": "101",
                "mode_dp": "3",
                "modes": "smart,zone,pose,part,chargego,wallfollow,selectroom",
                "return_mode": "chargego",
                "fan_speed_dp": "14",
                "fan_speeds": "strong,normal,quiet",
                "clean_time_dp": "17",
                "clean_area_dp": "16",
                "clean_record_dp": "19",
                "locate_dp": "13",
                "fault_dp": "18",
                "friendly_name": "",
                "id": "5",
                "platform": PLATFORM_DOMAIN,
                "icon": "mdi:robot-vacuum",
            }
        ],
    }
}

DPS_STATUS = {
    "2": True,  # powergo_dp
    "3": "smart",  # mode_dp
    "5": "cleaning",  # id - state
    "13": False,  # locate_dp
    "14": "quiet",  # fan_speed_dp
    "16": 0,  # clean_area_dp
    "17": 0,  # clean_time_dp
    "18": 0,  # fault_dp
    "19": "",  # clean_record_dp
    "101": False,  # pause_dp
}


async def test_vacuum():
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaVacuum)
    entities: list[LocalTuyaVacuum] = get_entites(device)

    assert len(entities) > 0
    entity_1, *_ = entities
    assert type(entity_1) is LocalTuyaVacuum

    entity_1_cfg = CONFIG[DEVICE_NAME]["entities"][0]

    status = DPS_STATUS.copy()
    device.status_updated(status)
    assert entity_1.state == VacuumActivity.CLEANING
    assert entity_1.fan_speed == "quiet"
    assert status[entity_1_cfg[CONF_MODE_DP]] in entity_1._modes_list

    device.status_updated({entity_1_cfg[CONF_PAUSE_DP]: True})
    assert entity_1.state == VacuumActivity.PAUSED

    device.status_updated({entity_1_cfg["id"]: "standby"})
    assert entity_1.state == VacuumActivity.IDLE


async def test_vacuum_return_home():
    # return_mode path (default config): writes the mode value to the mode DP.
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaVacuum)
    entity_1, *_ = get_entites(device)
    entity_1._device.set_dp = AsyncMock()

    assert entity_1.supported_features & VacuumEntityFeature.RETURN_HOME
    await entity_1.async_return_to_base()
    entity_1._device.set_dp.assert_awaited_once_with("chargego", "3")

    # return_home_dp takes precedence over return_mode and writes True to it.
    entity_cfg = {**CONFIG[DEVICE_NAME]["entities"][0], CONF_RETURN_HOME_DP: "4"}
    config = {DEVICE_NAME: {**DEVICE_CONFIG, "entities": [entity_cfg]}}
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaVacuum)
    entity_2, *_ = get_entites(device)
    entity_2._device.set_dp = AsyncMock()

    await entity_2.async_return_to_base()
    entity_2._device.set_dp.assert_awaited_once_with(True, "4")


async def test_vacuum_return_home_dp_only():
    # return_home_dp alone advertises RETURN_HOME even without a usable return_mode.
    entity_cfg = {
        key: value
        for key, value in CONFIG[DEVICE_NAME]["entities"][0].items()
        if key != CONF_RETURN_MODE
    }
    entity_cfg[CONF_RETURN_HOME_DP] = "4"
    config = {DEVICE_NAME: {**DEVICE_CONFIG, "entities": [entity_cfg]}}
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaVacuum)
    entity_1, *_ = get_entites(device)
    entity_1._device.set_dp = AsyncMock()

    assert entity_1.supported_features & VacuumEntityFeature.RETURN_HOME
    await entity_1.async_return_to_base()
    entity_1._device.set_dp.assert_awaited_once_with(True, "4")


async def test_vacuum_return_home_unsupported(caplog):
    # Neither return_home_dp nor return_mode: no feature and an error is logged.
    entity_cfg = {
        key: value
        for key, value in CONFIG[DEVICE_NAME]["entities"][0].items()
        if key != CONF_RETURN_MODE
    }
    config = {DEVICE_NAME: {**DEVICE_CONFIG, "entities": [entity_cfg]}}
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaVacuum)
    entity_1, *_ = get_entites(device)
    entity_1._device.set_dp = AsyncMock()

    assert not entity_1.supported_features & VacuumEntityFeature.RETURN_HOME
    await entity_1.async_return_to_base()
    entity_1._device.set_dp.assert_not_awaited()
    assert "Missing command for return home" in caplog.text


def test_vacuum_flow_schema_has_return_home_dp():
    schema = flow_schema({"1": "bool", "3": "str"})
    optional_keys = {str(key) for key in schema if isinstance(key, vol.Optional)}
    assert CONF_RETURN_HOME_DP in optional_keys
