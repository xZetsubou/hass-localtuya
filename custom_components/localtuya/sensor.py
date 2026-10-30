"""Platform to present any Tuya DP as a sensor."""

import logging
import base64
import time
from datetime import timedelta
from functools import partial
from .config_flow import col_to_select

import voluptuous as vol
from homeassistant.components.sensor import (
    DEVICE_CLASSES_SCHEMA,
    DOMAIN,
    STATE_CLASSES_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ID,
    CONF_PLATFORM,
    CONF_UNIT_OF_MEASUREMENT,
    Platform,
    STATE_UNKNOWN,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_time_interval

from .entity import LocalTuyaEntity, async_setup_entry
from .const import CONF_ENERGY_POWER_DP, CONF_SCALING, CONF_OFFSET, CONF_STATE_CLASS

_LOGGER = logging.getLogger(__name__)

DEFAULT_PRECISION = 2

ATTR_POWER = "power"
ATTR_VOLTAGE = "voltage"
ATTR_CURRENT = "current"
MAP_UOM = {
    ATTR_CURRENT: UnitOfElectricCurrent.AMPERE,
    ATTR_VOLTAGE: UnitOfElectricPotential.VOLT,
    ATTR_POWER: UnitOfPower.KILO_WATT,
}

# Energy integrated from a power DP: devices only push power when it changes,
# so the total is also advanced on a timer while the device stays connected.
ENERGY_UPDATE_INTERVAL = timedelta(seconds=60)
# Watt-hours per unit of the energy sensor.
ENERGY_UNITS_WH = {
    UnitOfEnergy.WATT_HOUR: 1,
    UnitOfEnergy.KILO_WATT_HOUR: 1_000,
    UnitOfEnergy.MEGA_WATT_HOUR: 1_000_000,
}
# Watts per unit of the power DP.
POWER_UNITS_W = {UnitOfPower.WATT: 1, UnitOfPower.KILO_WATT: 1_000}


def flow_schema(dps):
    """Return schema used in config flow."""
    return {
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): str,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_STATE_CLASS): col_to_select(
            [sc.value for sc in SensorStateClass]
        ),
        vol.Optional(CONF_SCALING): vol.All(
            vol.Coerce(float), vol.Range(min=-1000000.0, max=1000000.0)
        ),
        vol.Optional(CONF_OFFSET): vol.All(
            vol.Coerce(float), vol.Range(min=-1000000.0, max=1000000.0)
        ),
        vol.Optional(CONF_ENERGY_POWER_DP): col_to_select(dps, is_dps=True),
    }


