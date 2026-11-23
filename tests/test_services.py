"""Test for the localtuya set_dp service."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.localtuya import (
    SERVICE_SET_DP,
    SERVICE_SET_DP_SCHEMA,
    async_setup,
)
from custom_components.localtuya.const import DOMAIN
from custom_components.localtuya.core.pytuya import TuyaProtocol

DEVICE_ID = "767823809c9c1f458745"
HOST = "192.168.1.100"
ENTRY_ID = "entry_1"


async def _get_set_dp_handler():
    """Run async_setup against a fake hass and return (handler, device mock)."""
    device = MagicMock()
    device.connected = True
    device.set_dp = AsyncMock()
    device.set_dps = AsyncMock()

    entry = SimpleNamespace(
        entry_id=ENTRY_ID,
        data={"devices": {DEVICE_ID: {"host": HOST}}},
    )
    hass = MagicMock()
    hass.config_entries.async_entries.return_value = [entry]
    hass.data = {DOMAIN: {ENTRY_ID: SimpleNamespace(devices={HOST: device})}}

    with patch("custom_components.localtuya.TuyaDiscovery") as discovery:
        discovery.return_value.start = AsyncMock()
        assert await async_setup(hass, {})

    handlers = {
        c.args[1]: c.args[2] for c in hass.services.async_register.call_args_list
    }
    return handlers[SERVICE_SET_DP], device


def _call(data):
    return SimpleNamespace(data=SERVICE_SET_DP_SCHEMA(data))


async def test_set_dp_scalar():
    handler, device = await _get_set_dp_handler()
    await handler(_call({"device_id": DEVICE_ID, "dp": 1, "value": True}))
    device.set_dp.assert_awaited_once_with(True, 1)
    device.set_dps.assert_not_awaited()


async def test_set_dp_dict_with_dp_is_json_encoded():
    handler, device = await _get_set_dp_handler()
    blob = {"mic": 1, "trackpet": 0}
    await handler(_call({"device_id": DEVICE_ID, "dp": 246, "value": blob}))
    device.set_dps.assert_not_awaited()
    device.set_dp.assert_awaited_once()
    value, dp = device.set_dp.await_args.args
    assert dp == 246
    assert isinstance(value, str)
    assert json.loads(value) == blob


async def test_set_dp_dict_without_dp_is_multi_dp():
    handler, device = await _get_set_dp_handler()
    dps = {"1": True, "2": True}
    await handler(_call({"device_id": DEVICE_ID, "value": dps}))
    device.set_dps.assert_awaited_once_with(dps)
    device.set_dp.assert_not_awaited()


async def test_set_dp_scalar_without_dp_raises():
    handler, device = await _get_set_dp_handler()
    with pytest.raises(HomeAssistantError, match="dp is required"):
        await handler(_call({"device_id": DEVICE_ID, "value": 5}))
    device.set_dp.assert_not_awaited()
    device.set_dps.assert_not_awaited()


async def test_set_dp_dict_reaches_wire_as_json_string():
    """Service -> real TuyaDevice -> real protocol payload, no mocks in between."""
    from custom_components.localtuya import coordinator

    hass = MagicMock()
    entry = MagicMock()
    device = coordinator.TuyaDevice(
        hass,
        entry,
        {
            "host": HOST,
            "device_id": DEVICE_ID,
            "protocol_version": "3.3",
            "local_key": "wV[NcWGUSFF`dSgO",
            "friendly_name": "Local 3G",
            "entities": [],
        },
    )
    proto = TuyaProtocol(DEVICE_ID, "wV[NcWGUSFF`dSgO", 3.3, False, MagicMock())
    sent = []

    async def fake_exchange(command, dps=None, nodeID=None, payload=None):
        sent.append(proto._generate_payload(command, dps, nodeId=nodeID))

    proto.exchange = fake_exchange
    proto.transport = MagicMock()
    proto.transport.is_closing.return_value = False
    device._interface = proto

    entry_ns = SimpleNamespace(
        entry_id=ENTRY_ID, data={"devices": {DEVICE_ID: {"host": HOST}}}
    )
    fake_hass = MagicMock()
    fake_hass.config_entries.async_entries.return_value = [entry_ns]
    fake_hass.data = {DOMAIN: {ENTRY_ID: SimpleNamespace(devices={HOST: device})}}
    with patch("custom_components.localtuya.TuyaDiscovery") as discovery:
        discovery.return_value.start = AsyncMock()
        await async_setup(fake_hass, {})
    handler = {
        c.args[1]: c.args[2] for c in fake_hass.services.async_register.call_args_list
    }[SERVICE_SET_DP]

    blob = {"mic": 1, "trackpet": 0}
    await handler(_call({"device_id": DEVICE_ID, "dp": 246, "value": blob}))

    assert len(sent) == 1
    body = json.loads(sent[0].payload)
    dps = body["dps"]
    assert list(dps) == ["246"]
    assert isinstance(dps["246"], str)
    assert json.loads(dps["246"]) == blob
