"""Decision logic for the device offline watchdog (pure, no Home Assistant imports).

A LocalTuya entity is `available` while it holds a status or its device is connected.
The status is only cleared by TuyaDevice._shutdown_entities(), which disconnected()
schedules; every code path that loses that schedule leaves the entities available with
a stale status for as long as the device stays unreachable. The watchdog in
coordinator.TuyaDevice enforces the invariant periodically; this module holds the
decision so it can be unit-tested without Home Assistant.
"""

from __future__ import annotations

# Seconds a device may stay without a connection before its entities are forced
# unavailable. Measured from the first tick that saw the connection gone, NOT from the
# last status update: a healthy relay whose state never changes sends no status for
# hours, and a brief network blip must still be left to the normal path (two missed
# heartbeats + TIMEOUT_CONNECT, roughly 30 s) and its reconnect.
OFFLINE_GRACE = 60

# How often the watchdog evaluates the invariant.
OFFLINE_WATCHDOG_INTERVAL_SECONDS = 30


def should_force_offline(
    *,
    connected: bool,
    is_sleep: bool,
    is_closing: bool,
    is_subdevice: bool,
    entities_available: bool,
    seconds_offline: float,
    grace: float = OFFLINE_GRACE,
) -> bool:
    """Return True when the device's entities must be forced unavailable.

    connected:           the device has a live pytuya connection
    is_sleep:            low-power device that legitimately keeps its last status
    is_closing:          the device is being unloaded
    is_subdevice:        gateway child; its availability is driven by the gateway
    entities_available:  at least one entity still reports itself available
    seconds_offline:     time since the connection was first seen to be gone
    """
    if is_closing or is_sleep or is_subdevice or connected:
        return False
    if not entities_available:
        return False
    return seconds_offline >= grace


def entity_holds_status(entity_available: bool, ha_state: str | None) -> bool:
    """Return True when an entity still looks available anywhere it is observed.

    entity_available:  the entity object's own `available` (has a status or the
                       device is connected)
    ha_state:          the state Home Assistant currently shows for it, or None
                       when it has no state (not added / removed)

    The two can disagree: a dispatch of `None` clears the entity's status, but if
    the state write that should follow is lost or raced, Home Assistant keeps
    showing the last status (light.201_b5 read `on` for 8 h on 2026-09-19 with
    no socket to the bulb, while the watchdog saw "nothing available" and stayed
    quiet). The invariant matters where it is observed, so the shown state
    counts too.
    """
    if entity_available:
        return True
    return ha_state is not None and ha_state != "unavailable"
