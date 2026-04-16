"""Tests for low-power device handling."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.localtuya import TuyaCloudApi, coordinator
from custom_components.localtuya.const import DOMAIN

from . import DEVICE_CONFIG, DEVICE_NAME, create_entry


def build_device(*, event_driven: bool = False, scan_interval: int = 0):
    """Build a TuyaDevice for low-power tests."""
    config = {
        DEVICE_NAME: {
            **DEVICE_CONFIG,
            "entities": [],
            "device_event_driven": event_driven,
            "scan_interval": scan_interval,
        }
    }

    hass = HomeAssistant("")
    entry = ConfigEntry(**create_entry(config))
    tuya_api = TuyaCloudApi("EU", "test_client_id", "test_secret", "test_user_id")

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator.HassLocalTuyaData(tuya_api, {})

    return coordinator.TuyaDevice(hass, entry, config[DEVICE_NAME])


@pytest.mark.asyncio
async def test_event_driven_device_is_treated_as_sleeping():
    """Event-driven low-power devices should always behave as sleeping devices."""
    device = build_device(event_driven=True)

    assert device.is_sleep is True


@pytest.mark.asyncio
async def test_event_driven_device_skips_keep_alive_and_refresh():
    """Event-driven devices should avoid active maintenance loops."""
    device = build_device(event_driven=True, scan_interval=30)

    interface = AsyncMock()
    interface.is_connected = True
    interface.status = AsyncMock(return_value={"1": "closed"})
    interface.enable_debug = Mock()
    interface.add_dps_to_request = Mock()
    interface.keep_alive = Mock()

    with (
        patch(
            "custom_components.localtuya.coordinator.pytuya_connect",
            new=AsyncMock(return_value=interface),
        ),
        patch(
            "custom_components.localtuya.coordinator.dispatcher_send"
        ),
        patch(
            "custom_components.localtuya.coordinator.async_dispatcher_connect",
            return_value=lambda: None,
        ),
        patch(
            "custom_components.localtuya.coordinator.async_track_time_interval"
        ) as track_interval,
    ):
        await device._make_connection()

    track_interval.assert_not_called()
    interface.keep_alive.assert_not_called()


@pytest.mark.asyncio
async def test_event_driven_shutdown_keeps_last_state_available():
    """Event-driven devices should not be forced unavailable after disconnect."""
    device = build_device(event_driven=True)

    with (
        patch(
            "custom_components.localtuya.coordinator.asyncio.sleep",
            new=AsyncMock(),
        ),
        patch("custom_components.localtuya.coordinator.dispatcher_send") as dispatcher,
    ):
        await device._shutdown_entities("sleeping")

    dispatcher.assert_not_called()
