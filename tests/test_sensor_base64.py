from custom_components.localtuya.sensor import (
    ATTR_CURRENT,
    ATTR_POWER,
    ATTR_VOLTAGE,
    LocalTuyaSensor,
)


class _DummySensor:
    def debug(self, *_args, **_kwargs):
        return None


def test_decode_base64_known_phase_payload():
    decoded = LocalTuyaSensor.decode_base64(_DummySensor(), "CJsAAEoAAAA=")

    assert decoded[ATTR_VOLTAGE] == 220.3
    assert decoded[ATTR_CURRENT] == 0.074
    assert decoded[ATTR_POWER] == 0.0


def test_decode_base64_invalid_payload_returns_empty_dict():
    decoded = LocalTuyaSensor.decode_base64(_DummySensor(), "not-valid-base64")

    assert decoded == {}