class LocalTuyaSensor(LocalTuyaEntity, SensorEntity):
    """Representation of a Tuya sensor."""

    def __init__(
        self,
        device,
        config_entry,
        sensorid,
        **kwargs,
    ):
        """Initialize the Tuya sensor."""
        super().__init__(device, config_entry, sensorid, _LOGGER, **kwargs)
        self._state = None

        self._has_sub_entities = False
        self._attr_device_class = self._config.get(CONF_DEVICE_CLASS)

        # Energy from power: integrate a power DP instead of reading this DP.
        self._power_dp = self._config.get(CONF_ENERGY_POWER_DP) or None
        self._energy_wh = 0.0
        self._power_w = None
        self._power_sampled_at = None
        if self._power_dp:
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            unit = self._config.get(CONF_UNIT_OF_MEASUREMENT)
            if unit not in ENERGY_UNITS_WH:
                unit = UnitOfEnergy.KILO_WATT_HOUR
            self._attr_native_unit_of_measurement = unit

    async def async_added_to_hass(self):
        """Advance the energy total periodically when integrating power."""
        await super().async_added_to_hass()

        if self._power_dp:
            self.async_on_remove(
                async_track_time_interval(
                    self.hass, self._energy_interval, ENERGY_UPDATE_INTERVAL
                )
            )

    @property
    def native_value(self):
        """Return sensor state."""
        return self._state

    @property
    def state_class(self) -> str | None:
        """Return state class."""
        return getattr(self, "_attr_state_class", self._config.get(CONF_STATE_CLASS))

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return getattr(
            self,
            "_attr_native_unit_of_measurement",
            self._config.get(CONF_UNIT_OF_MEASUREMENT),
        )

    def status_updated(self):
        """Device status was updated."""

        if self._power_dp:
            self._update_energy(self.power_value())
            return

        state = self.dp_value(self._dp_id)

        if self.is_base64(state):
            if not self._has_sub_entities:
                self.hass.loop.call_soon_threadsafe(
                    self.hass.async_create_task, self.__create_sub_sensors()
                )

            if None not in (
                sub_sensor := getattr(self, "_attr_sub_sensor", None),
                sub_sensor_state := self.decode_base64(state).get(sub_sensor),
            ):
                self._state = sub_sensor_state
            else:
                self._state = state
        else:
            self._state = self.scale(state)

    def status_restored(self, stored_state) -> None:
        super().status_restored(stored_state)

        if self._power_dp:
            try:
                energy = float(self._last_state)
            except (TypeError, ValueError):
                return
            self._energy_wh = energy * ENERGY_UNITS_WH[self.native_unit_of_measurement]
            self._state = self._energy_value()
            return

        if (last_state := self._last_state) and self.is_base64(last_state):
            self._status.update({self._dp_id: last_state})

    def power_value(self) -> float | None:
        """Return the power DP value in watts, scaled by the power DP's own entity."""
        value = self.dp_value(self._power_dp)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return None

        power_config = next(
            (
                entity
                for entity in self._device_config.entities
                if str(entity.get(CONF_ID)) == str(self._power_dp)
                and entity.get(CONF_PLATFORM) == DOMAIN
            ),
            {},
        )
        if (scale_factor := power_config.get(CONF_SCALING)) is not None:
            value = value * scale_factor
        if (offset := power_config.get(CONF_OFFSET)) is not None:
            value = value + offset
        unit = power_config.get(CONF_UNIT_OF_MEASUREMENT)
        return max(value * POWER_UNITS_W.get(unit, 1), 0)

    def _update_energy(self, power_w: float | None):
        """Add the energy used since the last sample (left Riemann sum)."""
        now = time.monotonic()
        if self._power_w is not None and self._power_sampled_at is not None:
            self._energy_wh += self._power_w * (now - self._power_sampled_at) / 3600

        self._power_w = power_w
        self._power_sampled_at = now if power_w is not None else None
        self._state = self._energy_value()
        if self._state is not None:
            self._last_state = self._state

    def _energy_interval(self, _now=None):
        """Advance the energy total while the power reading stays the same."""
        if not self._device.connected:
            # Nothing is known about the power while disconnected.
            self._power_w = self._power_sampled_at = None
            return

        self._update_energy(self.power_value())
        self.async_write_ha_state()

    def _energy_value(self) -> float:
        """Return the energy total in the sensor unit."""
        return round(
            self._energy_wh / ENERGY_UNITS_WH[self.native_unit_of_measurement], 4
        )

    # No need to restore state for a sensor
    async def restore_state_when_connected(self):
        """Do nothing for a sensor."""
        return

    def is_base64(self, data):
        """Return if the data is valid Tuya raw Base64 encoded data."""
        return (
            (data and isinstance(data, str))
            and len(data) >= 12
            and len(data) % 2 == 0
            and data.endswith("=")
        )

    def decode_base64(self, data):
        """Decode data base64 such as DPS phase_a."""
        buf = base64.b64decode(data)
        voltage = (buf[1] | buf[0] << 8) / 10
        current = (buf[4] | buf[3] << 8) / 1000
        power = (buf[7] | buf[6] << 8) / 1000
        return {ATTR_VOLTAGE: voltage, ATTR_CURRENT: current, ATTR_POWER: power}

    async def __create_sub_sensors(self):
        """Create sub entities for voltage, current and power and hide this parent sensor."""
        sub_entities = []

        for sensor in (ATTR_CURRENT, ATTR_POWER, ATTR_VOLTAGE):
            sub_entity = LocalTuyaSensor(
                self._device, self._device_config.as_dict(), self._dp_id
            )
            setattr(sub_entity, "_attr_sub_sensor", sensor)
            setattr(sub_entity, "_attr_unique_id", f"{self.unique_id}_{sensor}")
            setattr(sub_entity, "_attr_name", f"{self.name} {sensor.capitalize()}")
            setattr(sub_entity, "_attr_device_class", SensorDeviceClass(sensor))
            setattr(sub_entity, "_attr_state_class", SensorStateClass.MEASUREMENT)
            setattr(sub_entity, "_attr_native_unit_of_measurement", MAP_UOM[sensor])
            sub_entities.append(sub_entity)

        # Sub entities shouldn't have add entities attr.
        if sub_entities and self.componet_add_entities:
            self._has_sub_entities = True
            self.componet_add_entities(sub_entities)
            er.async_get(self.hass).async_update_entity(
                self.entity_id, hidden_by=er.RegistryEntryHider.INTEGRATION
            )


async_setup_entry = partial(async_setup_entry, DOMAIN, LocalTuyaSensor, flow_schema)
