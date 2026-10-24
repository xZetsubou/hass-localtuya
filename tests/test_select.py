"""Test for localtuya."""

from . import *
from custom_components.localtuya.select import (
    LocalTuyaSelect,
    DOMAIN as PLATFORM_DOMAIN,
)

CONFIG = {
    DEVICE_NAME: {
        **DEVICE_CONFIG,
        "entities": [
            {
                "entity_category": "config",
                "friendly_name": "Motor Direction",
                "icon": "mdi:swap-vertical",
                "id": "5",
                "is_passive_entity": False,
                "platform": PLATFORM_DOMAIN,
                "restore_on_reconnect": False,
                "select_options": {"back": "Back", "forward": "Forward"},
            }
        ],
    }
}

DPS_STATUS = {"5": "back"}


async def test_lock():
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaSelect)
    entities: list[LocalTuyaSelect] = get_entites(device)

    assert len(entities) > 0
    entity_1, *_ = entities
    assert type(entity_1) is LocalTuyaSelect

    device.status_updated(DPS_STATUS)
    assert (
        entity_1.state in CONFIG[DEVICE_NAME]["entities"][0]["select_options"].values()
    )


async def test_integer_options_keep_numeric_order_and_write_integer():
    config = {
        DEVICE_NAME: {
            **DEVICE_CONFIG,
            "entities": [
                {
                    **CONFIG[DEVICE_NAME]["entities"][0],
                    "select_options": {"0": "Warm", "1000": "Cool", "500": "Neutral"},
                    "select_dps_type": "int",
                }
            ],
        }
    }
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaSelect)
    select = get_entites(device)[0]
    device.set_dp = AsyncMock()

    assert select.options == ["Warm", "Neutral", "Cool"]
    await select.async_select_option("Cool")
    device.set_dp.assert_awaited_once_with(1000, "5")

    device.status_updated({"5": 500})
    assert select.current_option == "Neutral"
    device.set_dp.reset_mock()
    await select.async_select_option("Cool")
    device.set_dp.assert_awaited_once_with(1000, "5")

    device.status_updated({"5": "500"})
    device.set_dp.reset_mock()
    await select.async_select_option("Cool")
    device.set_dp.assert_awaited_once_with(1000, "5")


async def test_numeric_string_options_remain_strings_before_status():
    config = {
        DEVICE_NAME: {
            **DEVICE_CONFIG,
            "entities": [
                {
                    **CONFIG[DEVICE_NAME]["entities"][0],
                    "select_options": {"0": "Off", "1": "On"},
                }
            ],
        }
    }
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaSelect)
    select = get_entites(device)[0]
    device.set_dp = AsyncMock()

    await select.async_select_option("On")
    device.set_dp.assert_awaited_once_with("1", "5")

    device.status_updated({"5": "0"})
    device.set_dp.reset_mock()
    await select.async_select_option("On")
    device.set_dp.assert_awaited_once_with("1", "5")

    device.status_updated({"5": 0})
    device.set_dp.reset_mock()
    await select.async_select_option("On")
    device.set_dp.assert_awaited_once_with(1, "5")
