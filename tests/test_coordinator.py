
"""Tests for the LocalTuya coordinator."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from custom_components.localtuya.coordinator import TuyaDevice
from custom_components.localtuya.const import DeviceConfig


@pytest.fixture
def device():
    """Create a minimally mocked Tuya device."""
    device = object.__new__(TuyaDevice)

    device.id = "test_device"
    device.hass = MagicMock()
    device.hass.bus.async_listeners.return_value = {
        "localtuya_device_dp_triggered": 1,
        "localtuya_status_update": 1,
    }

    device._interface = SimpleNamespace(dispatched_dps={})
    device._device_config = SimpleNamespace(enable_multi_dp_events=False)

    return device


def test_single_dp_event(device):
    """A single DP should trigger an event by default."""
    device._interface.dispatched_dps = {"1": "vibration"}

    device._handle_event({"1": "vibration"}, {"1": "vibration"})

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

    device._handle_event(
        {"1": "vibration", "5": False},
        {"1": "vibration", "5": False},
    )

    device.hass.bus.async_fire.assert_not_called()


def test_multiple_dps_enabled(device):
    """Each DP should trigger an event when the option is enabled."""
    device._device_config.enable_multi_dp_events = True
    device._interface.dispatched_dps = {
        "1": "vibration",
        "5": False,
    }

    device._handle_event(
        {"1": "vibration", "5": False},
        {"1": "vibration", "5": False},
    )

    assert device.hass.bus.async_fire.call_count == 2

    calls = device.hass.bus.async_fire.call_args_list

    assert calls[0].args == (
        "localtuya_device_dp_triggered",
        {"device_id": "test_device", "dp": "1", "value": "vibration"},
    )
    assert calls[1].args == (
        "localtuya_device_dp_triggered",
        {"device_id": "test_device", "dp": "5", "value": False},
    )


def test_repeated_identical_reports(device):
    """Repeated reports should trigger events even when values are identical."""
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

    device._handle_event({"1": "vibration"}, {"1": "vibration"})

    device.hass.bus.async_fire.assert_not_called()


def test_no_dp_event_listener(device):
    """DP events should not be fired without listeners."""
    device._device_config.enable_multi_dp_events = True
    device._interface.dispatched_dps = {
        "1": "vibration",
        "5": False,
    }
    device.hass.bus.async_listeners.return_value = {
        "localtuya_status_update": 1,
    }

    device._handle_event(
        {"1": "vibration", "5": False},
        {"1": "vibration", "5": False},
    )

    device.hass.bus.async_fire.assert_not_called()


def test_status_update_unchanged(device):
    """Status updates should not fire when the status is unchanged."""
    device._interface.dispatched_dps = {}

    status = {"1": "vibration"}

    device._handle_event(status, status)

    device.hass.bus.async_fire.assert_not_called()


def test_status_update_changed(device):
    """Status updates should still fire when the status changes."""
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
