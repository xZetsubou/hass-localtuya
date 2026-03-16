"""
    Tuya Devices: https://xzetsubou.github.io/hass-localtuya/auto_configure/

    This functionality is similar to HA Tuya, as it retrieves the category and searches for the corresponding categories. 
    The categories data has been improved & modified to work seamlessly with localtuya

    Device Data: You can obtain all the data for your device from Home Assistant by directly downloading the diagnostics or using entry diagnostics.
        Alternative: Use Tuya IoT.

    Add a new device or modify an existing one:
        1. Make sure the device category doesn't already exist. If you are creating a new one, you can modify existing categories.
        2. In order to add a device, you need to specify the category of the device you want to add inside the entity type dictionary.
    
    Add entities to devices:
        1. Open the file with the name of the entity type on which you want to make changes [e.g. switches.py] and search for your device category.
        2. You can add entities inside the tuple value of the dictionary by including LocalTuyaEntity and passing the parameters for the entity configurations.
        3. These configurations include "id" (required), "icon" (optional), "device_class" (optional), "state_class" (optional), and "name" (optional) [Using COVERS as an example]
            Example: "3 ( code: percent_state , value: 0 )" - Refer to the Device Data section above for more details.
                current_state_dp = DPCode.PERCENT_STATE < This maps the "percent_state" code DP to the current_state_dp configuration.

            If the configuration is not DPS, it will be inserted through "custom_configs". This is used to inject any configuration into the entity configuration
                Example: custom_configs={"positioning_mode": "position"}. I hope that clarifies the concept
                
        Check URL above for more details. 
"""

import json
from .base import LocalTuyaEntity, CONF_DPS_STRINGS, CLOUD_VALUE, DPType
from enum import Enum
from homeassistant.const import Platform, CONF_FRIENDLY_NAME, CONF_PLATFORM, CONF_ID

import logging
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfPower,
    UnitOfElectricPotential,
    UnitOfTemperature,
)

# Supported files
from .alarm_control_panels import ALARMS  # not added yet
from .binary_sensors import BINARY_SENSORS
from .buttons import BUTTONS
from .climates import CLIMATES
from .covers import COVERS
from .fans import FANS
from .humidifiers import HUMIDIFIERS
from .lights import LIGHTS
from .numbers import NUMBERS
from .remotes import REMOTES
from .selects import SELECTS
from .sensors import SENSORS
from .sirens import SIRENS
from .switches import SWITCHES
from .vacuums import VACUUMS
from .locks import LOCKS
from .water_heaters import WATER_HEATERS

# The supported PLATFORMS [ Platform: Data ]
DATA_PLATFORMS = {
    Platform.ALARM_CONTROL_PANEL: ALARMS,
    Platform.BINARY_SENSOR: BINARY_SENSORS,
    Platform.BUTTON: BUTTONS,
    Platform.CLIMATE: CLIMATES,
    Platform.COVER: COVERS,
    Platform.FAN: FANS,
    Platform.HUMIDIFIER: HUMIDIFIERS,
    Platform.LIGHT: LIGHTS,
    Platform.LOCK: LOCKS,
    Platform.NUMBER: NUMBERS,
    Platform.REMOTE: REMOTES,
    Platform.SELECT: SELECTS,
    Platform.SENSOR: SENSORS,
    Platform.SIREN: SIRENS,
    Platform.SWITCH: SWITCHES,
    Platform.VACUUM: VACUUMS,
    Platform.WATER_HEATER: WATER_HEATERS,
}

_LOGGER = logging.getLogger(__name__)

TUYA_CATEGORY = "category"
DEVICE_CLOUD_DATA = "device_cloud_data"


