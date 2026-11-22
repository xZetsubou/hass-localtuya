"""Tests for the offline watchdog decision (pure function, no HA needed)."""

from custom_components.localtuya.core.offline_watchdog import (
    OFFLINE_GRACE,
    entity_holds_status,
    should_force_offline,
)


def _decide(**overrides):
    base = dict(
        connected=False,
        is_sleep=False,
        is_closing=False,
        is_subdevice=False,
        entities_available=True,
        seconds_offline=OFFLINE_GRACE + 1,
    )
    base.update(overrides)
    return should_force_offline(**base)


def test_stale_entities_on_unreachable_device_are_forced_offline():
    # The 2026-09-03 case: relay cut the bulb's power, connection_lost was lost,
    # entity kept `on` for 15 h.
    assert _decide() is True


def test_within_grace_nothing_happens():
    # A blip shorter than the grace is the normal path's business (heartbeats,
    # _shutdown_entities, reconnect), not the watchdog's.
    assert _decide(seconds_offline=OFFLINE_GRACE - 1) is False
    assert _decide(seconds_offline=0) is False


def test_exactly_at_grace_fires():
    assert _decide(seconds_offline=OFFLINE_GRACE) is True


def test_connected_device_is_never_touched():
    assert _decide(connected=True, seconds_offline=10**6) is False


def test_sleep_device_keeps_last_status():
    assert _decide(is_sleep=True) is False


def test_closing_device_is_left_alone():
    assert _decide(is_closing=True) is False


def test_subdevice_is_driven_by_its_gateway():
    assert _decide(is_subdevice=True) is False


def test_already_unavailable_entities_do_not_refire():
    # After a normal _shutdown_entities the invariant already holds: stay quiet.
    assert _decide(entities_available=False) is False


def test_custom_grace():
    assert _decide(seconds_offline=20, grace=10) is True
    assert _decide(seconds_offline=5, grace=10) is False


# --- entity_holds_status: the shown state counts too (2026-09-19) ------------


def test_entity_with_own_status_holds():
    assert entity_holds_status(True, "unavailable") is True


def test_cleared_entity_still_shown_on_holds():
    # The 2026-09-19 case: status cleared, HA still shows `on`.
    assert entity_holds_status(False, "on") is True


def test_cleared_entity_shown_unknown_holds():
    assert entity_holds_status(False, "unknown") is True


def test_cleared_entity_shown_unavailable_is_done():
    assert entity_holds_status(False, "unavailable") is False


def test_entity_without_ha_state_is_done():
    # Not added to HA (or removed): nothing to repair.
    assert entity_holds_status(False, None) is False
