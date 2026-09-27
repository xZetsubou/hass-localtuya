"""Test for localtuya."""

from . import *
from custom_components.localtuya.light import (
    LocalTuyaLight,
    DOMAIN as PLATFORM_DOMAIN,
    ColorMode,
)
from custom_components.localtuya.const import CONF_SCENE_PROFILE
from custom_components.localtuya.scene_profiles import ETERNITY_EAVE
from unittest.mock import AsyncMock

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


async def test_eternity_eave_effects_follow_dp106_without_color_mode():
    config = {
        DEVICE_NAME: {
            **DEVICE_CONFIG,
            "entities": [
                {
                    "id": "20",
                    "platform": "light",
                    "scene": "106",
                    CONF_SCENE_PROFILE: ETERNITY_EAVE,
                }
            ],
        }
    }
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaLight)
    light = get_entites(device)[0]
    device.status_updated({"20": True, "106": "020f01f403e8"})
    assert "Halloween" in light.effect_list
    assert light.effect == "Halloween"
    device.status_updated({"106": "020f000a000a"})
    assert light.effect == "Halloween"  # Changed speed and brightness
    device.status_updated({"106": "650c01f403e81#0019ff19#00ff4600"})
    assert light.effect is None  # Unknown DIY mode must not be mislabeled

    device.set_dps = AsyncMock()
    await light.async_turn_on(effect="Bubbly")
    device.set_dps.assert_awaited_once_with({"106": "3301012c03e8"})
