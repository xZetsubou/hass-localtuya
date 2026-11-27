"""Platform to present any Tuya DP as a Lock."""

import asyncio
import base64
import binascii
import logging
import secrets
import struct
import time
from functools import partial
from typing import Any
from .config_flow import col_to_select

import voluptuous as vol
from homeassistant.components.lock import DOMAIN, LockEntity
from homeassistant.exceptions import HomeAssistantError
from .entity import LocalTuyaEntity, async_setup_entry

from .const import CONF_JAMMED_DP, CONF_LOCK_STATE_DP, CONF_REMOTE_KEY_DP

_LOGGER = logging.getLogger(__name__)

# Code-based remote unlock (remote_no_pd_setkey + remote_no_dp_key), used by
# access-control keypads ("mk") and many Wi-Fi locks. Both DPs are raw:
#   set key  -> validity(1) | member(2) | start(4) | end(4) | uses(2) | code(8 ASCII)
#   unlock   -> action(1) | member(2) | code(8 ASCII) | source(2)
#   replies  <- status(1) | member(2) ...      status 0 = success
# Each unlock registers a fresh one-time code, valid for a few minutes, so no
# long-lived credential is stored anywhere.
REMOTE_MEMBER_ID = 100
REMOTE_CODE_WINDOW = 300  # seconds either side of now, allows for clock drift
REMOTE_ACTION_UNLOCK = 0x01
REMOTE_SOURCE_APP = 0x0001
REMOTE_REPLY_TIMEOUT = 5
REMOTE_STATUS = {
    1: "failed",
    2: "password error",
    3: "timeout",
    4: "outside permitted hours",
    5: "wrong code",
    6: "double locked",
}


def flow_schema(dps):
    """Return schema used in config flow."""
    return {
        vol.Optional(CONF_LOCK_STATE_DP): col_to_select(dps, is_dps=True),
        vol.Optional(CONF_JAMMED_DP): col_to_select(dps, is_dps=True),
        vol.Optional(CONF_REMOTE_KEY_DP): col_to_select(dps, is_dps=True),
    }


def _raw(value) -> bytes | None:
    """Decode a raw (base64) DP value, None if it isn't one."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        return None


def build_set_key_msg(code: str, now: int) -> str:
    """remote_no_pd_setkey payload: one-time code for REMOTE_MEMBER_ID."""
    msg = struct.pack(
        ">BHIIH",
        1,  # valid
        REMOTE_MEMBER_ID,
        now - REMOTE_CODE_WINDOW,
        now + REMOTE_CODE_WINDOW,
        1,  # usable times
    )
    return base64.b64encode(msg + code.encode("ascii")).decode()


def build_unlock_msg(code: str) -> str:
    """remote_no_dp_key payload: unlock with the code just registered."""
    msg = struct.pack(">BH", REMOTE_ACTION_UNLOCK, REMOTE_MEMBER_ID)
    msg += code.encode("ascii") + struct.pack(">H", REMOTE_SOURCE_APP)
    return base64.b64encode(msg).decode()


class LocalTuyaLock(LocalTuyaEntity, LockEntity):
    """Representation of a Tuya Lock."""

    def __init__(
        self,
        device,
        config_entry,
        Lockid,
        **kwargs,
    ):
        """Initialize the Tuya Lock."""
        super().__init__(device, config_entry, Lockid, _LOGGER, **kwargs)
        self._state = None
        self._remote_key_dp = self._config.get(CONF_REMOTE_KEY_DP)
        self._replies: dict[str, asyncio.Future] = {}

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        if self._remote_key_dp:
            # Access controllers answer a remote *lock* (action 0) with success
            # and then release the strike exactly like an unlock. They relock
            # on their own, so refuse rather than open the door.
            raise HomeAssistantError(
                f"{self.name} relocks automatically; remote lock is not supported"
            )
        await self._device.set_dp(True, self._dp_id)

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        if self._remote_key_dp:
            return await self._async_remote_unlock()
        await self._device.set_dp(False, self._dp_id)

    async def _async_remote_unlock(self) -> None:
        """Register a one-time code, then unlock with it."""
        code = "".join(secrets.choice("0123456789") for _ in range(8))

        status = await self._send_and_wait(
            self._remote_key_dp, build_set_key_msg(code, int(time.time()))
        )
        if status not in (None, 0):
            raise HomeAssistantError(
                f"{self.name} refused the unlock code: {REMOTE_STATUS.get(status, status)}"
            )

        status = await self._send_and_wait(self._dp_id, build_unlock_msg(code))
        if status is None:
            self.warning(f"{self.name}: no reply to remote unlock")
        elif status != 0:
            raise HomeAssistantError(
                f"{self.name} refused to unlock: {REMOTE_STATUS.get(status, status)}"
            )

    async def _send_and_wait(self, dp, value: str) -> int | None:
        """Write a raw DP and wait for the device's reply status byte."""
        dp = str(dp)
        # Replies often repeat the previous value byte for byte; forget it so
        # the reply registers as a change and reaches status_updated.
        self._status.pop(dp, None)
        self._device._status.pop(dp, None)

        future = self.hass.loop.create_future()
        self._replies[dp] = future
        try:
            await self._device.set_dp(value, dp)
            async with asyncio.timeout(REMOTE_REPLY_TIMEOUT):
                return await future
        except TimeoutError:
            return None
        finally:
            self._replies.pop(dp, None)

    def status_updated(self):
        """Device status was updated."""
        for dp, future in self._replies.items():
            if not future.done() and (reply := _raw(self.dp_value(dp))):
                future.set_result(reply[0])

        state = self.dp_value(self._dp_id)
        if self._remote_key_dp:
            # The main DP only carries command replies; the strike is locked
            # unless the state DP says otherwise.
            state = None
        if (lock_state := self.dp_value(CONF_LOCK_STATE_DP)) or lock_state is not None:
            state = lock_state

        if (raw := _raw(state)) and len(raw) == 3 and raw[-1] in (1, 2):
            # closed_opened_kit (raw): last byte 1 = released, 2 = closed.
            self._attr_is_locked = raw[-1] == 2
        else:
            self._attr_is_locked = state in (False, "closed", "close", None)

        if jammed := self.dp_value(CONF_JAMMED_DP, False):
            self._attr_is_jammed = jammed

    # No need to restore state for a Lock
    async def restore_state_when_connected(self):
        """Do nothing for a Lock."""
        return


async_setup_entry = partial(async_setup_entry, DOMAIN, LocalTuyaLock, flow_schema)
