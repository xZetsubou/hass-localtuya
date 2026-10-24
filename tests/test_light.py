"""Test for localtuya."""

from . import *
from custom_components.localtuya.light import (
    LocalTuyaLight,
    DOMAIN as PLATFORM_DOMAIN,
    ColorMode,
    LightEntityFeature,
)

CONFIG = {
    DEVICE_NAME: {
        **DEVICE_CONFIG,
        "entities": [
            {
                "id": "20",
                "color_mode": "21",
                "brightness": "22",
                "color_temp": "23",
                "color": "24",
                "scene": "25",
                "brightness_lower": 0,
                "brightness_upper": 1000,
                "color_temp_min_kelvin": 2700,
                "color_temp_max_kelvin": 6500,
                "color_temp_reverse": False,
                "music_mode": True,
                "friendly_name": None,
                "icon": "",
                "entity_category": "None",
                "platform": "light",
            }
        ],
    }
}

DPS_STATUS = {
    "20": True,
    "21": "white",
    "22": 600,
    "23": 1000,
    "24": "000403e8000c",
    "25": "010e0d000084000003e800000000",
}
ENC_COLOR = "0319090087db1c"
BLE_COLOR = "0319090087db1c"


async def test_light():
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaLight)
    entities: list[LocalTuyaLight] = get_entites(device)

    assert len(entities) > 0
    entity_1, *_ = entities
    assert type(entity_1) is LocalTuyaLight

    status = DPS_STATUS.copy()
    device.status_updated(status)

    assert entity_1.state == "on"
    assert entity_1.brightness is not None
    assert entity_1.is_white_mode
    assert entity_1.color_temp_kelvin is not None

    device.status_updated({"22": 1000})
    assert entity_1.brightness == 255
    device.status_updated({"22": 0})
    assert entity_1.brightness == 0

    device.status_updated({"21": "colour"})
    assert entity_1.hs_color is not None

    device.status_updated({"24": ENC_COLOR})
    sat, brightness = entity_1.hs_color
    assert sat < 360 and brightness <= 100

    device.status_updated({"21": "music"})
    assert entity_1.is_music_mode

    device.status_updated({"21": "scene"})
    assert entity_1.effect is not None
    assert entity_1.is_scene_mode

    # Bluetooth
    # device.status_updated({"21": "colour", "24": "AHhkZA==", "25": ""})


async def test_scene_effects_for_write_only_light_without_scene_status():
    config = {
        DEVICE_NAME: {
            **DEVICE_CONFIG,
            "entities": [{**CONFIG[DEVICE_NAME]["entities"][0], "music_mode": False}],
        }
    }
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaLight)
    light = get_entites(device)[0]

    light._write_only = True
    light.connection_made()
    assert "Good Night" in light.effect_list
    assert light.supported_features & LightEntityFeature.EFFECT


async def test_explicit_scenes_without_scene_status():
    config = {
        DEVICE_NAME: {
            **DEVICE_CONFIG,
            "entities": [
                {
                    **CONFIG[DEVICE_NAME]["entities"][0],
                    "music_mode": False,
                    "scene_values": {"scene_data": "Sleep"},
                }
            ],
        }
    }
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaLight)
    light = get_entites(device)[0]

    light.connection_made()
    assert "Sleep" in light.effect_list
    assert light.supported_features & LightEntityFeature.EFFECT


async def test_command_only_scene_dp_and_late_status():
    config = {
        DEVICE_NAME: {
            **DEVICE_CONFIG,
            "entities": [{**CONFIG[DEVICE_NAME]["entities"][0], "music_mode": False}],
        }
    }
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaLight)
    light = get_entites(device)[0]
    light.connection_made()

    assert "Night 1" in light.effect_list
    assert light.supported_features & LightEntityFeature.EFFECT
    device.set_dps = AsyncMock()
    await light.async_turn_on(effect="Night 1")
    assert device.set_dps.await_args.args[0]["25"] == "000e0d0000000000000000c80000"

    light._status.update({"20": True, "21": "scene", "25": DPS_STATUS["25"]})
    light.status_updated()

    assert light.effect_list.count("Night 1") == 1
    assert light.supported_features & LightEntityFeature.EFFECT
    device.set_dps = AsyncMock()
    await light.async_turn_on(effect="Night 1")
    assert device.set_dps.await_args.args[0]["25"] == "000e0d0000000000000000c80000"


async def test_color_temperature_sends_configured_mode_without_mode_status():
    config = {
        DEVICE_NAME: {
            **DEVICE_CONFIG,
            "entities": [
                {
                    **CONFIG[DEVICE_NAME]["entities"][0],
                    "music_mode": False,
                    "brightness": None,
                    "brightness_lower": 100,
                }
            ],
        }
    }
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaLight)
    light = get_entites(device)[0]
    device.status_updated({"20": True, "23": 100})
    device.set_dps = AsyncMock()

    assert light.color_temp_kelvin == 2700
    await light.async_turn_on(color_temp_kelvin=2700)
    device.set_dps.assert_awaited_once_with({"23": 100, "21": "white"})

    device.set_dps.reset_mock()
    await light.async_turn_on(color_temp_kelvin=6500)

    device.set_dps.assert_awaited_once_with({"23": 1000, "21": "white"})
