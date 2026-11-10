
"""Tests for the LocalTuya coordinator."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import AsyncMock

import pytest
import time

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

    device._interface = SimpleNamespace(
        dispatched_dps={},
        is_connected=False,
    )    
    device._device_config = SimpleNamespace(
        enable_multi_dp_events=False,
        manual_dps="",
    )
    device._status = {}
    device._fake_gateway = False
    device._enable_debug = False
    device._logger = MagicMock()
    device._node_id = "test_node"
    device._last_update_time = 0
    device._subdevice_off_count = 0
    device.subdevice_state = SubdeviceState.ONLINE
    device.gateway = None
    device.sub_devices = {}
    device._device_config.sleep_time = 0
    device._task_connect = None
    device._task_reconnect = None
    device._task_shutdown_entities = None
    device._unsub_refresh = None
    device._unsub_new_entity = None
    device._entities = []
    device.debug = MagicMock()
    device.is_closing = False

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



# -------------------------------------------------------------------
# Command dispatch
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_dp_sends_single_dp(device):
    """set_dp should send a single datapoint to the device."""
    interface = SimpleNamespace(
        is_connected=True,
        set_dps=AsyncMock(),
    )
    device._interface = interface
    device._pending_status = {}

    await device.set_dp(True, "1")

    interface.set_dps.assert_awaited_once_with(
        {"1": True},
        cid="test_node",
    )
    assert device._pending_status == {}


@pytest.mark.asyncio
async def test_set_dps_sends_multiple_dps(device):
    """set_dps should send multiple datapoints in one command."""
    interface = SimpleNamespace(
        is_connected=True,
        set_dps=AsyncMock(),
    )
    device._interface = interface
    device._pending_status = {}

    payload = {
        "1": True,
        "2": "auto",
        "3": 25,
    }

    await device.set_dps(payload)

    interface.set_dps.assert_awaited_once_with(
        payload,
        cid="test_node",
    )
    assert device._pending_status == {}


@pytest.mark.asyncio
async def test_set_status_sends_pending_commands(device):
    """set_status should send all queued commands together."""
    interface = SimpleNamespace(
        is_connected=True,
        set_dps=AsyncMock(),
    )
    device._interface = interface
    device._pending_status = {
        "1": True,
        "2": "auto",
    }

    await device.set_status()

    interface.set_dps.assert_awaited_once_with(
        {
            "1": True,
            "2": "auto",
        },
        cid="test_node",
    )
    assert device._pending_status == {}


@pytest.mark.asyncio
async def test_set_dp_queues_command_while_asleep(device):
    """set_dp should queue commands instead of sending while asleep."""
    device._interface = None
    device._pending_status = {}
    device._device_config.sleep_time = 60
    device._last_update_time = time.monotonic() - 1

    await device.set_dp(True, 1)

    assert device._pending_status == {"1": True}


@pytest.mark.asyncio
async def test_set_dps_queues_commands_while_asleep(device):
    """set_dps should queue multiple commands while asleep."""
    device._interface = None
    device._pending_status = {}
    device._device_config.sleep_time = 60
    device._last_update_time = time.monotonic() - 1

    payload = {
        "1": True,
        "2": "auto",
    }

    await device.set_dps(payload)

    assert device._pending_status == payload


@pytest.mark.asyncio
async def test_set_status_flushes_commands_after_reconnect(device):
    """Queued commands should be sent when the device reconnects."""
    device._device_config.sleep_time = 60
    device._last_update_time = time.monotonic() - 1
    device._interface = None
    device._pending_status = {}

    await device.set_dp(True, 1)
    await device.set_dps({"2": "auto"})

    assert device._pending_status == {
        "1": True,
        "2": "auto",
    }

    interface = SimpleNamespace(
        is_connected=True,
        set_dps=AsyncMock(),
    )
    device._interface = interface

    await device.set_status()

    interface.set_dps.assert_awaited_once_with(
        {
            "1": True,
            "2": "auto",
        },
        cid="test_node",
    )
    assert device._pending_status == {}


@pytest.mark.asyncio
async def test_set_status_handles_command_failure(device):
    """A failed command should not propagate an exception."""
    interface = SimpleNamespace(
        is_connected=True,
        set_dps=AsyncMock(side_effect=TimeoutError("Command timed out")),
    )
    device._interface = interface
    device._pending_status = {"1": True}

    await device.set_status()

    interface.set_dps.assert_awaited_once_with(
        {"1": True},
        cid="test_node",
    )
    assert device._pending_status == {}


# -------------------------------------------------------------------
# Device properties
# -------------------------------------------------------------------


def test_connected(device):
    """Connected should reflect the interface connection state."""
    assert device.connected is False

    device._interface.is_connected = True

    assert device.connected is True


def test_is_connecting(device):
    """is_connecting should reflect whether a connection task exists."""
    assert device.is_connecting is False

    device._task_connect = MagicMock()

    assert device.is_connecting is True


def test_is_subdevice(device):
    """A device with a node ID should be recognized as a subdevice."""
    assert device.is_subdevice is True

    device._node_id = None

    assert device.is_subdevice is None

    device._node_id = "test_node"
    device._fake_gateway = True

    assert device.is_subdevice is False


def test_is_sleep(device):
    """A device should be considered asleep within its sleep interval."""
    device._device_config.sleep_time = 60
    device._last_update_time = time.monotonic() - 5

    assert device.is_sleep is True
    assert device.low_power is True


def test_is_not_sleep(device):
    """A device should not be asleep after its sleep interval."""
    device._device_config.sleep_time = 5
    device._last_update_time = time.monotonic() - 10

    assert device.is_sleep is False


def test_is_write_only(device):
    """A BLE subdevice marked with DP 0 should be write-only."""
    device._device_config.manual_dps = "0"

    assert device.is_write_only is True


def test_is_not_write_only(device):
    """A subdevice without DP 0 should not be write-only."""
    device._device_config.manual_dps = "1,2"

    assert device.is_write_only is False


def test_gateway_is_not_write_only(device):
    """A fake gateway should not be treated as a write-only subdevice."""
    device._device_config.manual_dps = "0"
    device._fake_gateway = True

    assert device.is_write_only is False


# -------------------------------------------------------------------
# Entity registration
# -------------------------------------------------------------------


def test_add_entities(device):
    """New entities should be added without replacing existing ones."""
    first = MagicMock()
    second = MagicMock()
    third = MagicMock()

    device.add_entities([first, second])
    device.add_entities([third])

    assert device._entities == [first, second, third]


# -------------------------------------------------------------------
# Subdevice connection
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connect_subdevices(device):
    """A connected gateway should connect all its subdevices."""
    device._interface.is_connected = True

    first = SimpleNamespace(async_connect=AsyncMock())
    second = SimpleNamespace(async_connect=AsyncMock())

    device.sub_devices = {
        "first": first,
        "second": second,
    }

    await device._connect_subdevices()

    first.async_connect.assert_awaited_once()
    second.async_connect.assert_awaited_once()


@pytest.mark.asyncio
async def test_connect_subdevices_without_subdevices(device):
    """A gateway without subdevices should do nothing."""
    device.sub_devices = {}

    await device._connect_subdevices()


@pytest.mark.asyncio
async def test_connect_subdevices_when_disconnected(device):
    """A disconnected gateway should not connect its subdevices."""
    first = SimpleNamespace(async_connect=AsyncMock())
    device.sub_devices = {"first": first}

    device._interface.is_connected = False

    await device._connect_subdevices()

    first.async_connect.assert_not_awaited()


# -------------------------------------------------------------------
# Device refresh
# -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_refresh_updates_dps(device):
    """A connected device should refresh its datapoints."""
    device._interface.is_connected = True
    device._interface.update_dps = AsyncMock()

    await device._async_refresh(None)

    device._interface.update_dps.assert_awaited_once_with(
        cid="test_node"
    )


@pytest.mark.asyncio
async def test_async_refresh_ignores_disconnected_device(device):
    """A disconnected device should not attempt a datapoint refresh."""
    device._interface = None

    await device._async_refresh(None)


@pytest.mark.asyncio
async def test_async_refresh_handles_timeout(device):
    """A refresh timeout should not propagate an exception."""
    device._interface.is_connected = True
    device._interface.update_dps = AsyncMock(
        side_effect=TimeoutError("Refresh timed out")
    )

    await device._async_refresh(None)

    device._interface.update_dps.assert_awaited_once_with(
        cid="test_node"
    )