def gen_localtuya_entities(localtuya_data: dict, tuya_category: str) -> list[dict]:
    """Return localtuya entities using the data that provided from TUYA"""
    detected_dps_list: list = localtuya_data.get(CONF_DPS_STRINGS)

    if not tuya_category or not detected_dps_list:
        _LOGGER.debug(f"Missing category: {tuya_category} or DPS: {detected_dps_list}")
        return []

    # Create a mapping of DP ID -> Value
    dps_dict = {}
    for dp_str in detected_dps_list:
        try:
            # Format is usually "ID ( code: CODE , value: VALUE )"
            parts = dp_str.split(' ')
            dp_id = parts[0]
            val_part = dp_str.split('value: ')[1].rsplit(' )', 1)[0]
            dps_dict[dp_id] = val_part
        except Exception:
            continue

    device_name: str = localtuya_data.get(CONF_FRIENDLY_NAME).strip()
    device_cloud_data: dict = localtuya_data.get(DEVICE_CLOUD_DATA, {})
    dps_data = device_cloud_data.get("dps_data", {})

    entities = {}

    for platform, tuya_data in DATA_PLATFORMS.items():
        # TODO: Refactor needed here.
        if cat_data := tuya_data.get(tuya_category):
            for ent_data in cat_data:
                main_confs = ent_data.data
                localtuya_conf = ent_data.localtuya_conf
                localtuya_entity_configs = ent_data.entity_configs
                # Conditions
                contains_any: list[str] = ent_data.contains_any
                entity = {}

                # used_dp = 0
                for k, code in localtuya_conf.items():
                    if type(code) == Enum:
                        code = code.value

                    # If there's multi possible codes.
                    if isinstance(code, tuple):
                        for _code in code:
                            if any(_code in dp.lower().split() for dp in detected_dps_list):
                                code = parse_enum(_code)
                                break
                            else:
                                code = None

                    for dp_data in detected_dps_list:
                        dp_data: str = dp_data.lower()
                        # Same method we use in config_flow to get dp.
                        dp_id = dp_data.split(" ")[0]

                        if k in entity:
                            # if the k already configured break the loop!.
                            _LOGGER.debug(f"{k} Already configured with: {entity[k]}.")
                            break

                        if contains_any is not None:
                            if not any(cond in dp_data for cond in contains_any):
                                continue

                        if code and code.lower() in dp_data.split():
                            entity[k] = dp_id

                # Pull dp values from cloud. still unsure to apply this to all.
                # This is due to the fact that some local values may not same with the values provided from cloud.
                # For now, this is applied only to numbers values.
                for k, v in localtuya_entity_configs.items():
                    if isinstance(v, CLOUD_VALUE):
                        config_dp = entity.get(v.dp_config)
                        dp_values = get_dp_values(config_dp, dps_data, v) or {}

                        if dp_values:
                            entity.update(dp_values)

                if entity:
                    # Update more configs.
                    entity.update(main_confs)
                    entity[CONF_PLATFORM] = platform
                    # If the entity is a sensor and it has a device_class, add it to the entity.
                    if platform == Platform.SENSOR and (
                        d_class := ent_data.data.get("device_class")
                    ):
                        entity["device_class"] = d_class

                    # Check if the entity is already configured.
                    # Note: We using ID as key to avoid duplicate entities.
                    # but if there is multiple entities with same ID? (e.g. climate and sensor)
                    # we should use platform + ID as key?
                    ent_id = entity.get(CONF_ID)
                    if ent_id not in entities:
                        entities[ent_id] = entity

    # ULTIMATE INTEGRATION: Force Power/Temp sensors if in cloud schema but not in auto-gen
    cloud_dps_raw = localtuya_data.get(DEVICE_CLOUD_DATA, {}).get("dps_data", {})
    _LOGGER.info(f"[TUYA-DEBUG] [ENTITY-GEN] Cloud schema DPs: {list(cloud_dps_raw)}")

    # ID mapping for forced sensors
    forced_mappings = {
        "18": {"name": "Current", "device_class": SensorDeviceClass.CURRENT, "scaling": 0.001, "unit": "mA"},
        "19": {"name": "Power", "device_class": SensorDeviceClass.POWER, "scaling": 0.1, "unit": "W"},
        "20": {"name": "Voltage", "device_class": SensorDeviceClass.VOLTAGE, "scaling": 0.1, "unit": "V"},
        "47": {"name": "Temperature", "device_class": SensorDeviceClass.TEMPERATURE, "scaling": 1.0, "unit": "°C"},
    }
    
    for dp_id, config in forced_mappings.items():
        if dp_id in dps_dict or dp_id in cloud_dps_raw:
            if dp_id not in entities:
                # ADVANCED CHECK: Use Cloud Schema Metadata (typeSpec)
                dp_schema = cloud_dps_raw.get(dp_id, {})
                type_spec_str = dp_schema.get("values", "")
                is_numeric = False
                
                # Check type in metadata
                if "Integer" in type_spec_str or "Value" in type_spec_str:
                    is_numeric = True
                    _LOGGER.info(f"[TUYA-DEBUG] DP {dp_id} confirmed numeric via Cloud Metadata (typeSpec)")
                else:
                    # Fallback to current value check if metadata is unclear
                    raw_val = dps_dict.get(dp_id)
                    if raw_val is None:
                        raw_val = dp_schema.get("value")
                    
                    try:
                        if raw_val is not None:
                            float(str(raw_val))
                            is_numeric = True
                            _LOGGER.info(f"[TUYA-DEBUG] DP {dp_id} confirmed numeric via Value fallback: {raw_val}")
                    except (ValueError, TypeError):
                        pass

                if not is_numeric:
                    _LOGGER.info(f"[TUYA-DEBUG] Skipping forced DP {dp_id} for {device_name}: not a numeric type")
                    continue

                _LOGGER.info(f"[TUYA-DEBUG] [ENTITY-FORCE] Forcing creation of sensor for DP {dp_id} for {device_name}")
                forced_entity = {
                    CONF_PLATFORM: Platform.SENSOR,
                    CONF_ID: int(dp_id),
                    CONF_FRIENDLY_NAME: f"{device_name} {config['name']}",
                    "device_class": config["device_class"],
                    "scaling": config["scaling"],
                    "unit_of_measurement": config["unit"],
                }
                entities[dp_id] = forced_entity

    _LOGGER.info(f"[TUYA-DEBUG] [ENTITY-GEN] Generated {len(entities)} entities for {device_name}")
    return list(entities.values())
