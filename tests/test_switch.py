"""Test for localtuya."""

from . import *
from homeassistant.const import EntityCategory
from homeassistant.helpers import device_registry as dr
from custom_components.localtuya.switch import LocalTuyaSwitch, DOMAIN as SWITCH_DOMAIN

CONFIG = {
    DEVICE_NAME: {
        **DEVICE_CONFIG,
        "entities": [
            {
                "entity_category": "None",
                "friendly_name": "Switch 1",
                "icon": "",
                "id": "1",
                "is_passive_entity": False,
                "platform": "switch",
                "restore_on_reconnect": False,
            },
            {
                "entity_category": "config",
                "friendly_name": "Switch 2",
                "icon": "",
                "id": "2",
                "is_passive_entity": False,
                "platform": "switch",
                "restore_on_reconnect": False,
            },
        ],
    }
}

DPS_STATUS = {"1": True, "2": False}


async def test_switch():
    device = await init(CONFIG, SWITCH_DOMAIN, LocalTuyaSwitch)
    entities: list[LocalTuyaSwitch] = get_entites(device)

    assert len(entities) > 0
    entity_sw1, entity_sw2, *_ = entities
    assert type(entity_sw1) is LocalTuyaSwitch

    assert entity_sw1.state == None
    device.status_updated(DPS_STATUS)

    assert entity_sw1.state == "on"
    assert entity_sw2.state == "off"
    assert entity_sw2.entity_category == EntityCategory.CONFIG


@pytest.mark.parametrize("gateway_id", [None, "registered_gateway"])
async def test_subdevice_device_info(monkeypatch, gateway_id):
    device = await init(CONFIG, SWITCH_DOMAIN, LocalTuyaSwitch)
    device._node_id = "subdevice_node"
    device.gateway = Mock(id="gateway")
    switch = get_entites(device)[0]
    switch.hass = device.hass

    def get_gateway_id(*args, **kwargs):
        if gateway_id is None:
            raise ValueError(
                "There is no device with identifier ('localtuya', 'local_gateway')"
            )
        return gateway_id

    monkeypatch.setattr(
        dr, "async_get_device_id_by_identifier", get_gateway_id, raising=False
    )
    registry = Mock()
    registry.async_get_device_by_identifier.return_value = (
        None if gateway_id is None else Mock(id=gateway_id)
    )
    get_registry = Mock(return_value=registry)
    monkeypatch.setattr(dr, "async_get", get_registry)

    device_info = switch.device_info

    if gateway_id is None:
        assert "via_device_id" not in device_info
    else:
        assert device_info["via_device_id"] == gateway_id
    get_registry.assert_called_once_with(switch.hass)
    registry.async_get_device_by_identifier.assert_called_once_with(
        ("localtuya", "local_gateway"), device._entry.entry_id
    )
