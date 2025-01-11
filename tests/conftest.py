from typing import Any
import pytest

from homeassistant.const import CONF_DISCOVERY

from custom_components.localtuya import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    return


@pytest.fixture(name="config")
def config_fixture() -> dict[str, Any]:
    return {
        DOMAIN: {
            CONF_DISCOVERY: False,
        },
    }
