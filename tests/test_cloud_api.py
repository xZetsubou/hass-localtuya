import time

from custom_components.localtuya.core.cloud_api import TuyaCloudApi


async def test_force_update_bypasses_cache_and_replaces_device_list():
    """Force refresh should ignore the recent-update cache and replace stale devices."""
    cloud_api = TuyaCloudApi("eu", "client_id", "secret", "user_id")
    cloud_api.device_list = {"old_device": {"id": "old_device"}}
    cloud_api._last_devices_update = int(time.time())
    calls = []

    async def mock_make_request(method, url, body=None, headers={}):
        calls.append((method, url))
        return {
            "success": True,
            "result": [
                {"id": "fresh_device", "name": "Fresh Device"},
            ],
        }

    cloud_api.async_make_request = mock_make_request

    result = await cloud_api.async_get_devices_list(force_update=True)

    assert result == "ok"
    assert calls == [("GET", "/v1.0/users/user_id/devices")]
    assert cloud_api.device_list == {
        "fresh_device": {"id": "fresh_device", "name": "Fresh Device"}
    }


async def test_cached_regular_refresh_does_not_request_cloud():
    """Regular refresh keeps using the cache while it is still fresh."""
    cloud_api = TuyaCloudApi("eu", "client_id", "secret", "user_id")
    cloud_api.device_list = {"cached_device": {"id": "cached_device"}}
    cloud_api._last_devices_update = int(time.time())
    calls = []

    async def mock_make_request(method, url, body=None, headers={}):
        calls.append((method, url))
        return {"success": True, "result": []}

    cloud_api.async_make_request = mock_make_request

    result = await cloud_api.async_get_devices_list()

    assert result is None
    assert calls == []
    assert cloud_api.device_list == {"cached_device": {"id": "cached_device"}}


async def test_stale_regular_refresh_updates_existing_device_list():
    """Non-forced refresh keeps the previous merge/update behavior."""
    cloud_api = TuyaCloudApi("eu", "client_id", "secret", "user_id")
    cloud_api.device_list = {"existing_device": {"id": "existing_device"}}
    cloud_api._last_devices_update = 0

    async def mock_make_request(method, url, body=None, headers={}):
        return {
            "success": True,
            "result": [
                {"id": "fresh_device", "name": "Fresh Device"},
            ],
        }

    cloud_api.async_make_request = mock_make_request

    result = await cloud_api.async_get_devices_list()

    assert result == "ok"
    assert cloud_api.device_list == {
        "existing_device": {"id": "existing_device"},
        "fresh_device": {"id": "fresh_device", "name": "Fresh Device"},
    }
