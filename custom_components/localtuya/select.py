"""Platform to present any Tuya DP as an enumeration."""

import logging
from functools import partial

import voluptuous as vol
from homeassistant.components.select import DOMAIN, SelectEntity
from homeassistant.const import CONF_DEVICE_CLASS, CONF_DEVICES, STATE_UNKNOWN
from homeassistant.helpers import selector
from homeassistant.exceptions import HomeAssistantError

from .diy_scenes import DiySceneSelect, configured_device
from .entity import LocalTuyaEntity, async_setup_entry as setup_localtuya_entities
from .const import (
    CONF_DEFAULT_VALUE,
    CONF_OPTIONS,
    CONF_PASSIVE_ENTITY,
    CONF_RESTORE_ON_RECONNECT,
    DictSelector,
)


def flow_schema(dps):
    """Return schema used in config flow."""
    return {
        vol.Required(CONF_OPTIONS, default={}): selector.ObjectSelector(),
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
        for k, v in config_options.items():
            options[k] = str(v) if v else k.replace("_", "").capitalize()

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
        self.debug("Sending Option: " + option + " -> " + option_value)
        await self._device.set_dp(option_value, self._dp_id)

    def status_updated(self):
        """Device status was updated."""
        super().status_updated()

        if (state := self.dp_value(self._dp_id)) is not None:
            self._state_friendly = self._options.to_ha(state, state)

    # Default value is the first option
    def entity_default_value(self):
        """Return the first option as the default value for this entity type."""
        return self._options.names[0]


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up configured selects and a saved-DIY picker on supported lights."""
    await _setup_selects(hass, config_entry, async_add_entities)
    catalog = hass.data["localtuya"]["diy_scenes"]
    extra = []
    for dev_id in config_entry.data[CONF_DEVICES]:
        try:
            device, _ = configured_device(hass, dev_id)
        except HomeAssistantError:  # Other Tuya models must not get a DIY picker.
            continue
        extra.append(DiySceneSelect(device, catalog))
    if extra:
        async_add_entities(extra)


_setup_selects = partial(setup_localtuya_entities, DOMAIN, LocalTuyaSelect, flow_schema)
