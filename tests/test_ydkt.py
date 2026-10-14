"""Test for the ydkt (portable air conditioner) entity configuration."""

from unittest.mock import AsyncMock

from . import *
from custom_components.localtuya.climate import (
    LocalTuyaClimate,
    HVACMode,
    DOMAIN as PLATFORM_DOMAIN,
)
from custom_components.localtuya.core.ha_entities import (
    DEVICE_CLOUD_DATA,
    gen_localtuya_entities,
)

YDKT_DEVICE_DATA = {
    "device_config": {
        "friendly_name": "Portable AC",
        "dps_strings": [
            "1 ( code: power , value: True )",
            "2 ( code: temp_set , value: 24 )",
            "3 ( code: temp_current , value: 26 )",
            "4 ( code: mode , value: cold )",
            "5 ( code: windspeed , value: med )",
            "6 ( code: windshake , value: on )",
            "7 ( code: anion , value: False )",
            "8 ( code: Sleeping_mode , value: False )",
        ],
    },
    "device_cloud_info": {
        "category": "ydkt",
        "dps_data": {
            "1": {
                "code": "power",
                "dp_id": 1,
                "type": "Boolean",
                "value": True,
                "values": "{}",
            },
            "2": {
                "code": "temp_set",
                "dp_id": 2,
                "type": "Integer",
                "value": 24,
                "values": '{"type": "value", "min": 16, "max": 31, "scale": 0, "step": 1, "unit": "C"}',
            },
            "3": {
                "code": "temp_current",
                "dp_id": 3,
                "type": "Integer",
                "value": 26,
                "values": '{"type": "value", "min": 0, "max": 50, "scale": 0, "step": 1, "unit": "C"}',
            },
            "4": {
                "code": "mode",
                "dp_id": 4,
                "type": "Enum",
                "value": "cold",
                "values": '{"type": "enum", "range": ["cold", "hot", "wet", "wind"]}',
            },
            "5": {
                "code": "windspeed",
                "dp_id": 5,
                "type": "Enum",
                "value": "med",
                "values": '{"type": "enum", "range": ["low", "med", "high"]}',
            },
            "6": {
                "code": "windshake",
                "dp_id": 6,
                "type": "Enum",
                "value": "on",
                "values": '{"type": "enum", "range": ["off", "on"]}',
            },
            "7": {
                "code": "anion",
                "dp_id": 7,
                "type": "Boolean",
                "value": False,
                "values": "{}",
            },
            "8": {
                "code": "Sleeping_mode",
                "dp_id": 8,
                "type": "Boolean",
                "value": False,
                "values": "{}",
            },
        },
    },
}


def ydkt_localtuya_data():
    """Return the data passed to gen_localtuya_entities for a ydkt device."""
    return {
        **YDKT_DEVICE_DATA["device_config"],
        DEVICE_CLOUD_DATA: YDKT_DEVICE_DATA["device_cloud_info"],
    }


async def test_ydkt_auto_configure():
    entities = gen_localtuya_entities(ydkt_localtuya_data(), "ydkt")

    climate = next(e for e in entities if e["platform"] == "climate")

    # The first matching DP of each config tuple must be selected.
    assert climate["id"] == "1"  # DPCode.POWER
    assert climate["target_temperature_dp"] == "2"  # DPCode.TEMP_SET
    assert climate["current_temperature_dp"] == "3"  # DPCode.TEMP_CURRENT
    assert climate["hvac_mode_dp"] == "4"  # DPCode.MODE
    assert climate["fan_speed_dp"] == "5"  # DPCode.WINDSPEED
    assert climate["swing_mode_dp"] == "6"  # DPCode.WINDSHAKE

    # DP values are remapped into HA values using the cloud DP data.
    assert climate["hvac_mode_set"] == {
        HVACMode.COOL: "cold",
        HVACMode.HEAT: "hot",
        HVACMode.DRY: "wet",
        HVACMode.FAN_ONLY: "wind",
    }
    assert climate["fan_speed_list"] == "low,med,high"
    assert climate["swing_modes"] == {"off": "Off", "on": "On"}
    assert climate["min_temperature"] == 16
    assert climate["max_temperature"] == 31

    # The ionizer and sleep switches are generated next to the climate entity.
    switches = {e["id"] for e in entities if e["platform"] == "switch"}
    assert switches == {"7", "8"}


async def test_ydkt_auto_configure_alternate_dps():
    # Devices may report the fallback codes of the config tuples instead.
    localtuya_data = {
        "friendly_name": "Portable AC",
        "dps_strings": [
            "1 ( code: switch , value: True )",
            "2 ( code: temp_set , value: 24 )",
            "3 ( code: temp_current , value: 26 )",
            "4 ( code: mode , value: cold )",
            "5 ( code: fan_speed_enum , value: med )",
            "6 ( code: windshake , value: on )",
        ],
    }

    entities = gen_localtuya_entities(localtuya_data, "ydkt")
    climate = next(e for e in entities if e["platform"] == "climate")

    assert climate["id"] == "1"  # DPCode.SWITCH
    assert climate["fan_speed_dp"] == "5"  # DPCode.FAN_SPEED_ENUM
    # Without cloud data the static custom configs are used.
    assert climate["hvac_mode_set"] == {
        HVACMode.COOL: "cold",
        HVACMode.HEAT: "hot",
        HVACMode.DRY: "wet",
        HVACMode.FAN_ONLY: "wind",
    }


async def test_ydkt_climate_entity():
    entities = gen_localtuya_entities(ydkt_localtuya_data(), "ydkt")
    config = {DEVICE_NAME: {**DEVICE_CONFIG, "entities": entities}}

    device = await init(config, PLATFORM_DOMAIN, LocalTuyaClimate)
    entity: LocalTuyaClimate = get_entites(device)[0]

    assert set(entity.hvac_modes) == {
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
        HVACMode.OFF,
    }
    assert entity.fan_modes == ["low", "med", "high"]
    assert entity.swing_modes == ["Off", "On"]

    device.status_updated(
        {"1": True, "2": 24, "3": 26, "4": "cold", "5": "med", "6": "on"}
    )
    assert entity.hvac_mode == HVACMode.COOL
    assert entity.fan_mode == "med"
    assert entity.swing_mode == "On"
    assert entity.target_temperature == 24
    assert entity.current_temperature == 26

    entity._device.set_dp = AsyncMock()
    entity._device.set_dps = AsyncMock()

    await entity.async_set_hvac_mode(HVACMode.HEAT)
    entity._device.set_dps.assert_awaited_once_with({"4": "hot"})

    await entity.async_set_fan_mode("high")
    entity._device.set_dp.assert_awaited_once_with("high", "5")

    entity._device.set_dp.reset_mock()
    await entity.async_set_swing_mode("On")
    entity._device.set_dp.assert_awaited_once_with("on", "6")
