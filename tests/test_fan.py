"""Test for localtuya."""

from . import *
import math
from copy import deepcopy
from unittest.mock import patch
from custom_components.localtuya.entity import _registry_device_id
from custom_components.localtuya.fan import LocalTuyaFan, DOMAIN as PLATFORM_DOMAIN
from homeassistant.util.percentage import (
    int_states_in_range,
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

CONFIG = {
    DEVICE_NAME: {
        **DEVICE_CONFIG,
        "entities": [
            {
                "friendly_name": "Fan",
                "entity_category": "config",
                "fan_speed_control": "3",
                "fan_direction": "4",
                "fan_direction_forward": "forward",
                "fan_direction_reverse": "reverse",
                "fan_speed_min": 1,
                "fan_speed_max": 6,
                "fan_speed_ordered_list": "disabled",
                "id": "1",
                "platform": "fan",
                "icon": "",
                "fan_oscillating_control": "6",
            },
            {
                "friendly_name": "Fan",
                "entity_category": "config",
                "fan_speed_control": "2",
                "fan_direction": "4",
                "fan_direction_forward": "forward",
                "fan_direction_reverse": "reverse",
                "fan_speed_min": 1,
                "fan_speed_max": 6,
                "fan_speed_ordered_list": "low,mid,high,max",
                "id": "21",
                "platform": "fan",
                "icon": "",
            },
        ],
    }
}

DPS_STATUS = {"1": True, "2": "mid", "3": 4, "4": "reverse", "6": True}


def test_registry_device_lookup_is_scoped_to_config_entry():
    with patch("custom_components.localtuya.entity.dr.async_get") as registry:
        device = registry.return_value.async_get_device.return_value
        device.id = "physical-parent"
        device.config_entries = {"correct-entry"}

        assert (
            _registry_device_id(None, "local_fan", "correct-entry") == "physical-parent"
        )
        assert _registry_device_id(None, "local_fan", "other-entry") is None
        registry.return_value.async_get_device.assert_called_with(
            identifiers={("localtuya", "local_fan")}
        )


async def test_fan():
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaFan)
    entities: list[LocalTuyaFan] = get_entites(device)

    assert len(entities) > 0
    entity_1, entity_2, *_ = entities
    assert type(entity_1) is LocalTuyaFan

    status = DPS_STATUS.copy()
    assert not entity_1.is_on
    device.status_updated(status)

    assert entity_1.is_on
    assert (
        entity_1.current_direction
        == status[CONFIG[DEVICE_NAME]["entities"][0]["fan_direction"]]
    )
    assert entity_1.oscillating == True

    speed_range = entity_1._speed_range
    speed_percentage = ranged_value_to_percentage(
        speed_range, status[CONFIG[DEVICE_NAME]["entities"][0]["fan_speed_control"]]
    )
    assert entity_1.percentage == speed_percentage

    assert percentage_to_ranged_value(speed_range, 100) == 6
    assert math.ceil(percentage_to_ranged_value(speed_range, 1)) == 1

    # Order speed.
    speed_range = entity_2._ordered_list
    speed_percentage = ordered_list_item_to_percentage(speed_range, "mid")
    assert entity_2.percentage == speed_percentage
    assert percentage_to_ordered_list_item(speed_range, 0) == speed_range[0]
    assert percentage_to_ordered_list_item(speed_range, 100) == speed_range[-1]


async def test_first_speed_step_rounds_to_one():
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaFan)
    fan = get_entites(device)[0]
    device.status_updated(DPS_STATUS)
    device.set_dp = AsyncMock()
    fan.schedule_update_ha_state = Mock()

    await fan.async_set_percentage(17)

    device.set_dp.assert_awaited_once_with(1, "3")


async def test_fan_group_uses_connected_child_device():
    config = deepcopy(CONFIG)
    config[DEVICE_NAME]["entities"][0]["device_group"] = "fan"
    with patch("custom_components.localtuya.entity.dr.async_get") as registry:
        device = await init(config, PLATFORM_DOMAIN, LocalTuyaFan)
    registry.return_value.async_get_or_create.assert_called_once()
    parent = registry.return_value.async_get_or_create.call_args.kwargs
    assert parent["model"] == f"Tuya generic ({device.id})"
    fan = get_entites(device)[0]
    with patch(
        "custom_components.localtuya.entity._registry_device_id",
        return_value="physical-parent",
    ):
        info = fan.device_info

    assert info["via_device_id"] == "physical-parent"
    assert info["identifiers"] == {("localtuya", f"local_{device.id}_fan")}


async def test_gateway_child_uses_device_id_link():
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaFan)
    device._node_id = "child-node"
    device.gateway = Mock(id="gateway")
    fan = get_entites(device)[0]

    with patch(
        "custom_components.localtuya.entity.dr.async_get_device_id_by_identifier",
        return_value="gateway-parent",
        create=True,
    ):
        info = fan.device_info

    assert info["via_device_id"] == "gateway-parent"
