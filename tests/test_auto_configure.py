from . import *
from custom_components.localtuya.core.ha_entities import (
    gen_localtuya_entities,
    DATA_PLATFORMS,
)
from custom_components.localtuya.const import PLATFORMS


@pytest.mark.parametrize("timer_code", ["countdown_left_fan", "fan_countdown_left"])
def test_fan_direction_and_shutdown_timer_auto_configure(timer_code):
    """Expose the direction and writable minute countdown of an fsd fan."""
    device_data = {
        "friendly_name": "Ceiling fan/Light v2",
        "dps_strings": [
            "20 ( code: switch_led , value: False )",
            "23 ( code: temp_value , value: 1000 )",
            "60 ( code: fan_switch , value: True )",
            "62 ( code: fan_speed , value: 1 )",
            "63 ( code: fan_direction , value: reverse )",
            f"64 ( code: {timer_code} , value: 59 )",
            "66 ( code: fan_beep , value: True )",
            "101 ( code: mute , value: False, cloud pull )",
        ],
        "device_cloud_data": {
            "product_name": "ceiling fan/Light v2",
            "dps_data": {
                "63": {
                    "type": "Enum",
                    "values": '{"range":["forward","reverse"]}',
                },
                "64": {
                    "type": "Integer",
                    "values": '{"unit":"min","min":0,"max":540,"scale":0,"step":1}',
                },
            }
        },
    }

    entities = gen_localtuya_entities(device_data, "fsd")
    color_cycle = next(entity for entity in entities if entity["id"] == "23")
    direction = next(entity for entity in entities if entity["id"] == "63")
    timer = next(entity for entity in entities if entity["id"] == "64")

    assert color_cycle["platform"] == "button"
    assert color_cycle["friendly_name"] == "Cycle light color"
    assert color_cycle["device_group"] == "light"
    assert color_cycle["button_press_value"] == 1000
    assert color_cycle["button_log_dp_changes"] is True
    assert direction["platform"] == "select"
    assert direction["device_group"] == "fan"
    assert direction["select_options"] == {
        "forward": "Forward",
        "reverse": "Reverse",
    }
    assert timer["platform"] == "number"
    assert timer["device_group"] == "fan"
    assert timer["min_value"] == 0
    assert timer["max_value"] == 540
    assert timer["unit_of_measurement"] == "min"
    assert (
        next(entity for entity in entities if entity["id"] == "20")["device_group"]
        == "light"
    )
    assert (
        next(entity for entity in entities if entity["id"] == "60")["device_group"]
        == "fan"
    )
    parent_switch = next(entity for entity in entities if entity["id"] == "66")
    assert parent_switch["platform"] == "switch"
    assert "device_group" not in parent_switch
    assert not any(entity["id"] == "101" for entity in entities)

    without_color_dp = {
        **device_data,
        "dps_strings": [
            dp for dp in device_data["dps_strings"] if not dp.startswith("23 ")
        ],
    }
    assert not any(
        entity["platform"] == "button"
        for entity in gen_localtuya_entities(without_color_dp, "fsd")
    )

    other_product = {
        **device_data,
        "device_cloud_data": {
            **device_data["device_cloud_data"],
            "product_name": "Other ceiling fan light",
        },
    }
    assert not any(
        entity["platform"] == "button"
        for entity in gen_localtuya_entities(other_product, "fsd")
    )


