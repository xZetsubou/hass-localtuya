from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.setup import async_setup_component

from custom_components.localtuya.const import DOMAIN


async def test_async_setup(hass: HomeAssistant, config: ConfigType):
    assert await async_setup_component(hass, DOMAIN, config)
