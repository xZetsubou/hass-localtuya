"""Test for localtuya."""

from . import *
from custom_components.localtuya.const import CONF_REFRESH_DP_QUERY

DPS_STATUS = {"20": True, "21": "colour"}


def create_device(device_config: dict[str, Any]) -> coordinator.TuyaDevice:
    hass = HomeAssistant("")
    entry = ConfigEntry(**create_entry({DEVICE_NAME: device_config}))
    hass.data.setdefault(DOMAIN, {entry.entry_id: {}})
    device = coordinator.TuyaDevice(hass, entry, device_config)
    device._interface = Mock(is_connected=True)
    device._interface.status = AsyncMock(return_value=DPS_STATUS)
    device._interface.update_dps = AsyncMock()
    device.status_updated = Mock()
    return device


async def test_refresh_update_dps_by_default():
    device = create_device({**DEVICE_CONFIG, "entities": []})

    await device._async_refresh(None)

    device._interface.update_dps.assert_awaited_once()
    device._interface.status.assert_not_awaited()
    device.status_updated.assert_not_called()


async def test_refresh_dp_query():
    device = create_device(
        {**DEVICE_CONFIG, "entities": [], CONF_REFRESH_DP_QUERY: True}
    )

    await device._async_refresh(None)

    device._interface.status.assert_awaited_once()
    device._interface.update_dps.assert_not_awaited()
    device.status_updated.assert_called_once_with(DPS_STATUS)
