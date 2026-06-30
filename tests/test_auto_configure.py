from . import *
from custom_components.localtuya.config_flow import (
    auto_entity_labels,
    filter_auto_entities,
    validate_input,
)
from custom_components.localtuya.core.ha_entities import (
    gen_localtuya_entities,
    DATA_PLATFORMS,
)
from custom_components.localtuya.const import (
    PLATFORMS,
    CONF_DEVICE_SLEEP_TIME,
    CONF_ENABLE_DEBUG,
    CONF_FRIENDLY_NAME,
    CONF_LOCAL_KEY,
    CONF_PROTOCOL_VERSION,
)
from homeassistant.const import CONF_DEVICE_ID, CONF_HOST


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


def test_auto_configure_review_labels_show_cloud_metadata():
    category = COVER_DEVICE_DATA["device_cloud_info"]["category"]
    entities = gen_localtuya_entities(COVER_DEVICE_DATA["device_config"], category)
    labels = auto_entity_labels(
        entities,
        COVER_DEVICE_DATA["device_cloud_info"]["dps_data"],
    )

    assert labels[0].startswith("DP 101:")
    assert "\ncode:" in labels[0]
    assert "\ntype:" in labels[0]
    assert "| access:" in labels[0]
    assert any("value: open" in label.lower() for label in labels)
    assert labels.index(next(label for label in labels if label.startswith("DP 101:"))) < labels.index(
        next(label for label in labels if label.startswith("DP 12:"))
    )


def test_filter_auto_entities_uses_the_same_sorted_order_as_labels():
    entities = [
        {"id": "12", "friendly_name": "Fault", "platform": "sensor"},
        {"id": "101", "friendly_name": "Remote Register", "platform": "switch"},
    ]
    dps_data = {
        "12": {"type": "bitmap", "accessMode": "ro", "code": "fault", "value": 0},
        "101": {
            "type": "bool",
            "accessMode": "rw",
            "code": "remote_register",
            "value": False,
        },
    }

    selected_label = next(
        label for label in auto_entity_labels(entities, dps_data) if label.startswith("DP 101:")
    )

    filtered = filter_auto_entities(entities, [selected_label], dps_data)

    assert [entity["id"] for entity in filtered] == ["101"]


async def test_validate_input_accepts_cloud_dps_when_local_scan_is_empty():
    class DummyInterface:
        connected = False
        is_connecting = False

        async def detect_available_dps(self, cid=None):
            return {}

        async def close(self):
            return None

    class DummyCloudData:
        def __init__(self):
            self.device_list = {
                "dev1": {
                    "dps_data": {
                        "1": {
                            "code": "switch",
                            "type": "bool",
                            "values": '{"type":"bool"}',
                            "accessMode": "rw",
                            "value": True,
                        }
                    }
                }
            }

        async def async_get_device_functions(self, device_id):
            return self.device_list[device_id]["dps_data"]

    class DummyEntryRuntime:
        def __init__(self):
            self.devices = {}
            self.cloud_data = DummyCloudData()

    import custom_components.localtuya.config_flow as config_flow_module

    original_connect = config_flow_module.pytuya.connect

    async def fake_connect(*args, **kwargs):
        return DummyInterface()

    config_flow_module.pytuya.connect = fake_connect
    try:
        result = await validate_input(
            DummyEntryRuntime(),
            {
                CONF_DEVICE_ID: "dev1",
                CONF_HOST: "192.168.1.10",
                CONF_LOCAL_KEY: "abc123",
                CONF_PROTOCOL_VERSION: "3.3",
                CONF_ENABLE_DEBUG: False,
                CONF_FRIENDLY_NAME: "Device 1",
                CONF_DEVICE_SLEEP_TIME: 0,
            },
        )

        assert result[CONF_PROTOCOL_VERSION] == "3.3"
        assert any("1" in dps for dps in result["dps_strings"])
    finally:
        config_flow_module.pytuya.connect = original_connect
