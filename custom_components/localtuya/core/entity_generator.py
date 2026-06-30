"""Generate LocalTuya entities from Tuya Cloud DP metadata."""

from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ENTITY_CATEGORY,
    CONF_FRIENDLY_NAME,
    CONF_ID,
    CONF_PLATFORM,
    CONF_UNIT_OF_MEASUREMENT,
    EntityCategory,
    Platform,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)

from ..const import (
    CONF_DPS_STRINGS,
    CONF_MAX_VALUE,
    CONF_MIN_VALUE,
    CONF_OPTIONS,
    CONF_PASSIVE_ENTITY,
    CONF_RESTORE_ON_RECONNECT,
    CONF_SCALING,
    CONF_STATE_CLASS,
    CONF_STATE_ON,
    CONF_STEPSIZE,
)

_LOGGER = logging.getLogger(__name__)

DEVICE_CLOUD_DATA = "device_cloud_data"

TYPE_BOOL = "bool"
TYPE_BITMAP = "bitmap"
TYPE_ENUM = "enum"
TYPE_STRING = "string"
TYPE_VALUE = "value"

READ_ONLY = "ro"

ENERGY_CODES = {"add_ele", "energy", "total_energy", "total_forward_energy"}
CURRENT_CODES = {
    "cur_current",
    "current",
    "phase_a_current",
    "phase_b_current",
    "phase_c_current",
}
POWER_CODES = {
    "cur_power",
    "power",
    "phase_a_power",
    "phase_b_power",
    "phase_c_power",
}
VOLTAGE_CODES = {
    "cur_voltage",
    "voltage",
    "phase_a_voltage",
    "phase_b_voltage",
    "phase_c_voltage",
}


def gen_cloud_entities(localtuya_data: dict, used_ids: set[str] | None = None) -> list[dict]:
    """Generate LocalTuya entity configs directly from Tuya Cloud metadata."""
    device_cloud_data = localtuya_data.get(DEVICE_CLOUD_DATA) or {}
    dps_data = device_cloud_data.get("dps_data") or {}
    detected_ids = _detected_ids(localtuya_data.get(CONF_DPS_STRINGS) or [])
    used_ids = {str(dp_id) for dp_id in used_ids or set()}

    if not dps_data:
        return []

    entities = []
    for dp_id, dp_data in sorted(dps_data.items(), key=lambda item: int(item[0])):
        dp_id = str(dp_id)
        if dp_id in used_ids:
            continue
        if detected_ids and dp_id not in detected_ids:
            continue

        entity = _entity_from_dp(dp_id, dp_data)
        if entity:
            entities.append(entity)

    _LOGGER.debug(
        "%s: Cloud entity generator created entities: %s",
        localtuya_data.get(CONF_FRIENDLY_NAME),
        entities,
    )
    return entities


def _detected_ids(dps_strings: list[str]) -> set[str]:
    """Extract DP IDs from LocalTuya friendly DPS strings."""
    return {dp.split(" ", 1)[0] for dp in dps_strings if dp}


def _entity_from_dp(dp_id: str, dp_data: dict[str, Any]) -> dict | None:
    """Convert a single Tuya DP metadata item into a LocalTuya entity config."""
    code = str(dp_data.get("code") or dp_id)
    dp_type = _dp_type(dp_data)
    values = _dp_values(dp_data)
    access_mode = str(dp_data.get("accessMode") or "").lower()
    writable = access_mode != READ_ONLY and "w" in access_mode

    base = {
        CONF_ID: dp_id,
        CONF_FRIENDLY_NAME: _friendly_name(dp_data, code),
    }

    if dp_type == TYPE_BOOL:
        if writable:
            return {
                **base,
                CONF_PLATFORM: Platform.SWITCH,
                CONF_RESTORE_ON_RECONNECT: False,
                CONF_PASSIVE_ENTITY: False,
            }
        return {
            **base,
            CONF_PLATFORM: Platform.BINARY_SENSOR,
            CONF_STATE_ON: "true",
            CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        }

    if dp_type == TYPE_ENUM:
        options = values.get("range") or []
        if writable and options:
            return {
                **base,
                CONF_PLATFORM: Platform.SELECT,
                CONF_OPTIONS: {option: _label(option) for option in options},
                CONF_RESTORE_ON_RECONNECT: False,
                CONF_PASSIVE_ENTITY: False,
                CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
            }
        return {
            **base,
            CONF_PLATFORM: Platform.SENSOR,
            CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        }

    if dp_type == TYPE_VALUE:
        if writable:
            return _number_entity(base, code, values)
        return _sensor_entity(base, code, values)

    if dp_type in (TYPE_BITMAP, TYPE_STRING):
        return {
            **base,
            CONF_PLATFORM: Platform.SENSOR,
            CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        }

    return None


