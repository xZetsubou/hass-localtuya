import logging
from types import SimpleNamespace

from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DEVICES,
    CONF_FRIENDLY_NAME,
    CONF_HOST,
    CONF_LOCAL_KEY,
    CONF_NAME,
)

from custom_components.localtuya import config_flow
from custom_components.localtuya.config_flow import LocalTuyaOptionsFlowHandler
from custom_components.localtuya.const import (
    CONF_GATEWAY_ID,
    CONF_NODE_ID,
    CONF_NO_CLOUD,
    CONF_PROTOCOL_VERSION,
    CONF_TUYA_GWID,
    CONF_TUYA_IP,
    CONF_TUYA_VERSION,
    DATA_DISCOVERY,
    DOMAIN,
)


class MockCloudData:
    def __init__(self, device_list, refreshed_device_list=None, refresh_result="ok"):
        self.device_list = device_list
        self.refreshed_device_list = refreshed_device_list or device_list
        self.refresh_result = refresh_result
        self.force_update_calls = []

    async def async_get_devices_list(self, force_update=False):
        self.force_update_calls.append(force_update)
        self.device_list = self.refreshed_device_list
        return self.refresh_result


def _field_suggested_value(schema, field_name):
    for field in schema.schema:
        if field.schema == field_name:
            return field.description["suggested_value"]
    raise AssertionError(f"Field {field_name} not found in schema")


def _make_options_flow(config_entry, cloud_data, discovered_devices):
    handler = LocalTuyaOptionsFlowHandler(config_entry)
    handler.config_entry = config_entry
    handler.hass = SimpleNamespace(
        data={
            DOMAIN: {
                config_entry.entry_id: SimpleNamespace(cloud_data=cloud_data),
                DATA_DISCOVERY: SimpleNamespace(devices=discovered_devices),
            }
        },
        config_entries=SimpleNamespace(async_entries=lambda domain: []),
    )
    handler.async_show_form = lambda **kwargs: kwargs
    return handler


async def test_add_device_refreshes_cloud_before_merging_subdevices(caplog):
    """Add device should merge against a freshly refreshed Tuya Cloud device list."""
    local_gateway = {
        CONF_TUYA_IP: "192.168.1.20",
        CONF_TUYA_GWID: "gateway_id",
        CONF_TUYA_VERSION: "3.3",
    }
    refreshed_cloud_devices = {
        "gateway_id": {
            CONF_LOCAL_KEY: "gateway_key",
            CONF_NAME: "Gateway",
            "online": True,
        },
        "subdevice_id": {
            CONF_LOCAL_KEY: "gateway_key",
            CONF_NAME: "Zigbee Button",
            CONF_NODE_ID: "node_1",
            "category": "wxkg",
            "online": True,
        },
    }
    cloud_data = MockCloudData(
        device_list={},
        refreshed_device_list=refreshed_cloud_devices,
    )
    config_entry = SimpleNamespace(
        entry_id="entry_id",
        data={CONF_NO_CLOUD: False, CONF_DEVICES: {}},
    )
    handler = _make_options_flow(
        config_entry,
        cloud_data,
        {"gateway_id": local_gateway},
    )

    with caplog.at_level(logging.DEBUG, logger=config_flow._LOGGER.name):
        result = await handler.async_step_add_device()

    assert cloud_data.force_update_calls == [True]
    assert result["step_id"] == "add_device"
    assert handler.discovered_devices["subdevice_id"] == {
        CONF_TUYA_IP: "192.168.1.20",
        CONF_TUYA_GWID: "subdevice_id",
        CONF_TUYA_VERSION: "3.3",
        CONF_NODE_ID: "node_1",
        CONF_GATEWAY_ID: "gateway_id",
    }
    assert (
        "Merged device list: local/discovered=1 cloud=2 merged=2" in caplog.text
    )


async def test_add_device_logs_cloud_refresh_failure(caplog):
    """Cloud refresh failures should be logged without blocking the Add device form."""
    cloud_data = MockCloudData(device_list={}, refresh_result="cloud_error")
    config_entry = SimpleNamespace(
        entry_id="entry_id",
        data={CONF_NO_CLOUD: False, CONF_DEVICES: {}},
    )
    handler = _make_options_flow(config_entry, cloud_data, {})

    with caplog.at_level(logging.WARNING, logger=config_flow._LOGGER.name):
        result = await handler.async_step_add_device()

    assert result["step_id"] == "add_device"
    assert "Failed to refresh Tuya cloud device list: cloud_error" in caplog.text


async def test_configure_device_uses_cloud_defaults_for_entered_device_id(monkeypatch):
    """A user-entered cloud device id should populate cloud defaults after validation errors."""

    async def mock_validate_input(localtuya_data, user_input):
        raise config_flow.CannotConnect

    monkeypatch.setattr(config_flow, "validate_input", mock_validate_input)

    cloud_data = MockCloudData(
        device_list={
            "cloud_device": {
                CONF_LOCAL_KEY: "cloud_local_key",
                CONF_NAME: "Cloud Device",
            }
        }
    )
    config_entry = SimpleNamespace(
        entry_id="entry_id",
        data={CONF_NO_CLOUD: False, CONF_DEVICES: {}},
    )
    handler = _make_options_flow(config_entry, cloud_data, {})
    handler.selected_device = "different_selected_device"

    result = await handler.async_step_configure_device(
        {
            CONF_HOST: "192.168.1.30",
            CONF_DEVICE_ID: "cloud_device",
            CONF_LOCAL_KEY: "",
            CONF_FRIENDLY_NAME: "",
            CONF_PROTOCOL_VERSION: "auto",
            CONF_NODE_ID: "",
        }
    )

    assert result["errors"] == {"base": "cannot_connect"}
    assert (
        _field_suggested_value(result["data_schema"], CONF_LOCAL_KEY)
        == "cloud_local_key"
    )
    assert (
        _field_suggested_value(result["data_schema"], CONF_FRIENDLY_NAME)
        == "Cloud Device"
    )
