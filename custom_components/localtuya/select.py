"""Platform to present any Tuya DP as an enumeration."""

import logging
from functools import partial

import voluptuous as vol
from homeassistant.components.select import DOMAIN, SelectEntity
from homeassistant.const import CONF_DEVICE_CLASS, STATE_UNKNOWN
from homeassistant.helpers import selector

from .entity import LocalTuyaEntity, async_setup_entry
from .const import (
    CONF_DEFAULT_VALUE,
    CONF_OPTIONS,
    CONF_PASSIVE_ENTITY,
    CONF_RESTORE_ON_RECONNECT,
    CONF_SELECT_DPS_TYPE,
    DictSelector,
)


def flow_schema(dps):
    """Return schema used in config flow."""
    return {
        vol.Required(CONF_OPTIONS, default={}): selector.ObjectSelector(),
        vol.Optional(CONF_SELECT_DPS_TYPE, default="auto"): vol.In(
            ["auto", "int", "str"]
        ),
        vol.Required(CONF_RESTORE_ON_RECONNECT): bool,
        vol.Required(CONF_PASSIVE_ENTITY): bool,
        vol.Optional(CONF_DEFAULT_VALUE): str,
    }


_LOGGER = logging.getLogger(__name__)


class LocalTuyaSelect(LocalTuyaEntity, SelectEntity):
    """Representation of a Tuya Enumeration."""

    def __init__(
        self,
        device,
        config_entry,
        sensorid,
        **kwargs,
    ):
        """Initialize the Tuya sensor."""
        super().__init__(device, config_entry, sensorid, _LOGGER, **kwargs)
        self._state = STATE_UNKNOWN
        self._state_friendly = ""

        # Set Display options
        options = {}
        config_options: dict = self._config.get(CONF_OPTIONS, {})
        if not isinstance(config_options, dict):
            self.warning(
                f"{self.name} DPiD: {self._dp_id}: Options configured incorrectly!"
                + "It must be in the format of key-value pairs,"
                + "where each line follows the structure [device_value: friendly name]"
            )
            config_options = {}
        numeric_options = bool(config_options) and all(
            str(key).lstrip("-").isdigit() for key in config_options
        )
        if numeric_options:
            config_options = dict(
                sorted(config_options.items(), key=lambda item: int(item[0]))
            )
        for k, v in config_options.items():
            key = str(k)
            options[key] = str(v) if v else key.replace("_", "").capitalize()

        self._options = DictSelector(options)

    @property
    def current_option(self) -> str:
        """Return the current value."""
        return self._state_friendly

    @property
    def options(self) -> list:
        """Return the list of values."""
        return self._options.names

    @property
    def device_class(self):
        """Return the class of this device."""
        return self._config.get(CONF_DEVICE_CLASS)

    async def async_select_option(self, option: str) -> None:
        """Update the current value."""
        option_value = self._options.to_tuya(option)
        current_value = self.dp_value(self._dp_id)
        value_type = self._config.get(CONF_SELECT_DPS_TYPE, "auto")
        if value_type == "int" or (
            value_type == "auto"
            and isinstance(current_value, int)
            and not isinstance(current_value, bool)
        ):
            option_value = int(option_value)
        self.debug(f"Sending Option: {option} -> {option_value}")
        await self._device.set_dp(option_value, self._dp_id)

    def status_updated(self):
        """Device status was updated."""
        super().status_updated()

        if (state := self.dp_value(self._dp_id)) is not None:
            self._state_friendly = self._options.to_ha(str(state), str(state))

    # Default value is the first option
    def entity_default_value(self):
        """Return the first option as the default value for this entity type."""
        return self._options.names[0]


async_setup_entry = partial(async_setup_entry, DOMAIN, LocalTuyaSelect, flow_schema)
