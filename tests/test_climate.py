"""Test for localtuya."""

from unittest.mock import AsyncMock
from . import *
import copy
from custom_components.localtuya.climate import (
    LocalTuyaClimate,
    HVACAction,
    HVACMode,
    DOMAIN as PLATFORM_DOMAIN,
)

FAN_SPEED_LIST = ["auto", "low", "middle", "high"]
FAN_SPEED_DICT = {"1": "Silent", "2": "Low", "3": "Middle", "4": "High"}
ENTITY_CONFIG = {
    "friendly_name": "Terrace Floor",
    "entity_category": "None",
    "target_temperature_dp": "16",
    "current_temperature_dp": "24",
    "temperature_step": "1",
    "min_temperature": 7.0,
    "max_temperature": 35.0,
    "precision": "1",
    "target_precision": "1",
    "hvac_mode_dp": "2",
    "hvac_mode_set": {
        "auto": "program",
        "heat": "manual",
        "cool": "COLD",
    },
    "hvac_action_dp": "100",
    "hvac_action_set": {
        "heating": True,
        "idle": False,
    },
    "preset_dp": "5",
    "preset_set": {"holiday": "Holiday Friendly Name"},
    "fan_speed_dp": "6",
    "fan_speed_list": ",".join(FAN_SPEED_LIST),
    "swing_mode_dp": "11",
    "swing_modes": {
        "both": "up-and-down",
        "up": "up-only",
        "down": "down-only",
    },
    "swing_horizontal_dp": "12",
    "swing_horizontal_modes": {
        "both": "left-and-right",
        "left": "left-only",
        "right": "right-only",
    },
    "temperature_unit": "fahrenheit/celsius",
    "id": "1",
    "eco_dp": "101",
    "eco_value": "eco_on",
    "platform": "climate",
    "icon": "",
    "heuristic_action": False,
}
# Entity with Boolean datapoints mapped as swing/preset, as reported in #831.
# The config-flow ObjectSelector can only ever produce string dict keys, so a
# mapping entered in the UI as `true: "on"` / `false: "off"` is stored as
# {"true": "on", "false": "off"} -- while a Boolean datapoint reports real
# Python True/False values.
BOOL_ENTITY_CONFIG = {
    **ENTITY_CONFIG,
    "id": "3",
    "preset_dp": "30",
    "preset_set": {"false": "Normal", "true": "Sleep"},
    "swing_mode_dp": "31",
    "swing_modes": {"false": "off", "true": "on"},
    "swing_horizontal_dp": "32",
    "swing_horizontal_modes": {"false": "off", "true": "on"},
    "eco_dp": "999",  # kept out of DPS_STATUS so eco never shadows preset_set.
}

CONFIG = {
    DEVICE_NAME: {
        **DEVICE_CONFIG,
        "entities": [
            ENTITY_CONFIG,
            {**ENTITY_CONFIG, "id": "2", "fan_speed_list": FAN_SPEED_DICT},
            BOOL_ENTITY_CONFIG,
        ],
    }
}

DPS_STATUS = {
    "1": True,
    "2": "COLD",
    "5": "holiday",
    "6": "middle",
    "11": "both",
    "12": "right",
    "16": 68,  # F
    "24": 24,  # c
    "100": False,
    "101": "ECO_NOT",
    "30": True,
    "31": False,
    "32": True,
}


async def test_climate():
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaClimate)
    entities: list[LocalTuyaClimate] = get_entites(device)

    assert len(entities) > 0
    entity_1, entity_2, *_ = entities
    assert type(entity_1) is LocalTuyaClimate

    assert entity_1._is_on == None

    status = {**DPS_STATUS, **{"1": False}}
    device.status_updated(status)
    assert type(entity_1._state_on) is bool

    assert entity_1._is_on == False
    assert entity_1.hvac_action == HVACAction.OFF
    assert entity_1.hvac_mode == HVACMode.OFF

    device.status_updated(DPS_STATUS)
    assert entity_1._is_on == True
    assert entity_1.hvac_action == HVACAction.IDLE
    assert entity_1.hvac_mode == HVACMode.COOL
    assert entity_1.fan_modes == FAN_SPEED_LIST
    assert entity_2.fan_modes == list(FAN_SPEED_DICT.values())
    assert entity_1.preset_mode == "Holiday Friendly Name"
    assert entity_1.current_temperature == 24
    assert entity_1.target_temperature == 20  # f to c
    assert entity_1.fan_mode == "middle"

    # Eco Preset
    device.status_updated({**DPS_STATUS, **{"101": "eco_on"}})
    assert entity_1.preset_mode == "eco"

    # heuristic_action
    entity_1._hvac_action_dp = None
    status = {**DPS_STATUS, **{"2": "manual", "24": 18.9}}
    device.status_updated(status)
    assert entity_1.hvac_action == HVACAction.HEATING
    status = {**DPS_STATUS, **{"2": "manual", "24": 21.1}}
    device.status_updated(status)
    assert entity_1.hvac_action == HVACAction.IDLE

    # String DP ID
    status = {**DPS_STATUS, **{"1": "OFF"}}
    device.status_updated(status)
    assert not entity_1._is_on
    assert type(entity_1._state_on) is str

    # Integer DP ID
    status = {**DPS_STATUS, **{"1": 1}}
    device.status_updated(status)
    assert entity_1._is_on
    assert type(entity_1._state_on) is int

    # Swing modes
    assert entity_1.swing_mode == "up-and-down"
    assert entity_1.swing_horizontal_mode == "right-only"
    device.status_updated({**DPS_STATUS, **{"11": "up", "12": "both"}})
    assert entity_1.swing_mode == "up-only"
    assert entity_1.swing_horizontal_mode == "left-and-right"


async def test_climate_boolean_swing_and_preset_dps():
    """Regression test for #831.

    Real Boolean datapoints (device sends actual True/False, not the
    strings "true"/"false") configured as the swing/preset DP must still
    update swing_mode/preset_mode, and writing them back must send a real
    bool to the device rather than the string "true"/"false".
    """
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaClimate)
    entity_1, entity_2, entity_3, *_ = get_entites(device)
    assert type(entity_3) is LocalTuyaClimate

    device.status_updated(DPS_STATUS)
    assert entity_3.preset_mode == "Sleep"  # dp "30" == True
    assert entity_3.swing_mode == "off"  # dp "31" == False
    assert entity_3.swing_horizontal_mode == "on"  # dp "32" == True

    # Flip every boolean DP and confirm the entity follows.
    device.status_updated({**DPS_STATUS, **{"30": False, "31": True, "32": False}})
    assert entity_3.preset_mode == "Normal"
    assert entity_3.swing_mode == "on"
    assert entity_3.swing_horizontal_mode == "off"

    # Writing back must send a real bool, not the string "true"/"false",
    # since the datapoint itself is Boolean.
    device.set_dp = AsyncMock()

    await entity_3.async_set_preset_mode("Sleep")
    device.set_dp.assert_called_once_with(True, "30")
    assert device.set_dp.call_args.args[0] is True

    device.set_dp.reset_mock()
    await entity_3.async_set_swing_mode("on")
    device.set_dp.assert_called_once_with(True, "31")
    assert device.set_dp.call_args.args[0] is True

    device.set_dp.reset_mock()
    await entity_3.async_set_swing_horizontal_mode("off")
    device.set_dp.assert_called_once_with(False, "32")
    assert device.set_dp.call_args.args[0] is False
