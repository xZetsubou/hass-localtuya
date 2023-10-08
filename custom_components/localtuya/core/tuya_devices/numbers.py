"""
    This a file contains available tuya data
    https://developer.tuya.com/en/docs/iot/standarddescription?id=K9i5ql6waswzq
    Credits: official HA Tuya integration.
    Modified by: xZetsubou

    #TODO get values using "Get the instructions set by category"
"""
from homeassistant.components.number import NumberDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfTime

from .base import DPCode, LocalTuyaEntity, CONF_DEVICE_CLASS, EntityCategory
from ...const import CONF_MIN_VALUE, CONF_MAX_VALUE, CONF_STEPSIZE_VALUE


def localtuya_numbers(_min, _max, _step=1, native_unit=None) -> dict:
    """Will return dict with CONF MIN AND CONF MAX"""
    data = {CONF_MIN_VALUE: _min, CONF_MAX_VALUE: _max, CONF_STEPSIZE_VALUE: _step}

    if native_unit:
        pass
        # data.update({"native_unit": native_unit})

    return data


NUMBERS: dict[LocalTuyaEntity] = {
    # Multi-functional Sensor
    # https://developer.tuya.com/en/docs/iot/categorydgnbj?id=Kaiuz3yorvzg3
    "dgnbj": (
        LocalTuyaEntity(
            id=DPCode.ALARM_TIME,
            name="Time",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 60),
        ),
    ),
    # Smart Kettle
    # https://developer.tuya.com/en/docs/iot/fbh?id=K9gf484m21yq7
    "bh": (
        LocalTuyaEntity(
            id=DPCode.TEMP_SET,
            name="Temperature",
            device_class=NumberDeviceClass.TEMPERATURE,
            icon="mdi:thermometer",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 100),
        ),
        LocalTuyaEntity(
            id=DPCode.TEMP_SET_F,
            name="Temperature",
            device_class=NumberDeviceClass.TEMPERATURE,
            icon="mdi:thermometer",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(32, 212),
        ),
        LocalTuyaEntity(
            id=DPCode.TEMP_BOILING_C,
            name="Temperature After Boiling",
            device_class=NumberDeviceClass.TEMPERATURE,
            icon="mdi:thermometer",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 100),
        ),
        LocalTuyaEntity(
            id=DPCode.TEMP_BOILING_F,
            name="Temperature After Boiling",
            device_class=NumberDeviceClass.TEMPERATURE,
            icon="mdi:thermometer",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(32, 212),
        ),
        LocalTuyaEntity(
            id=DPCode.WARM_TIME,
            name="Heat preservation time",
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 360),
        ),
    ),
    # Smart Pet Feeder
    # https://developer.tuya.com/en/docs/iot/categorycwwsq?id=Kaiuz2b6vydld
    "cwwsq": (
        LocalTuyaEntity(
            id=DPCode.MANUAL_FEED,
            name="Feed",
            icon="mdi:bowl",
            custom_configs=localtuya_numbers(1, 12),
        ),
        LocalTuyaEntity(
            id=DPCode.VOICE_TIMES,
            name="Voice prompt",
            icon="mdi:microphone",
            custom_configs=localtuya_numbers(0, 10),
        ),
    ),
    # Human Presence Sensor
    # https://developer.tuya.com/en/docs/iot/categoryhps?id=Kaiuz42yhn1hs
    "hps": (
        LocalTuyaEntity(
            id=DPCode.SENSITIVITY,
            name="sensitivity",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 9),
        ),
        LocalTuyaEntity(
            id=DPCode.NEAR_DETECTION,
            name="Near Detection CM",
            icon="mdi:signal-distance-variant",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 1000),
        ),
        LocalTuyaEntity(
            id=DPCode.FAR_DETECTION,
            name="Far Detection CM",
            icon="mdi:signal-distance-variant",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 1000),
        ),
    ),
    # Coffee maker
    # https://developer.tuya.com/en/docs/iot/categorykfj?id=Kaiuz2p12pc7f
    "kfj": (
        LocalTuyaEntity(
            id=DPCode.WATER_SET,
            name="Water Level",
            icon="mdi:cup-water",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 500),
        ),
        LocalTuyaEntity(
            id=DPCode.TEMP_SET,
            name="Temperature",
            device_class=NumberDeviceClass.TEMPERATURE,
            icon="mdi:thermometer",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 100),
        ),
        LocalTuyaEntity(
            id=DPCode.WARM_TIME,
            name="Heat preservation time",
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 1440),
        ),
        LocalTuyaEntity(
            id=DPCode.POWDER_SET,
            name="Powder",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 24),
        ),
    ),
    # Switch
    # https://developer.tuya.com/en/docs/iot/s?id=K9gf7o5prgf7s
    "kg": (
        LocalTuyaEntity(
            id=DPCode.COUNTDOWN_1,
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            name="Switch 1 Timer",
            custom_configs=localtuya_numbers(0, 86400, 1, UnitOfTime.SECONDS),
        ),
        LocalTuyaEntity(
            id=DPCode.COUNTDOWN_2,
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            name="Switch 2 Timer",
            custom_configs=localtuya_numbers(0, 86400, 1, UnitOfTime.SECONDS),
        ),
        LocalTuyaEntity(
            id=DPCode.COUNTDOWN_3,
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            name="Switch 3 Timer",
            custom_configs=localtuya_numbers(0, 86400, 1, UnitOfTime.SECONDS),
        ),
        LocalTuyaEntity(
            id=DPCode.COUNTDOWN_4,
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            name="Switch 4 Timer",
            custom_configs=localtuya_numbers(0, 86400, 1, UnitOfTime.SECONDS),
        ),
        LocalTuyaEntity(
            id=DPCode.COUNTDOWN_5,
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            name="Switch 5 Timer",
            custom_configs=localtuya_numbers(0, 86400, 1, UnitOfTime.SECONDS),
        ),
        LocalTuyaEntity(
            id=DPCode.COUNTDOWN_6,
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            name="Switch 6 Timer",
            custom_configs=localtuya_numbers(0, 86400, 1, UnitOfTime.SECONDS),
        ),
        LocalTuyaEntity(
            id=DPCode.COUNTDOWN_USB1,
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            name="USB1 Timer",
            custom_configs=localtuya_numbers(0, 86400, 1, UnitOfTime.SECONDS),
        ),
        LocalTuyaEntity(
            id=DPCode.COUNTDOWN_USB2,
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            name="USB2 Timer",
            custom_configs=localtuya_numbers(0, 86400, 1, UnitOfTime.SECONDS),
        ),
        LocalTuyaEntity(
            id=DPCode.COUNTDOWN_USB3,
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            name="USB3 Timer",
            custom_configs=localtuya_numbers(0, 86400, 1, UnitOfTime.SECONDS),
        ),
        LocalTuyaEntity(
            id=DPCode.COUNTDOWN_USB4,
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            name="USB4 Timer",
            custom_configs=localtuya_numbers(0, 86400, 1, UnitOfTime.SECONDS),
        ),
        LocalTuyaEntity(
            id=DPCode.COUNTDOWN_USB5,
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            name="USB5 Timer",
            custom_configs=localtuya_numbers(0, 86400, 1, UnitOfTime.SECONDS),
        ),
        LocalTuyaEntity(
            id=DPCode.COUNTDOWN_USB6,
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            name="USB6 Timer",
            custom_configs=localtuya_numbers(0, 86400, 1, UnitOfTime.SECONDS),
        ),
        LocalTuyaEntity(
            id=DPCode.COUNTDOWN,
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            name="Switch Timer",
            custom_configs=localtuya_numbers(0, 86400, 1, UnitOfTime.SECONDS),
        ),
        LocalTuyaEntity(
            id=DPCode.COUNTDOWN_USB,
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            name="Switch Timer",
            custom_configs=localtuya_numbers(0, 86400, 1, UnitOfTime.SECONDS),
        ),
    ),
    # Sous Vide Cooker
    # https://developer.tuya.com/en/docs/iot/categorymzj?id=Kaiuz2vy130ux
    "mzj": (
        LocalTuyaEntity(
            id=DPCode.COOK_TEMPERATURE,
            name="Cooking temperature",
            icon="mdi:thermometer",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 500),
        ),
        LocalTuyaEntity(
            id=DPCode.COOK_TIME,
            name="Cooking time",
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 360, 1, UnitOfTime.MINUTES),
        ),
        LocalTuyaEntity(
            id=DPCode.CLOUD_RECIPE_NUMBER,
            name="Cloud Recipes",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 999999),
        ),
        LocalTuyaEntity(
            id=DPCode.APPOINTMENT_TIME,
            name="Appointment time",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 360),
        ),
    ),
    # Robot Vacuum
    # https://developer.tuya.com/en/docs/iot/fsd?id=K9gf487ck1tlo
    "sd": (
        LocalTuyaEntity(
            id=DPCode.VOLUME_SET,
            name="volume",
            icon="mdi:volume-high",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 100),
        ),
    ),
    # Siren Alarm
    # https://developer.tuya.com/en/docs/iot/categorysgbj?id=Kaiuz37tlpbnu
    "sgbj": (
        LocalTuyaEntity(
            id=DPCode.ALARM_TIME,
            name="Alarm duration",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(1, 60),
        ),
    ),
    # Smart Camera
    # https://developer.tuya.com/en/docs/iot/categorysp?id=Kaiuz35leyo12
    "sp": (
        LocalTuyaEntity(
            id=DPCode.BASIC_DEVICE_VOLUME,
            name="volume",
            icon="mdi:volume-high",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(1, 10),
        ),
        LocalTuyaEntity(
            id=DPCode.FLOODLIGHT_LIGHTNESS,
            name="Floodlight brightness",
            icon="mdi:brightness-6",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(1, 100),
        ),
    ),
    # Dimmer Switch
    # https://developer.tuya.com/en/docs/iot/categorytgkg?id=Kaiuz0ktx7m0o
    "tgkg": (
        LocalTuyaEntity(
            id=DPCode.BRIGHTNESS_MIN_1,
            name="minimum_brightness",
            icon="mdi:lightbulb-outline",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(10, 1000),
        ),
        LocalTuyaEntity(
            id=DPCode.BRIGHTNESS_MAX_1,
            name="maximum_brightness",
            icon="mdi:lightbulb-on-outline",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(10, 1000),
        ),
        LocalTuyaEntity(
            id=DPCode.BRIGHTNESS_MIN_2,
            name="minimum_brightness_2",
            icon="mdi:lightbulb-outline",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(10, 1000),
        ),
        LocalTuyaEntity(
            id=DPCode.BRIGHTNESS_MAX_2,
            name="maximum_brightness_2",
            icon="mdi:lightbulb-on-outline",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(10, 1000),
        ),
        LocalTuyaEntity(
            id=DPCode.BRIGHTNESS_MIN_3,
            name="minimum_brightness_3",
            icon="mdi:lightbulb-outline",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(10, 1000),
        ),
        LocalTuyaEntity(
            id=DPCode.BRIGHTNESS_MAX_3,
            name="maximum_brightness_3",
            icon="mdi:lightbulb-on-outline",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(10, 1000),
        ),
    ),
    # Dimmer Switch
    # https://developer.tuya.com/en/docs/iot/categorytgkg?id=Kaiuz0ktx7m0o
    "tgq": (
        LocalTuyaEntity(
            id=DPCode.BRIGHTNESS_MIN_1,
            name="minimum_brightness",
            icon="mdi:lightbulb-outline",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(10, 1000),
        ),
        LocalTuyaEntity(
            id=DPCode.BRIGHTNESS_MAX_1,
            name="maximum_brightness",
            icon="mdi:lightbulb-on-outline",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(10, 1000),
        ),
        LocalTuyaEntity(
            id=DPCode.BRIGHTNESS_MIN_2,
            name="minimum_brightness_2",
            icon="mdi:lightbulb-outline",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(10, 1000),
        ),
        LocalTuyaEntity(
            id=DPCode.BRIGHTNESS_MAX_2,
            name="maximum_brightness_2",
            icon="mdi:lightbulb-on-outline",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(10, 1000),
        ),
    ),
    # Vibration Sensor
    # https://developer.tuya.com/en/docs/iot/categoryzd?id=Kaiuz3a5vrzno
    "zd": (
        LocalTuyaEntity(
            id=DPCode.SENSITIVITY,
            name="Sensitivity",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 9),
        ),
    ),
    # Fingerbot
    # arm_down_percent: "{\"min\":50,\"max\":100,\"scale\":0,\"step\":1}"
    # arm_up_percent: "{\"min\":0,\"max\":50,\"scale\":0,\"step\":1}"
    # click_sustain_time: "values": "{\"unit\":\"s\",\"min\":2,\"max\":10,\"scale\":0,\"step\":1}"
    "szjqr": (
        LocalTuyaEntity(
            id=DPCode.ARM_DOWN_PERCENT,
            name="Move Down",
            icon="mdi:arrow-down-bold",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(50, 100, 1, PERCENTAGE),
        ),
        LocalTuyaEntity(
            id=DPCode.ARM_UP_PERCENT,
            name="Move UP",
            icon="mdi:arrow-up-bold",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(0, 50, 1, PERCENTAGE),
        ),
        LocalTuyaEntity(
            id=DPCode.CLICK_SUSTAIN_TIME,
            name="Down Delay",
            icon="mdi:timer",
            entity_category=EntityCategory.CONFIG,
            custom_configs=localtuya_numbers(2, 10),
        ),
    ),
    # Fan
    # https://developer.tuya.com/en/docs/iot/categoryfs?id=Kaiuz1xweel1c
    "fs": (
        LocalTuyaEntity(
            id=DPCode.TEMP,
            name="Temperature",
            device_class=NumberDeviceClass.TEMPERATURE,
            icon="mdi:thermometer-lines",
        ),
    ),
    # Humidifier
    # https://developer.tuya.com/en/docs/iot/categoryjsq?id=Kaiuz1smr440b
    "jsq": (
        LocalTuyaEntity(
            id=DPCode.TEMP_SET,
            name="Temperature",
            device_class=NumberDeviceClass.TEMPERATURE,
            icon="mdi:thermometer-lines",
            custom_configs=localtuya_numbers(0, 50),
        ),
        LocalTuyaEntity(
            id=DPCode.TEMP_SET_F,
            name="Temperature",
            device_class=NumberDeviceClass.TEMPERATURE,
            icon="mdi:thermometer-lines",
            custom_configs=localtuya_numbers(32, 212, 1),
        ),
    ),
    # Thermostat
    "wk": (
        LocalTuyaEntity(
            id=DPCode.TEMPCOMP,
            name="Calibration offset",
            custom_configs=localtuya_numbers(-9, 9),
        ),
        LocalTuyaEntity(
            id=DPCode.TEMPACTIVATE,
            name="Calibration swing",
            custom_configs=localtuya_numbers(1, 9),
        ),
    ),
}
NUMBERS["cz"] = NUMBERS["kg"]
NUMBERS["pc"] = NUMBERS["kg"]