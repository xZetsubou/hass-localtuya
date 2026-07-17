"""Test for localtuya."""

from unittest.mock import AsyncMock
from . import *
from custom_components.localtuya.number import (
    LocalTuyaNumber,
    DOMAIN as PLATFORM_DOMAIN,
)

CONFIG = {
    DEVICE_NAME: {
        **DEVICE_CONFIG,
        "entities": [
            {
                "entity_category": "None",
                "friendly_name": f"{PLATFORM_DOMAIN} 1",
                "icon": "",
                "id": "1",
                "scaling": 0.01,
                "platform": PLATFORM_DOMAIN,
                "restore_on_reconnect": False,
            }
        ],
    }
}

CONFIG_WITH_OFFSET = {
    DEVICE_NAME: {
        **DEVICE_CONFIG,
        "entities": [
            {
                "entity_category": "None",
                "friendly_name": f"{PLATFORM_DOMAIN} 2",
                "icon": "",
                "id": "2",
                "min_value": 0.0,
                "max_value": 100.0,
                "step_size": 1.0,
                "scaling": 0.1,
                "offset": 10.0,
                "platform": PLATFORM_DOMAIN,
                "restore_on_reconnect": False,
            }
        ],
    }
}

DPS_STATUS = {"1": 500}
DPS_STATUS_WITH_OFFSET = {"2": 50}


async def test_lock():
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaNumber)
    entities: list[LocalTuyaNumber] = get_entites(device)

    assert len(entities) > 0
    entity_1, *_ = entities
    assert type(entity_1) is LocalTuyaNumber

    device.status_updated(DPS_STATUS)
    assert entity_1.native_value == 5


async def test_scaling_and_offset():
    device = await init(CONFIG_WITH_OFFSET, PLATFORM_DOMAIN, LocalTuyaNumber)
    entities: list[LocalTuyaNumber] = get_entites(device)

    assert len(entities) > 0
    entity_1, *_ = entities
    assert type(entity_1) is LocalTuyaNumber

    # Verify scaled and offset limits
    # min: 0.0 * 0.1 + 10.0 = 10.0
    assert entity_1.native_min_value == 10.0
    # max: 100.0 * 0.1 + 10.0 = 20.0
    assert entity_1.native_max_value == 20.0
    # step size: 1.0 * 0.1 = 0.1 (not offset)
    assert entity_1.native_step == 0.1

    # Verify scaling + offset read
    # 50 * 0.1 + 10.0 = 15.0
    device.status_updated(DPS_STATUS_WITH_OFFSET)
    assert entity_1.native_value == 15.0

    # Verify setting value back: (15.0 - 10.0) / 0.1 = 50
    device.set_dp = AsyncMock()
    await entity_1.async_set_native_value(15.0)
    device.set_dp.assert_called_once_with(50, "2")

    # Verify setting value back: (20.0 - 10.0) / 0.1 = 100
    device.set_dp.reset_mock()
    await entity_1.async_set_native_value(20.0)
    device.set_dp.assert_called_once_with(100, "2")
