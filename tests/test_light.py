"""Test for localtuya."""

from . import *
from custom_components.localtuya.light import (
    LocalTuyaLight,
    DOMAIN as PLATFORM_DOMAIN,
    ColorMode,
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


async def test_light_work_mode_written_only_when_it_changes():
    """work_mode must not ride along on a write that does not change it.

    Some devices acknowledge a CONTROL frame that carries work_mode next to
    brightness/color_temp and then silently discard the whole payload, so the
    light never dims. Sending only the DPs that actually change keeps those
    devices working, and still switches work_mode when the mode really differs.
    """
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaLight)
    entity_1, *_ = get_entites(device)

    device.status_updated(DPS_STATUS.copy())
    assert entity_1.is_white_mode

    # Already in white mode: a brightness change must send brightness only.
    device.set_dps = AsyncMock()
    await entity_1.async_turn_on(brightness=128)
    states = device.set_dps.call_args.args[0]
    assert "22" in states
    assert "21" not in states

    # Still in white mode: a color temperature change must not re-send work_mode.
    device.set_dps = AsyncMock()
    await entity_1.async_turn_on(color_temp_kelvin=4000)
    states = device.set_dps.call_args.args[0]
    assert "23" in states
    assert "21" not in states

    # Coming from another mode, work_mode still has to be written.
    device.status_updated({"21": "colour"})
    device.set_dps = AsyncMock()
    await entity_1.async_turn_on(color_temp_kelvin=4000)
    states = device.set_dps.call_args.args[0]
    assert states.get("21") == "white"
