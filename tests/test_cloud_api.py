"""Tests for the Tuya cloud API client."""

from unittest.mock import AsyncMock

import pytest

from custom_components.localtuya.core.cloud_api import TuyaCloudApi


@pytest.mark.asyncio
async def test_device_list_includes_gateway_sub_devices():
    """Bluetooth sub-devices are added and inherit their gateway local key."""
    cloud = TuyaCloudApi("EU", "client", "secret", "user")

    responses = {
        "/v1.0/users/user/devices": {
            "success": True,
            "result": [{"id": "gateway", "local_key": "gateway-key"}],
        },
        "/v1.0/iot-03/devices/gateway/sub-devices": {
            "success": True,
            "result": [{"id": "timer", "node_id": "timer-node"}],
        },
    }
    cloud.async_make_request = AsyncMock(
        side_effect=lambda _method, url: responses.get(url, {"success": False})
    )

    assert await cloud.async_get_devices_list(force_update=True) == "ok"
    assert cloud.device_list["timer"]["gateway_id"] == "gateway"
    assert cloud.device_list["timer"]["node_id"] == "timer-node"
    assert cloud.device_list["timer"]["local_key"] == "gateway-key"


@pytest.mark.asyncio
async def test_device_list_ignores_devices_without_sub_device_support():
    """Devices without sub-device support remain in the device list."""
    cloud = TuyaCloudApi("EU", "client", "secret", "user")

    responses = {
        "/v1.0/users/user/devices": {
            "success": True,
            "result": [{"id": "outlet", "local_key": "outlet-key"}],
        },
        "/v1.0/iot-03/devices/outlet/sub-devices": {
            "success": False,
            "code": 1106,
            "msg": "permission deny",
        },
    }
    cloud.async_make_request = AsyncMock(
        side_effect=lambda _method, url: responses[url]
    )

    assert await cloud.async_get_devices_list(force_update=True) == "ok"
    assert cloud.device_list == {"outlet": {"id": "outlet", "local_key": "outlet-key"}}
