from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ENTITY_CATEGORY,
    CONF_FRIENDLY_NAME,
    CONF_ID,
    CONF_PLATFORM,
    UnitOfElectricCurrent,
    CONF_UNIT_OF_MEASUREMENT,
    EntityCategory,
    Platform,
    UnitOfElectricPotential,
    UnitOfPower,
)

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from custom_components.localtuya.const import (
    CONF_DPS_STRINGS,
    CONF_OPTIONS,
    CONF_PASSIVE_ENTITY,
    CONF_RESTORE_ON_RECONNECT,
    CONF_SCALING,
    CONF_STATE_CLASS,
)
from custom_components.localtuya.core.entity_generator import (
    DEVICE_CLOUD_DATA,
    gen_cloud_entities,
)


SOCKET_DATA = {
    CONF_FRIENDLY_NAME: "Freezer",
    CONF_DPS_STRINGS: [
        "1 ( code: switch_1 , value: True )",
        "19 ( code: cur_power , value: 0 )",
        "20 ( code: cur_voltage , value: 1229 )",
        "38 ( code: relay_status , value: on )",
    ],
    DEVICE_CLOUD_DATA: {
        "dps_data": {
            "1": {
                "code": "switch_1",
                "dp_id": 1,
                "type": "bool",
                "value": True,
                "accessMode": "rw",
                "values": '{"type": "bool"}',
            },
            "19": {
                "code": "cur_power",
                "dp_id": 19,
                "type": "value",
                "value": 0,
                "accessMode": "ro",
                "values": '{"type": "value", "max": 80000, "min": 0, "scale": 1, "step": 1, "unit": "W"}',
            },
            "20": {
                "code": "cur_voltage",
                "dp_id": 20,
                "type": "value",
                "value": 1229,
                "accessMode": "ro",
                "values": '{"type": "value", "max": 5000, "min": 0, "scale": 1, "step": 1, "unit": "V"}',
            },
            "38": {
                "code": "relay_status",
                "dp_id": 38,
                "type": "enum",
                "value": "on",
                "accessMode": "rw",
                "values": '{"type": "enum", "range": ["off", "on", "memory"]}',
            },
        }
    },
}


def test_gen_cloud_entities_from_socket_metadata():
    entities = {entity[CONF_ID]: entity for entity in gen_cloud_entities(SOCKET_DATA)}

    assert entities["1"][CONF_PLATFORM] == Platform.SWITCH
    assert entities["1"][CONF_RESTORE_ON_RECONNECT] is False
    assert entities["1"][CONF_PASSIVE_ENTITY] is False

    assert entities["19"][CONF_PLATFORM] == Platform.SENSOR
    assert entities["19"][CONF_DEVICE_CLASS] == SensorDeviceClass.POWER
    assert entities["19"][CONF_STATE_CLASS] == SensorStateClass.MEASUREMENT
    assert entities["19"][CONF_UNIT_OF_MEASUREMENT] == UnitOfPower.WATT
    assert entities["19"][CONF_SCALING] == 0.1

    assert entities["20"][CONF_PLATFORM] == Platform.SENSOR
    assert entities["20"][CONF_DEVICE_CLASS] == SensorDeviceClass.VOLTAGE
    assert entities["20"][CONF_UNIT_OF_MEASUREMENT] == UnitOfElectricPotential.VOLT

    assert entities["38"][CONF_PLATFORM] == Platform.SELECT
    assert entities["38"][CONF_OPTIONS] == {
        "off": "Off",
        "on": "On",
        "memory": "Memory",
    }
    assert entities["38"][CONF_ENTITY_CATEGORY] == EntityCategory.CONFIG


def test_gen_cloud_entities_skips_used_ids():
    entities = gen_cloud_entities(SOCKET_DATA, used_ids={"1", "19", "20"})

    assert [entity[CONF_ID] for entity in entities] == ["38"]


def test_gen_cloud_entities_maps_phase_b_c_codes():
    phase_data = {
        CONF_FRIENDLY_NAME: "Three Phase Device",
        CONF_DPS_STRINGS: [
            "21 ( code: phase_b_current , value: 1000 )",
            "22 ( code: phase_c_power , value: 500 )",
            "23 ( code: phase_b_voltage , value: 2300 )",
        ],
        DEVICE_CLOUD_DATA: {
            "dps_data": {
                "21": {
                    "code": "phase_b_current",
                    "dp_id": 21,
                    "type": "value",
                    "value": 1000,
                    "accessMode": "ro",
                    "values": '{"type": "value", "max": 20000, "min": 0, "scale": 0, "step": 1, "unit": "mA"}',
                },
                "22": {
                    "code": "phase_c_power",
                    "dp_id": 22,
                    "type": "value",
                    "value": 500,
                    "accessMode": "ro",
                    "values": '{"type": "value", "max": 20000, "min": 0, "scale": 0, "step": 1, "unit": "W"}',
                },
                "23": {
                    "code": "phase_b_voltage",
                    "dp_id": 23,
                    "type": "value",
                    "value": 2300,
                    "accessMode": "ro",
                    "values": '{"type": "value", "max": 3000, "min": 0, "scale": 1, "step": 1, "unit": "V"}',
                },
            }
        },
    }

    entities = {entity[CONF_ID]: entity for entity in gen_cloud_entities(phase_data)}

    assert entities["21"][CONF_DEVICE_CLASS] == SensorDeviceClass.CURRENT
    assert entities["21"][CONF_UNIT_OF_MEASUREMENT] == UnitOfElectricCurrent.MILLIAMPERE
    assert entities["22"][CONF_DEVICE_CLASS] == SensorDeviceClass.POWER
    assert entities["22"][CONF_UNIT_OF_MEASUREMENT] == UnitOfPower.WATT
    assert entities["23"][CONF_DEVICE_CLASS] == SensorDeviceClass.VOLTAGE
    assert entities["23"][CONF_UNIT_OF_MEASUREMENT] == UnitOfElectricPotential.VOLT
