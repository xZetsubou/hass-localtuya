"""Saved DIY scene validation and selection."""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.localtuya.diy_scenes import (
    DiySceneCatalog,
    DiySceneSelect,
    valid_diy_code,
)
from homeassistant.exceptions import HomeAssistantError


@pytest.mark.parametrize("count", range(1, 7))
def test_valid_diy_color_count(count):
    code = "650001f403e8" + str(count - 1) + "#0019ff19" * count
    assert valid_diy_code(code)
    assert not valid_diy_code(code + "#00ff4600")


@pytest.mark.parametrize("code", ["", None, "361501f403e8", "650001f403e86#0019ff19"])
def test_reject_non_diy(code):
    assert not valid_diy_code(code)


@pytest.mark.asyncio
async def test_save_replace_select_delete_and_disconnect():
    catalog = DiySceneCatalog(Mock(data={}, config=Mock(config_dir="/tmp")))
    catalog.store = Mock(async_save=AsyncMock())
    device = Mock(
        id="fixture-id", connected=True, _status={"106": "650001f403e80#0019ff19"}
    )
    device.set_dp = AsyncMock()
    select = DiySceneSelect(device, catalog)
    select.async_write_ha_state = Mock()
    select.schedule_update_ha_state = Mock()
    select._status_updated(device._status)
    catalog.selects[device.id] = select
    await catalog.save(device.id, " Team Colors ", device._status["106"])
    assert select.options == ["Team Colors"]
    assert select.current_option == "Team Colors"
    await select.async_select_option("Team Colors")
    device.set_dp.assert_awaited_once_with("650001f403e80#0019ff19", 106)
    updated = "650501f403e81#0019ff19#00ff4600"
    await catalog.save(device.id, "Team Colors", updated)
    assert select.options == ["Team Colors"]
    assert select.current_option is None
    with pytest.raises(HomeAssistantError):
        await catalog.save(device.id, "Bad", "not a mode")
    device.connected = False
    with pytest.raises(HomeAssistantError):
        await select.async_select_option("Team Colors")
    await catalog.delete(device.id, "Team Colors")
    assert select.options == []
    assert catalog.store.async_save.await_count == 3