def _number_entity(base: dict, code: str, values: dict[str, Any]) -> dict:
    """Build a number entity config from value type metadata."""
    return {
        **base,
        CONF_PLATFORM: Platform.NUMBER,
        CONF_MIN_VALUE: values.get("min", 0),
        CONF_MAX_VALUE: values.get("max", 100000),
        CONF_STEPSIZE: values.get("step", 1),
        CONF_SCALING: _scaling(values),
        CONF_UNIT_OF_MEASUREMENT: _sensor_unit(code, values.get("unit")),
        CONF_RESTORE_ON_RECONNECT: False,
        CONF_PASSIVE_ENTITY: False,
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
    }


def _sensor_entity(base: dict, code: str, values: dict[str, Any]) -> dict:
    """Build a sensor entity config from value type metadata."""
    normalized_code = code.lower()
    entity = {
        **base,
        CONF_PLATFORM: Platform.SENSOR,
        CONF_SCALING: _scaling(values),
        CONF_UNIT_OF_MEASUREMENT: _sensor_unit(code, values.get("unit")),
        CONF_STATE_CLASS: SensorStateClass.MEASUREMENT,
    }

    device_class = _sensor_device_class(code, values.get("unit"))
    if device_class:
        entity[CONF_DEVICE_CLASS] = device_class
    if normalized_code in ENERGY_CODES:
        entity[CONF_STATE_CLASS] = SensorStateClass.TOTAL_INCREASING

    return entity


def _dp_type(dp_data: dict[str, Any]) -> str:
    """Return normalized Tuya DP type."""
    values = _dp_values(dp_data)
    dp_type = dp_data.get("type") or values.get("type") or ""
    dp_type = str(dp_type).lower()
    if dp_type in ("boolean",):
        return TYPE_BOOL
    if dp_type in ("integer",):
        return TYPE_VALUE
    return dp_type


def _dp_values(dp_data: dict[str, Any]) -> dict[str, Any]:
    """Return parsed values/typeSpec metadata."""
    values = dp_data.get("values") or {}
    if isinstance(values, dict):
        return values
    if not values:
        return {}
    try:
        return json.loads(values)
    except (TypeError, json.JSONDecodeError):
        _LOGGER.debug("Unable to parse Tuya DP values: %s", values)
        return {}


def _friendly_name(dp_data: dict[str, Any], code: str) -> str:
    """Return the best available readable entity name."""
    return dp_data.get("custom_name") or _label(code)


def _label(value: str) -> str:
    """Turn Tuya code values into readable labels."""
    return str(value).replace("_", " ").strip().title()


def _scaling(values: dict[str, Any]) -> float:
    """Return LocalTuya scaling factor from Tuya scale metadata."""
    scale = values.get("scale", 0) or 0
    return 1 / (10 ** int(scale))


def _sensor_device_class(code: str, unit: str | None) -> SensorDeviceClass | None:
    """Infer Home Assistant sensor device class from Tuya code/unit."""
    code = code.lower()
    if code in CURRENT_CODES or unit == "mA":
        return SensorDeviceClass.CURRENT
    if code in POWER_CODES or unit == "W":
        return SensorDeviceClass.POWER
    if code in VOLTAGE_CODES or unit == "V":
        return SensorDeviceClass.VOLTAGE
    if code in ENERGY_CODES:
        return SensorDeviceClass.ENERGY
    return None


def _sensor_unit(code: str, unit: str | None) -> str | None:
    """Infer a Home Assistant unit from Tuya code/unit metadata."""
    code = code.lower()
    if code in CURRENT_CODES or unit == "mA":
        return UnitOfElectricCurrent.MILLIAMPERE
    if code in POWER_CODES or unit == "W":
        return UnitOfPower.WATT
    if code in VOLTAGE_CODES or unit == "V":
        return UnitOfElectricPotential.VOLT
    if code in ENERGY_CODES:
        return UnitOfEnergy.KILO_WATT_HOUR
    return unit
