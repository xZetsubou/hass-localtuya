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


async def eave_light(mode="020f01f403e8"):
    config = {
        DEVICE_NAME: {
            **DEVICE_CONFIG,
            "entities": [
                {
                    "id": "20",
                    "platform": "light",
                    "scene": "106",
                    "color_mode": "106",
                    "color": "104",
                    "brightness_lower": 29,
                    "brightness_upper": 1000,
                    CONF_SCENE_PROFILE: ETERNITY_EAVE,
                }
            ],
        }
    }
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaLight)
    light = get_entites(device)[0]
    device.status_updated({"20": True, "106": mode, "104": "0b080d01156934"})
    device.set_dps = AsyncMock()
    return device, light


async def test_eave_scene_slider_preserves_effect_and_reports_written_brightness():
    device, light = await eave_light()
    await light.async_turn_on(brightness=128)
    device.set_dps.assert_awaited_once_with({"106": "020f01f401f6"})
    device.status_updated({"106": "020f01f401f6"})
    assert light.brightness == 128
    assert light.effect == "Halloween"


async def test_eave_color_uses_static_diy_mode_and_slider_preserves_rgb():
    device, light = await eave_light()
    await light.async_turn_on(hs_color=(120, 100), brightness=128)
    device.set_dps.assert_awaited_once_with({"106": "6500000001f60#0000ff00"})
    device.status_updated({"106": "6500000001f60#0000ff00"})
    assert light.hs_color == [120, 100]
    assert light.brightness == 128
    assert light.effect is None
    device.set_dps.reset_mock()
    await light.async_turn_on(brightness=51)
    device.set_dps.assert_awaited_once_with({"106": "6500000000c80#0000ff00"})
    device.status_updated({"106": "6500000000c80#0000ff00"})
    assert light.brightness == 51
    assert light.hs_color == [120, 100]


@pytest.mark.parametrize("brightness", [1, 5, 51, 128, 204, 255])
async def test_eave_initial_effect_brightness_uses_new_effect(brightness):
    device, light = await eave_light("6500000000c80#00ff0000")
    value = round(brightness * 1000 / 255)
    expected = f"3301012c{value:04x}"
    await light.async_turn_on(effect="Bubbly", brightness=brightness)
    device.set_dps.assert_awaited_once_with({"106": expected})
    device.status_updated({"106": expected})
    assert light.brightness == brightness
    assert light.effect == "Bubbly"


async def test_eave_color_selection_inherits_brightness():
    device, light = await eave_light("020f01f400c8")
    await light.async_turn_on(hs_color=(240, 100))
    device.set_dps.assert_awaited_once_with({"106": "6500000000c80#000000ff"})
    device.status_updated({"106": "6500000000c80#000000ff"})
    assert light.brightness == 51
    assert light.hs_color == [240, 100]


async def test_eave_diy_slider_preserves_speed_and_palette():
    mode = "650c01f403e81#0019ff19#00ff4600"
    device, light = await eave_light(mode)
    await light.async_turn_on(brightness=128)
    expected = "650c01f401f61#0019ff19#00ff4600"
    device.set_dps.assert_awaited_once_with({"106": expected})
    device.status_updated({"106": expected})
    assert light.brightness == 128
    assert light.effect is None
    assert light.is_scene_mode


async def test_eave_power_preserves_mode():
    device, light = await eave_light("6500000000c80#0000ff00")
    device.set_dp = AsyncMock()
    await light.async_turn_off()
    device.set_dp.assert_awaited_once_with(False, "20")
    device.status_updated({"20": False})
    await light.async_turn_on()
    device.set_dps.assert_awaited_once_with({"20": True})
    device.status_updated({"20": True})
    assert light.is_on
    assert light.brightness == 51
    assert light.hs_color == [120, 100]


@pytest.mark.parametrize("mode", [None, "colour", "garbage", "6500000003e81#00ff0000"])
async def test_eave_unknown_mode_does_not_parse_dp104_or_write_invalid_dps(mode):
    device, light = await eave_light(mode)
    assert light.brightness is None
    await light.async_turn_on(brightness=128)
    device.set_dps.assert_awaited_once_with({})
    device.set_dps.reset_mock()
    await light.async_turn_on(hs_color=(0, 0), brightness=255)
    device.set_dps.assert_awaited_once_with({"106": "6500000003e80#00ffffff"})


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
