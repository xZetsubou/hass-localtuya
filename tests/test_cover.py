"""Test for localtuya."""

from . import *
from custom_components.localtuya.cover import (
    LocalTuyaCover,
    DOMAIN as PLATFORM_DOMAIN,
    STATE_OPENING,
    STATE_CLOSING,
    STATE_STOPPED,
    STATE_SET_CMD,
    STATE_SET_OPENING,
    STATE_SET_CLOSING,
)

CONFIG = {
    DEVICE_NAME: {
        **DEVICE_CONFIG,
        "entities": [
            {
                "commands_set": "open_close_stop",
                "current_position_dp": "3",
                "entity_category": "None",
                "friendly_name": "Curtain",
                "icon": "",
                "id": "1",
                "platform": "cover",
                "position_inverted": False,
                "positioning_mode": "position",
                "set_position_dp": "2",
                "span_time": 25.0,
            },
        ],
    }
}

DPS_STATUS = {"1": "stop", "2": 80, "3": 80}


async def test_cover():
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaCover)
    entities: list[LocalTuyaCover] = get_entites(device)

    assert len(entities) > 0
    entity_1, *_ = entities
    entity_1.schedule_update_ha_state = lambda: None
    assert type(entity_1) is LocalTuyaCover

    status = DPS_STATUS.copy()
    device.status_updated(DPS_STATUS)

    assert entity_1.is_closed == False
    assert entity_1.current_cover_position == status["2"]

    await entity_1.async_set_cover_position(position=0)
    assert entity_1._current_state == STATE_SET_CLOSING
    await entity_1.async_set_cover_position(position=100)
    assert entity_1._current_state == STATE_SET_OPENING

    device.status_updated({**status, **{"2": 100, "3": 100}})
    assert entity_1.is_closed == False
    await entity_1.async_set_cover_position(position=100)
    assert entity_1._current_state == STATE_STOPPED

    # Position inverted.
    entity_1._position_inverted = True
    device.status_updated({})
    assert entity_1.is_closed == True

    # await entity_1.async_set_cover_position(position=100)
    # assert entity_1._current_state == STATE_SET_CLOSING


async def test_cover_inverted_without_position():
    """An inverted cover that doesn't report its position yet must not crash."""
    entity_config = {**CONFIG[DEVICE_NAME]["entities"][0], "position_inverted": True}
    config = {DEVICE_NAME: {**CONFIG[DEVICE_NAME], "entities": [entity_config]}}
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaCover)
    entity_1, *_ = get_entites(device)
    entity_1.schedule_update_ha_state = lambda: None

    device.status_updated({"1": "open"})
    assert entity_1.current_cover_position is None

    device.status_updated({"1": "close", "3": 100})
    assert entity_1.current_cover_position == 0