COVER_DEVICE_DATA = {
    "device_config": {
        "friendly_name": "Cover",
        "dps_strings": [
            "1 ( code: control , value: open )",
            "2 ( code: percent_control , value: 100 )",
            "3 ( code: percent_state , value: 100 )",
            "5 ( code: control_back_mode , value: forward )",
            "7 ( code: work_state , value: opening )",
            "11 ( code: situation_set , value: fully_open )",
            "12 ( code: fault , value: 0 )",
            "101 ( code: remote_register , value: False, cloud pull )",
            "102 ( code: reset_limit , value: False, cloud pull )",
            "103 ( code: up_confirm , value: True )",
            "104 ( code: middle_confirm , value: False )",
            "105 ( code: down_confirm , value: True )",
            "106 ( code: motor_mode , value: contiuation )",
        ],
    },
    "device_cloud_info": {
        "active_time": 1660859328,
        "biz_type": 18,
        "category": "cl",
        "create_time": 1660859328,
        "icon": "smart/icon/ay1535532217868NsRD0/d303688e83885c9920b0b2dcf3872aa3.png",
        "id": "bfa2f86e3068440a449dhd",
        "ip": "2...1",
        "lat": "",
        "local_key": "999...420",
        "lon": "",
        "model": "",
        "name": "Blind",
        "online": True,
        "owner_id": "13377642",
        "product_id": "jzmy5ut0vishwscm",
        "product_name": "zemismart curtain motor",
        "status": [
            {"code": "control", "value": "open"},
            {"code": "percent_control", "value": 0},
            {"code": "percent_state", "value": 0},
            {"code": "control_back_mode", "value": "forward"},
            {"code": "work_state", "value": "opening"},
            {"code": "situation_set", "value": "fully_open"},
            {"code": "fault", "value": 0},
        ],
        "sub": False,
        "time_zone": "+03:00",
        "uid": "eu1...Hyb",
        "update_time": 1737849634,
        "uuid": "d3a81500860ab39c",
        "dps_data": {
            "1": {
                "code": "control",
                "custom_name": "",
                "dp_id": 1,
                "time": 1737581443559,
                "type": "Enum",
                "value": "open",
                "values": '{"type": "enum", "range": ["open", "stop", "close", "continue"]}',
                "id": 1,
                "accessMode": "rw",
            },
            "2": {
                "code": "percent_control",
                "custom_name": "",
                "dp_id": 2,
                "time": 1738097484455,
                "type": "Integer",
                "value": 0,
                "values": '{"type": "value", "max": 100, "min": 0, "scale": 0, "step": 1, "unit": "%"}',
                "id": 2,
                "accessMode": "rw",
            },
            "3": {
                "code": "percent_state",
                "custom_name": "",
                "dp_id": 3,
                "time": 1738097508589,
                "type": "value",
                "value": 0,
                "id": 3,
                "accessMode": "ro",
                "values": '{"type": "value", "max": 100, "min": 0, "scale": 0, "step": 1, "unit": "%"}',
            },
            "5": {
                "code": "control_back_mode",
                "custom_name": "",
                "dp_id": 5,
                "time": 1734388862581,
                "type": "Enum",
                "value": "forward",
                "values": '{"type": "enum", "range": ["forward", "back"]}',
                "id": 5,
                "accessMode": "rw",
            },
            "7": {
                "code": "work_state",
                "custom_name": "",
                "dp_id": 7,
                "time": 1735420780853,
                "type": "enum",
                "value": "opening",
                "id": 7,
                "accessMode": "ro",
                "values": '{"type": "enum", "range": ["opening", "closing"]}',
            },
            "11": {
                "code": "situation_set",
                "custom_name": "",
                "dp_id": 11,
                "time": 1734388860575,
                "type": "enum",
                "value": "fully_open",
                "id": 11,
                "accessMode": "ro",
                "values": '{"type": "enum", "range": ["fully_open", "fully_close"]}',
            },
            "12": {
                "code": "fault",
                "custom_name": "",
                "dp_id": 12,
                "time": 1734388860586,
                "type": "bitmap",
                "value": 0,
                "id": 12,
                "accessMode": "ro",
                "values": '{"type": "bitmap", "label": ["motor_fault"], "maxlen": 1}',
            },
            "101": {
                "code": "remote_register",
                "custom_name": "",
                "dp_id": 101,
                "time": 1660859328099,
                "type": "bool",
                "value": False,
                "id": 101,
                "accessMode": "rw",
                "values": '{"type": "bool"}',
            },
            "102": {
                "code": "reset_limit",
                "custom_name": "",
                "dp_id": 102,
                "time": 1660859328099,
                "type": "bool",
                "value": False,
                "id": 102,
                "accessMode": "rw",
                "values": '{"type": "bool"}',
            },
            "103": {
                "code": "up_confirm",
                "custom_name": "",
                "dp_id": 103,
                "time": 1734388860596,
                "type": "bool",
                "value": True,
                "id": 103,
                "accessMode": "rw",
                "values": '{"type": "bool"}',
            },
            "104": {
                "code": "middle_confirm",
                "custom_name": "",
                "dp_id": 104,
                "time": 1734388860605,
                "type": "bool",
                "value": False,
                "id": 104,
                "accessMode": "rw",
                "values": '{"type": "bool"}',
            },
            "105": {
                "code": "down_confirm",
                "custom_name": "",
                "dp_id": 105,
                "time": 1734388860616,
                "type": "bool",
                "value": True,
                "id": 105,
                "accessMode": "rw",
                "values": '{"type": "bool"}',
            },
            "106": {
                "code": "motor_mode",
                "custom_name": "",
                "dp_id": 106,
                "time": 1736952575226,
                "type": "enum",
                "value": "contiuation",
                "id": 106,
                "accessMode": "rw",
                "values": '{"type": "enum", "range": ["contiuation", "point"]}',
            },
        },
    },
}


async def test_auto_configure():

    for k in PLATFORMS.values():
        assert k in DATA_PLATFORMS

    category = COVER_DEVICE_DATA["device_cloud_info"]["category"]
    entities = gen_localtuya_entities(COVER_DEVICE_DATA["device_config"], category)
    assert len(entities) > 4
