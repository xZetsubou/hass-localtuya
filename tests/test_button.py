"""Test for localtuya."""

from . import *
from unittest.mock import call, patch
from custom_components.localtuya.button import (
    LocalTuyaButton,
    DOMAIN as PLATFORM_DOMAIN,
)

CONFIG = {
    DEVICE_NAME: {
        **DEVICE_CONFIG,
        "entities": [
            {
                "entity_category": "None",
                "friendly_name": "Button 1",
                "icon": "",
                "id": "1",
                "is_passive_entity": False,
                "platform": "button",
                "restore_on_reconnect": False,
            }
        ],
    }
}

DPS_STATUS = {"1": True, "2": False}


async def test_button():
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaButton)
    entities: list[LocalTuyaButton] = get_entites(device)

    assert len(entities) > 0
    entity_1, *_ = entities
    assert type(entity_1) is LocalTuyaButton

    device.status_updated(DPS_STATUS)

    assert entity_1.state == None

    device.set_dp = AsyncMock()
    await entity_1.async_press()
    device.set_dp.assert_awaited_once_with(True, "1")


async def test_button_can_send_integer_press_value():
    config = {
        DEVICE_NAME: {
            **DEVICE_CONFIG,
            "entities": [
                {
                    **CONFIG[DEVICE_NAME]["entities"][0],
                    "id": "23",
                    "button_press_value": 1000,
                }
            ],
        }
    }
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaButton)
    button = get_entites(device)[0]
    device.set_dp = AsyncMock()

    await button.async_press()
    await button.async_press()
    assert device.set_dp.await_args_list == [call(1000, "23"), call(1000, "23")]


async def test_button_logs_reported_dp_changes():
    config = {
        DEVICE_NAME: {
            **DEVICE_CONFIG,
            "entities": [
                {
                    **CONFIG[DEVICE_NAME]["entities"][0],
                    "id": "23",
                    "button_log_dp_changes": True,
                }
            ],
        }
    }
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaButton)
    button = get_entites(device)[0]
    button.entity_id = "button.test_cycle_light_color"

    with patch("custom_components.localtuya.button.log_entry") as log:
        for value in (1000, 0, 500, 500, 1000):
            device.status_updated({"23": value})

    assert log.call_count == 3
    assert all(
        args.kwargs["entity_id"] == button.entity_id for args in log.call_args_list
    )
    assert all(args.args[2] == "reported a change" for args in log.call_args_list)
    assert all("domain" not in args.kwargs for args in log.call_args_list)
