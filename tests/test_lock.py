"""Test for localtuya."""

from . import *
from custom_components.localtuya.lock import LocalTuyaLock, DOMAIN as PLATFORM_DOMAIN

STATE_ON = "activated"
CONFIG = {
    DEVICE_NAME: {
        **DEVICE_CONFIG,
        "entities": [
            {
                "entity_category": "None",
                "friendly_name": f"{PLATFORM_DOMAIN} 1",
                "icon": "",
                "id": "1",
                "lock_state_dp": "2",
                "jammed_dp": "3",
                "platform": PLATFORM_DOMAIN,
                "restore_on_reconnect": False,
            }
        ],
    }
}

DPS_STATUS = {"1": None, "2": "unlocked"}


async def test_lock():
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaLock)
    entities: list[LocalTuyaLock] = get_entites(device)

    assert len(entities) > 0
    entity_1, *_ = entities
    assert type(entity_1) is LocalTuyaLock

    device.status_updated(DPS_STATUS)
    assert entity_1.state == "unlocked"

    device.status_updated({**DPS_STATUS, **{"1": True}})
    assert not entity_1.is_locked

    assert not entity_1.is_jammed
    device.status_updated({**DPS_STATUS, **{"3": True}})
    assert entity_1.is_jammed


# Access-control keypad ("mk"): code-based remote unlock.
KEYPAD_CONFIG = {
    DEVICE_NAME: {
        **DEVICE_CONFIG,
        "entities": [
            {
                "entity_category": "None",
                "friendly_name": "Door",
                "icon": "",
                "id": "9",  # remote_no_dp_key
                "remote_key_dp": "8",  # remote_no_pd_setkey
                "lock_state_dp": "35",  # closed_opened_kit
                "platform": PLATFORM_DOMAIN,
                "restore_on_reconnect": False,
            }
        ],
    }
}


async def _keypad(replies: dict[str, str]):
    """Keypad whose device answers each raw DP write with `replies[dp]`."""
    import base64
    from homeassistant.exceptions import HomeAssistantError  # noqa: F401

    device = await init(KEYPAD_CONFIG, PLATFORM_DOMAIN, LocalTuyaLock)
    entity: LocalTuyaLock = get_entites(device)[0]
    entity.hass.loop = asyncio.events.get_running_loop()
    entity.warning = Mock()
    sent = []

    async def set_dp(value, dp):
        sent.append((str(dp), base64.b64decode(value)))
        if str(dp) in replies:
            device.status_updated({str(dp): replies[str(dp)]})

    device.set_dp = set_dp
    device._status = {}
    return device, entity, sent


@pytest.mark.asyncio
async def test_keypad_remote_unlock():
    import struct

    device, entity, sent = await _keypad({"8": "AABk", "9": "AABkNzg="})
    before = int(time.time())
    await entity.async_unlock()

    (key_dp, key), (unlock_dp, unlock) = sent
    assert key_dp == "8" and unlock_dp == "9"
    valid, member, start, end, uses = struct.unpack(">BHIIH", key[:13])
    assert (valid, member, uses) == (1, 100, 1)
    assert start <= before and end >= before + 299
    code = key[13:]
    assert len(code) == 8 and code.isdigit()
    # Unlock carries the same one-time code, action 1, source app.
    assert unlock == b"\x01\x00\x64" + code + b"\x00\x01"


@pytest.mark.asyncio
async def test_keypad_remote_unlock_refused():
    from homeassistant.exceptions import HomeAssistantError

    _, entity, sent = await _keypad({"8": "AABk", "9": "BQBk"})  # 05 = wrong code
    with pytest.raises(HomeAssistantError, match="wrong code"):
        await entity.async_unlock()
    assert len(sent) == 2

    _, entity, sent = await _keypad({"8": "AQBk"})  # key registration failed
    with pytest.raises(HomeAssistantError, match="failed"):
        await entity.async_unlock()
    assert len(sent) == 1  # never sent the unlock


@pytest.mark.asyncio
async def test_keypad_lock_is_refused():
    from homeassistant.exceptions import HomeAssistantError

    _, entity, sent = await _keypad({})
    with pytest.raises(HomeAssistantError, match="relocks automatically"):
        await entity.async_lock()
    assert sent == []  # a remote "lock" would open the strike


async def test_keypad_strike_state():
    device = await init(KEYPAD_CONFIG, PLATFORM_DOMAIN, LocalTuyaLock)
    entity: LocalTuyaLock = get_entites(device)[0]

    device.status_updated({"9": "AABkNzg="})  # reply only: still locked
    assert entity.is_locked
    device.status_updated({"35": "AQAB"})  # strike released
    assert not entity.is_locked
    device.status_updated({"35": "AQAC"})  # relocked
    assert entity.is_locked
