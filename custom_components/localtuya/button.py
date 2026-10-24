"""Platform to locally control Tuya-based button devices."""

import logging
from functools import partial

import voluptuous as vol
from homeassistant.components.button import DOMAIN, ButtonEntity
from homeassistant.components.logbook import log_entry

from .entity import LocalTuyaEntity, async_setup_entry
from .const import CONF_BUTTON_LOG_DP_CHANGES, CONF_BUTTON_PRESS_VALUE

_LOGGER = logging.getLogger(__name__)


def flow_schema(dps):
    """Return schema used in config flow."""
    return {
        vol.Optional(CONF_BUTTON_PRESS_VALUE): vol.Coerce(int),
        vol.Optional(CONF_BUTTON_LOG_DP_CHANGES, default=False): bool,
    }


class LocalTuyaButton(LocalTuyaEntity, ButtonEntity):
    """Representation of a Tuya button."""

    def __init__(
        self,
        device,
        config_entry,
        buttonid,
        **kwargs,
    ):
        """Initialize the Tuya button."""
        super().__init__(device, config_entry, buttonid, _LOGGER, **kwargs)
        self._state = None
        self._last_reported_value = None

    def status_updated(self):
        """Log a reported DP change without assuming where it originated."""
        super().status_updated()
        if not self._config.get(CONF_BUTTON_LOG_DP_CHANGES):
            return

        value = self.dp_value(self._dp_id)
        if (
            self._last_reported_value is not None
            and value is not None
            and value != self._last_reported_value
            and self.entity_id
        ):
            # Status callbacks can also run in a worker thread during setup.
            log_entry(
                self.hass,
                self.name,
                "reported a change",
                entity_id=self.entity_id,
            )
        self._last_reported_value = value

    async def async_press(self):
        """Press the button."""
        await self._device.set_dp(
            self._config.get(CONF_BUTTON_PRESS_VALUE, True), self._dp_id
        )


async_setup_entry = partial(async_setup_entry, DOMAIN, LocalTuyaButton, flow_schema)