def parse_enum(dp_code: Enum) -> str:
    """Get enum value if code type is enum"""
    try:
        parsed_dp_code = dp_code.value
    except:
        parsed_dp_code = dp_code

    return parsed_dp_code


def get_dp_values(dp: str, dps_data: dict, req_info: CLOUD_VALUE = None) -> dict:
    """Get DP Values"""
    if not dp or not dps_data:
        return

    dp_data = dps_data.get(dp, {})
    dp_values = dp_data.get("values")
    dp_type = dp_data.get("type", "").capitalize()

    if not dp_values or not (dp_values := json.loads(dp_values)):
        return

    # Some DPS doesn't have the type, in high level data.
    if not dp_type and (_type := dp_values.get("type")):
        dp_type = _type.capitalize()
        # Fix type names.
        dp_type = DPType.INTEGER if dp_type == "Value" else dp_type

    # Integer values: min, max, scale, step
    if dp_values and dp_type == DPType.INTEGER:
        # We only need the scaling factor, other values will be scaled from via later on.
        # dp_values["min"] = scale(dp_values.get("min"), val_scale)
        valid_type = req_info.prefer_type and req_info.prefer_type in (str, float, int)
        pref_type = req_info.prefer_type if valid_type else int
        val_scale = dp_values.get("scale", 1)
        dp_values["min"] = pref_type(dp_values.get("min"))
        dp_values["max"] = pref_type(dp_values.get("max"))
        dp_values["step"] = pref_type(dp_values.get("step"))

        pref_type = req_info.prefer_type if valid_type else float
        dp_values["scale"] = pref_type(scale(1, val_scale, float))

        # Scale if requested.
        if req_info.scale:
            for v in ("min", "max", "step"):
                value = dp_values[v]
                dp_values[v] = pref_type(scale(value, val_scale))

        return dp_values

    # ENUM Values: range: list of values.
    if dp_values and dp_type == DPType.ENUM:
        range_values = dp_values.get("range", [])

        dp_values["min"] = range_values[0] if range_values else 0  # first value
        dp_values["max"] = range_values[-1] if range_values else 0  # Last value
        dp_values["range"] = convert_list(range_values, req_info)
        return dp_values

    # Sensors don't have type
    if dp_values and not dp_type:
        # we need scaling factor for sensors.
        if "scale" in dp_values:
            dp_values["scale"] = scale(1, dp_values["scale"], float)
            return dp_values


def scale(value: int, scale: int, _type: type = int) -> float:
    """Return scaled value."""
    value = _type(value) / (10**scale)
    if value.is_integer():
        value = int(value)
    return value


def convert_list(_list: list, req_info: CLOUD_VALUE):
    """Return list to dict values."""
    if not _list:
        return []

    prefer_type = req_info.prefer_type

    if prefer_type == str:
        # Return str "value1,value2,value3"
        to_str = ",".join(str(v) for v in _list)
        return to_str

    if prefer_type == dict:
        # Return dict {value_1: Value 1, value_2: Value 2, value_3: Value 3}
        to_dict = {}
        for k in _list:
            if k.lower() in req_info.remap_values:
                k_name = req_info.remap_values.get(k.lower())
            else:
                # k_name = k.replace("_", " ").capitalize()  # Default name
                k_name = k  # Default name
                if isinstance(req_info.default_value, dict):
                    k_name = req_info.default_value.get(k, k_name)

            if req_info.reverse_dict:
                to_dict.update({k_name: k})
            else:
                to_dict.update({k: k_name})
        return to_dict

    # otherwise return prefer type list
    return _list


def convert_to_kelvin(value):
    """Convert Tuya color temperature to kelvin"""
    # Given data points
    v0, k0 = 0, 2700  # (0, 2700)
    v1, k1 = 1000, 6500  # (1000, 6500)

    # Calculate slope (m) and y-intercept (b) using the given points
    m = (k1 - k0) / (v1 - v0)
    b = k0 - m * v0

    # Use the linear equation to calculate the color temperature (K)
    kelvin = m * value + b

    return kelvin
