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
