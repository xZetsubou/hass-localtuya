
"""Tests for the LocalTuya coordinator."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from custom_components.localtuya.const import DeviceConfig
from custom_components.localtuya.coordinator import TuyaDevice
from custom_components.localtuya.core.pytuya import SubdeviceState


@pytest.fixture
def device():
    """Create a minimally initialized Tuya device."""
    device = object.__new__(TuyaDevice)

    device.id = "test_device"
    device.hass = MagicMock()
    device.hass.bus.async_listeners.return_value = {
        "localtuya_device_dp_triggered": 1,
        "localtuya_status_update": 1,
    }

    device._interface = SimpleNamespace(dispatched_dps={})
    device._device_config = SimpleNamespace(
        enable_multi_dp_events=False,
        manual_dps="",
    )
    device._status = {}
    device._fake_gateway = False
    device._node_id = "test_node"
    device._last_update_time = 0
    device._subdevice_off_count = 0
    device.subdevice_state = SubdeviceState.ONLINE
    device.gateway = None
    device.sub_devices = {}

    return device


# -------------------------------------------------------------------
# DP event handling
# -------------------------------------------------------------------


def test_single_dp_event(device):
    """A single DP should trigger an event by default."""
    device._interface.dispatched_dps = {"1": "vibration"}
    status = {"1": "vibration"}

    device._handle_event(status, status)

    device.hass.bus.async_fire.assert_called_once_with(
        "localtuya_device_dp_triggered",
        {"device_id": "test_device", "dp": "1", "value": "vibration"},
    )


def test_multiple_dps_disabled(device):
    """Multiple DPs should not trigger events by default."""
    device._interface.dispatched_dps = {
        "1": "vibration",
        "5": False,
    }
    status = {"1": "vibration", "5": False}

    device._handle_event(status, status)

    device.hass.bus.async_fire.assert_not_called()


def test_multiple_dps_enabled(device):
    """Each DP should trigger an event when the option is enabled."""
    device._device_config.enable_multi_dp_events = True
    device._interface.dispatched_dps = {
        "1": "vibration",
        "5": False,
        "7": 42,
    }
    status = {"1": "vibration", "5": False, "7": 42}

    device._handle_event(status, status)

    calls = device.hass.bus.async_fire.call_args_list

    assert len(calls) == 3
    assert calls[0].args == (
        "localtuya_device_dp_triggered",
        {"device_id": "test_device", "dp": "1", "value": "vibration"},
    )
    assert calls[1].args == (
        "localtuya_device_dp_triggered",
        {"device_id": "test_device", "dp": "5", "value": False},
    )
    assert calls[2].args == (
        "localtuya_device_dp_triggered",
        {"device_id": "test_device", "dp": "7", "value": 42},
    )


def test_repeated_identical_multi_dp_reports(device):
    """Repeated identical reports should still trigger DP events."""
    device._device_config.enable_multi_dp_events = True
    device._interface.dispatched_dps = {
        "1": "vibration",
        "5": False,
    }
    status = {"1": "vibration", "5": False}

    device._handle_event(status, status)
    device._handle_event(status, status)

    assert device.hass.bus.async_fire.call_count == 4


def test_empty_dispatched_dps(device):
    """An empty DP update should not trigger events."""
    device._device_config.enable_multi_dp_events = True
    device._interface.dispatched_dps = {}
    status = {"1": "vibration"}

    device._handle_event(status, status)

    device.hass.bus.async_fire.assert_not_called()


def test_no_dp_event_listener(device):
    """DP events should not fire when there are no DP event listeners."""
    device._device_config.enable_multi_dp_events = True
    device._interface.dispatched_dps = {
        "1": "vibration",
        "5": False,
    }
    device.hass.bus.async_listeners.return_value = {
        "localtuya_status_update": 1,
    }
    status = {"1": "vibration", "5": False}

    device._handle_event(status, status)

    device.hass.bus.async_fire.assert_not_called()


# -------------------------------------------------------------------
# Status event handling
# -------------------------------------------------------------------


def test_status_update_unchanged(device):
    """Status update event should not fire when status is unchanged."""
    device._interface.dispatched_dps = {}
    status = {"1": "vibration"}

    device._handle_event(status, status)

    device.hass.bus.async_fire.assert_not_called()


def test_status_update_changed(device):
    """Status update event should fire when status changes."""
    device._interface.dispatched_dps = {}

    device._handle_event(
        {"1": "vibration"},
        {"1": "idle"},
    )

    device.hass.bus.async_fire.assert_called_once_with(
        "localtuya_status_update",
        {
            "device_id": "test_device",
            "old_status": {"1": "vibration"},
            "new_status": {"1": "idle"},
        },
    )


# -------------------------------------------------------------------
# Status handling
# -------------------------------------------------------------------


def test_status_updated_merges_partial_updates(device):
    """A partial status update should preserve previously received DPs."""
    device._status = {"1": "vibration"}
    device._interface.dispatched_dps = {"5": True}
    device._dispatch_status = MagicMock()

    device.status_updated({"5": True})

    assert device._status == {
        "1": "vibration",
        "5": True,
    }
    device._dispatch_status.assert_called_once()


def test_fake_gateway_ignores_status_updates(device):
    """Fake gateways should not process status updates."""
    device._fake_gateway = True
    device._status = {"1": "original"}
    device._dispatch_status = MagicMock()

    device.status_updated({"1": "updated"})

    assert device._status == {"1": "original"}
    device._dispatch_status.assert_not_called()


# -------------------------------------------------------------------
# Subdevice handling
# -------------------------------------------------------------------


def test_filter_subdevices(device):
    """Closed subdevices should be removed while active ones remain."""
    active = SimpleNamespace(is_closing=False)
    closed = SimpleNamespace(is_closing=True)

    device.sub_devices = {
        "active": active,
        "closed": closed,
    }

    device.filter_subdevices()

    assert device.sub_devices == {"active": active}


# -------------------------------------------------------------------
# Gateway handling
# -------------------------------------------------------------------


def test_get_gateway_with_matching_local_key(device):
    """Return the gateway when its local key matches the subdevice."""
    gateway = SimpleNamespace(local_key="test_key")

    device.gateway = gateway
    device.local_key = "test_key"

    assert device._get_gateway() is gateway


def test_get_gateway_with_mismatched_local_key(device):
    """Reject a gateway whose local key differs from the subdevice."""
    gateway = SimpleNamespace(local_key="gateway_key")

    device.gateway = gateway
    device.local_key = "subdevice_key"
    device.subdevice_state = SubdeviceState.ONLINE
    device.warning = MagicMock()

    assert device._get_gateway() is None
    assert device.subdevice_state == SubdeviceState.ABSENT
    device.warning.assert_called_once()


def test_get_gateway_without_gateway(device):
    """Return None when no gateway is configured."""
    device.gateway = None

    assert device._get_gateway() is None


# -------------------------------------------------------------------
# Device configuration
# -------------------------------------------------------------------


def test_multi_dp_events_default_disabled():
    """Multi-DP events should be disabled for existing configurations."""
    config = DeviceConfig({
        "device_id": "test_device",
        "host": "192.168.1.100",
        "local_key": "test_key",
        "protocol_version": "3.3",
        "entities": [],
    })

    assert config.enable_multi_dp_events is False


def test_multi_dp_events_can_be_enabled():
    """Multi-DP events can be enabled through device configuration."""
    config = DeviceConfig({
        "device_id": "test_device",
        "host": "192.168.1.100",
        "local_key": "test_key",
        "protocol_version": "3.3",
        "entities": [],
        "enable_multi_dp_events": True,
    })

    assert config.enable_multi_dp_events is True
