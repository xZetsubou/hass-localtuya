"""Test for localtuya sensor platform."""

from unittest.mock import MagicMock

from . import *
from custom_components.localtuya.sensor import LocalTuyaSensor, DOMAIN as PLATFORM_DOMAIN

# Raw 3-phase breaker payload -> 214.0 V, 1.2 A, 0.177 kW
PHASE_B64 = "CFwABLAAALE="
PHASE_DECODED = {"voltage": 214.0, "current": 1.2, "power": 0.177}

CONFIG = {
    DEVICE_NAME: {
        **DEVICE_CONFIG,
        "entities": [
            {
                "entity_category": "None",
                "friendly_name": "Phase A",
                "icon": "",
                "id": "6",
                "platform": PLATFORM_DOMAIN,
                "restore_on_reconnect": False,
            }
        ],
    }
}


async def test_decode_base64():
    """Raw base64 phase data is decoded into voltage/current/power."""
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaSensor)
    sensor, *_ = get_entites(device)

    assert type(sensor) is LocalTuyaSensor
    assert sensor.is_base64(PHASE_B64)
    assert not sensor.is_base64("500")
    assert sensor.decode_base64(PHASE_B64) == PHASE_DECODED


async def test_base64_status_creates_sub_sensors(monkeypatch):
    """A base64 phase DP spawns decoded voltage/current/power sub-sensors."""
    device = await init(CONFIG, PLATFORM_DOMAIN, LocalTuyaSensor)
    sensor, *_ = get_entites(device)
    sensor.entity_id = "sensor.phase_a"

    created = []
    sensor.componet_add_entities = lambda entities: created.extend(entities)
    monkeypatch.setattr(
        "custom_components.localtuya.sensor.er.async_get", lambda hass: MagicMock()
    )

    # Sub-sensor creation is scheduled on the event loop; run it synchronously.
    def run_coro(coro, **kwargs):
        try:
            coro.send(None)
        except StopIteration:
            pass

    sensor.hass.async_create_task = run_coro
    sensor.hass.loop = MagicMock()
    sensor.hass.loop.call_soon_threadsafe = lambda func, *args, **kwargs: func(*args)

    device.status_updated({"6": PHASE_B64})

    assert len(created) == 3
    assert {e._attr_sub_sensor for e in created} == {"voltage", "current", "power"}

    for sub in created:
        sub._status = {"6": PHASE_B64}
        sub.status_updated()
    assert {e._attr_sub_sensor: e.native_value for e in created} == PHASE_DECODED


ENERGY_CONFIG = {
    DEVICE_NAME: {
        **DEVICE_CONFIG,
        "entities": [
            {
                "friendly_name": "Electricity",
                "id": "17",
                "platform": PLATFORM_DOMAIN,
                "unit_of_measurement": "kWh",
                "scaling": 0.001,
                "energy_power_dp": "19",
            },
            {
                "friendly_name": "Power",
                "id": "19",
                "platform": PLATFORM_DOMAIN,
                "unit_of_measurement": "W",
                "scaling": 0.1,
            },
        ],
    }
}


class FakeClock:
    """Controllable time.monotonic replacement."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


async def init_energy_sensor(monkeypatch, config=ENERGY_CONFIG):
    clock = FakeClock()
    monkeypatch.setattr("custom_components.localtuya.sensor.time.monotonic", clock)
    device = await init(config, PLATFORM_DOMAIN, LocalTuyaSensor)
    energy, power = get_entites(device)
    return device, energy, power, clock


async def test_energy_from_power(monkeypatch):
    """Energy is integrated from the power DP, ignoring the sensor's own DP."""
    device, energy, power, clock = await init_energy_sensor(monkeypatch)

    assert energy.device_class == "energy"
    assert energy.state_class == "total_increasing"
    assert energy.native_unit_of_measurement == "kWh"

    # 100.0 W (raw 1000, scaled 0.1 by the power sensor) for one hour.
    device.status_updated({"17": 5, "19": 1000})
    assert energy.native_value == 0
    assert power.native_value == 100

    clock.now += 3600
    device.status_updated({"19": 500})
    assert energy.native_value == 0.1

    # Left Riemann sum: the half hour after the change uses the new 50 W.
    clock.now += 1800
    device.status_updated({"19": 0})
    assert energy.native_value == 0.125


async def test_energy_interval_advances_and_pauses_offline(monkeypatch):
    """The timer keeps the total moving and stops counting while offline."""
    device, energy, _, clock = await init_energy_sensor(monkeypatch)
    energy.async_write_ha_state = MagicMock()

    device._connected = True
    monkeypatch.setattr(type(device), "connected", property(lambda d: d._connected))

    device.status_updated({"19": 2000})  # 200 W
    clock.now += 1800
    energy._energy_interval()
    assert energy.native_value == 0.1
    energy.async_write_ha_state.assert_called_once()

    # Offline for an hour: nothing is added for that time.
    device._connected = False
    clock.now += 600
    energy._energy_interval()
    clock.now += 3000
    device._connected = True
    energy._energy_interval()
    assert energy.native_value == 0.1

    # Counting resumes from the reconnection.
    clock.now += 1800
    device.status_updated({"19": 2000})
    assert energy.native_value == 0.2


async def test_energy_restored_and_units(monkeypatch):
    """The total survives restarts, and the power unit/energy unit are honoured."""
    config = {
        DEVICE_NAME: {
            **DEVICE_CONFIG,
            "entities": [
                {
                    "friendly_name": "Energy",
                    "id": "17",
                    "platform": PLATFORM_DOMAIN,
                    "unit_of_measurement": "Wh",
                    "energy_power_dp": "19",
                },
                {
                    "friendly_name": "Power",
                    "id": "19",
                    "platform": PLATFORM_DOMAIN,
                    "unit_of_measurement": "kW",
                    "scaling": 0.001,
                },
            ],
        }
    }
    device, energy, _, clock = await init_energy_sensor(monkeypatch, config)
    assert energy.native_unit_of_measurement == "Wh"

    stored = MagicMock()
    stored.attributes = {"raw_state": 12.5}
    energy.status_restored(stored)
    assert energy.native_value == 12.5

    # Raw 1500 -> 1.5 kW for 6 minutes = 150 Wh; negative power is ignored.
    device.status_updated({"19": 1500})
    clock.now += 360
    device.status_updated({"19": -100})
    clock.now += 360
    device.status_updated({"19": 0})
    assert energy.native_value == 162.5
