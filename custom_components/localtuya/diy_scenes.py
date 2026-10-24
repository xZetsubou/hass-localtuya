"""Named, locally replayable Eternity Eave DIY scenes.

Saved scenes are per physical device, stored in Home Assistant's .storage. They
are not Tuya cloud scenes and do not change device firmware.
"""

import re

from homeassistant.components.select import SelectEntity
from homeassistant.const import CONF_DEVICES, CONF_HOST, CONF_PLATFORM
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.storage import Store

from .const import DOMAIN, CONF_NODE_ID

STORAGE_KEY = "localtuya_eternity_eave_diy_scenes"
# Header: 65 effect(2), speed(4), brightness(4), count-minus-one(1).
# Each color is #00RRGGBB. Other vendor formats are not accepted blindly.
DIY_RE = re.compile(r"65[0-9a-f]{10}([0-5])((?:#00[0-9a-f]{6}){1,6})\Z", re.I)


def valid_diy_code(value):
    """Only persist DIY mode values with a consistent 1-6 color count."""
    if not isinstance(value, str) or not (match := DIY_RE.fullmatch(value)):
        return False
    return len(match.group(2).split("#")) - 1 == int(match.group(1)) + 1


class DiySceneCatalog:
    """Shared HA storage and registered per-device select entities."""

    def __init__(self, hass):
        self.store = Store(hass, 1, STORAGE_KEY)
        self.saved = {}
        self.selects = {}

    async def load(self):
        self.saved = await self.store.async_load() or {}

    async def save(self, device_id, name, code):
        if not isinstance(name, str) or not name.strip() or len(name) > 100:
            raise HomeAssistantError("Scene name must be 1-100 characters")
        if not valid_diy_code(code):
            raise HomeAssistantError("Current DP 106 is not a valid 1-6 color DIY mode")
        name = name.strip()
        if (
            name not in self.saved.get(device_id, {})
            and len(self.saved.get(device_id, {})) >= 100
        ):
            raise HomeAssistantError("Maximum of 100 saved DIY scenes per device")
        self.saved.setdefault(device_id, {})[name] = code
        await self.store.async_save(self.saved)
        if entity := self.selects.get(device_id):
            entity.async_write_ha_state()

    async def delete(self, device_id, name):
        if name not in self.saved.get(device_id, {}):
            raise HomeAssistantError("Unknown saved DIY scene")
        del self.saved[device_id][name]
        await self.store.async_save(self.saved)
        if entity := self.selects.get(device_id):
            entity.async_write_ha_state()


class DiySceneSelect(SelectEntity):
    """DIY scene picker attached to the same HA device as its LocalTuya light."""

    _attr_has_entity_name = True
    _attr_name = "Saved DIY scene"
    _attr_icon = "mdi:palette"
    _attr_should_poll = False

    def __init__(self, device, catalog):
        self._device = device
        self._catalog = catalog
        self._id = device.id
        self._attr_unique_id = f"local_{self._id}_saved_diy_scene"
        self._attr_options = []
        self._status = {}

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._catalog.selects[self._id] = self
        self.async_on_remove(lambda: self._catalog.selects.pop(self._id, None))
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"localtuya_{self._id}", self._status_updated
            )
        )
        self._status_updated(self._device._status)

    def _status_updated(self, status):
        self._status = status or {}
        # Tuya coordinator can dispatch from a SyncWorker thread.
        self.schedule_update_ha_state()

    @property
    def device_info(self):
        return dr.DeviceInfo(identifiers={(DOMAIN, f"local_{self._id}")})

    @property
    def available(self):
        return bool(self._device.connected)

    @property
    def options(self):
        return list(self._catalog.saved.get(self._id, {}))

    @property
    def current_option(self):
        code = self._status.get("106")
        return next(
            (
                name
                for name, saved in self._catalog.saved.get(self._id, {}).items()
                if saved == code
            ),
            None,
        )

    async def async_select_option(self, option):
        if option not in self._catalog.saved.get(self._id, {}):
            raise HomeAssistantError("Unknown saved DIY scene")
        if not self.available:
            raise HomeAssistantError("LocalTuya device is disconnected")
        await self._device.set_dp(self._catalog.saved[self._id][option], 106)


def configured_device(hass, device_id):
    """Find a LocalTuya Eave light with locally readable mode DP 106."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if (config := entry.data.get(CONF_DEVICES, {}).get(device_id)) is None:
            continue
        # Require the explicit scene profile from the factory-scene PR. This
        # avoids adding vendor-specific controls to other Tuya dj lights.
        if not any(
            ent.get(CONF_PLATFORM) == "light"
            and str(ent.get("id")) == "20"
            and ent.get("scene_profile") == "eternity_eave"
            and str(ent.get("scene")) == "106"
            for ent in config.get("entities", [])
        ):
            raise HomeAssistantError("Device has not enabled Eternity Eave scenes")
        host = config[CONF_HOST]
        if node := config.get(CONF_NODE_ID):
            host = f"{host}_{node}"
        return hass.data[DOMAIN][entry.entry_id].devices[host], config
    raise HomeAssistantError("Unknown LocalTuya device")
