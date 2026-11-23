"""Test the localtuya services."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import voluptuous as vol
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError

import custom_components.localtuya as localtuya
from custom_components.localtuya.const import DOMAIN

ENTRY_ID = "entry"
DEVICES = {
    "plug": {"host": "192.168.1.10"},
    "sensor": {"host": "192.168.1.11", "node_id": "a1b2", "gateway_id": "gateway"},
}


async def setup_services(devices: dict) -> dict:
    hass = Mock()
    hass.data = {}
    entry = Mock(entry_id=ENTRY_ID, data={"devices": DEVICES})
    hass.config_entries.async_entries.return_value = [entry]
    with patch.object(localtuya, "TuyaDiscovery") as discovery:
        discovery.return_value.start = AsyncMock()
        assert await localtuya.async_setup(hass, {})
    hass.data[DOMAIN][ENTRY_ID] = Mock(devices=devices)
    return {
        call.args[1]: call for call in hass.services.async_register.call_args_list
    }


def connected(status: dict) -> Mock:
    return Mock(connected=True, _status=status)


async def call(services: dict, name: str, data: dict):
    return await services[name].args[2](Mock(data=data))


async def test_get_status_returns_a_copy_of_the_device_status():
    status = {"1": True, "2": 50}
    services = await setup_services({"192.168.1.10": connected(status)})
    assert services["get_status"].kwargs["supports_response"] is SupportsResponse.ONLY
    response = await call(services, "get_status", {"device_id": "plug"})
    assert response == {"status": {"1": True, "2": 50}}
    status["1"] = False
    assert response["status"]["1"] is True


async def test_get_status_leaves_out_the_restored_state_placeholder():
    services = await setup_services(
        {
            "192.168.1.10": connected({"0": "restore", "1": True}),
            "192.168.1.11_a1b2": connected({"0": "restore"}),
        }
    )
    plug = await call(services, "get_status", {"device_id": "plug"})
    sensor = await call(services, "get_status", {"device_id": "sensor"})
    assert (plug, sensor) == ({"status": {"1": True}}, {"status": {}})


async def test_get_status_reads_a_sub_device_by_its_node_id():
    services = await setup_services(
        {
            "192.168.1.11": connected({"1": "gateway"}),
            "192.168.1.11_a1b2": connected({"1": 21.5}),
        }
    )
    response = await call(services, "get_status", {"device_id": "sensor"})
    assert response == {"status": {"1": 21.5}}


async def test_get_status_requires_a_device_id():
    services = await setup_services({})
    schema = services["get_status"].kwargs["schema"]
    assert schema({"device_id": "plug"}) == {"device_id": "plug"}
    with pytest.raises(vol.Invalid):
        schema({})


@pytest.mark.parametrize(
    ("device_id", "devices", "message"),
    [
        ("unknown", {}, "unknown device id"),
        (
            "plug",
            {"192.168.1.10": Mock(connected=False, _status={"1": True})},
            "not connected to device",
        ),
    ],
)
async def test_get_status_fails_for_an_unknown_or_disconnected_device(
    device_id, devices, message
):
    services = await setup_services(devices)
    with pytest.raises(HomeAssistantError, match=message):
        await call(services, "get_status", {"device_id": device_id})


async def test_set_dp_writes_to_the_device_it_looks_up():
    device = connected({})
    device.set_dps = AsyncMock()
    device.set_dp = AsyncMock()
    services = await setup_services({"192.168.1.11_a1b2": device})
    await call(services, "set_dp", {"device_id": "sensor", "value": {"1": True}})
    device.set_dps.assert_awaited_once_with({"1": True})
    await call(services, "set_dp", {"device_id": "sensor", "dp": 2, "value": 7})
    device.set_dp.assert_awaited_once_with(7, 2)


async def test_update_dps_asks_the_device_it_looks_up():
    device = connected({})
    device._node_id = "a1b2"
    device._interface.update_dps = AsyncMock()
    services = await setup_services({"192.168.1.11_a1b2": device})
    await call(services, "update_dps", {"device_id": "sensor", "dps": [1]})
    device._interface.update_dps.assert_awaited_once_with(dps=[1], cid="a1b2")
