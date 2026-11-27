"""
    This a file contains available tuya data
    https://developer.tuya.com/en/docs/iot/standarddescription?id=K9i5ql6waswzq
    Credits: official HA Tuya integration.
    Modified by: xZetsubou
"""

from .base import (
    DPCode,
    LocalTuyaEntity,
)


def localtuya_lock():
    """Define localtuya lock configs"""
    data = {}
    return data


LOCKS: dict[str, tuple[LocalTuyaEntity, ...]] = {
    # Locks
    "ms": (
        LocalTuyaEntity(
            id=(DPCode.REMOTE_UNLOCK_SWITCH, DPCode.SWITCH),
            jammed_dp=DPCode.HIJACK,
            lock_state_dp=(DPCode.CLOSED_OPENED, DPCode.OPEN_CLOSE),
        ),
    ),
}

# Access control (keypads / door controllers driving a strike). Remote unlock is
# a code handshake: register a one-time code on remote_no_pd_setkey, then send
# it on remote_no_dp_key. closed_opened_kit reports the strike (AQAB / AQAC).
# https://developer.tuya.com/en/docs/iot/s?id=Kb0o2xhlkxbet
LOCKS["mk"] = (
    LocalTuyaEntity(
        id=DPCode.REMOTE_NO_DP_KEY,
        remote_key_dp=DPCode.REMOTE_NO_PD_SETKEY,
        lock_state_dp=DPCode.CLOSED_OPENED_KIT,
    ),
)

LOCKS["jtmspro"] = LOCKS["ms"]
LOCKS["jtmsbh"] = LOCKS["ms"]
