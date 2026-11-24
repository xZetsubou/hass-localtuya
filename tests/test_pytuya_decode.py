"""Test decoding of payloads received from devices."""

import pytest

from custom_components.localtuya.core.pytuya import TuyaProtocol
from custom_components.localtuya.core.pytuya.cipher import AESCipher

KEY = b"0123456789abcdef"
ERR_PAYLOAD = "904"
ERR_JSON = "900"


def make_protocol(key, version):
    """Create a protocol with only what decoding needs."""
    protocol = object.__new__(TuyaProtocol)
    protocol.id = "device"
    protocol.local_key = key
    protocol.version = version
    protocol.version_bytes = str(version).encode()
    protocol.version_header = protocol.version_bytes + b"\0" * 12
    protocol.dev_type = "type_0a"
    protocol.dispatched_dps = {}
    protocol.debug = lambda *args, **kwargs: None
    return protocol


def decode(raw, version=3.3, encrypt_key=KEY, decode_key=KEY):
    """Encrypt raw with one key and decode it with another."""
    payload = AESCipher(encrypt_key).encrypt(raw, False)
    return make_protocol(decode_key, version)._decode_payload(payload)


@pytest.mark.parametrize("version", [3.3, 3.4])
def test_valid_utf8(version):
    """Valid payloads, including non-ASCII ones, are unchanged."""
    raw = '{"dps":{"1":true,"2":"21\u00b0C"}}'.encode()
    assert decode(raw, version)["dps"] == {"1": True, "2": "21\u00b0C"}


@pytest.mark.parametrize("version", [3.3, 3.4])
def test_invalid_utf8_in_dp(version):
    """Invalid bytes in one DP do not discard the other DPs."""
    raw = b'{"dps":{"1":true,"3":2,"109":"\xff\xff"}}'
    dps = decode(raw, version)["dps"]
    assert dps == {"1": True, "3": 2, "109": "\ufffd\ufffd"}


@pytest.mark.parametrize("version, error", [(3.3, ERR_PAYLOAD), (3.4, ERR_JSON)])
def test_invalid_utf8_not_json_is_rejected(version, error):
    """Undecodable data that is not a JSON object is still an error."""
    for raw in (b"\xff\xfe not json", b'["\xff"]'):
        assert decode(raw, version)["Err"] == error


def test_wrong_key_is_rejected():
    """A wrong local_key never yields DPs."""
    raw = b'{"dps":{"1":true,"109":"\xff\xff"}}'
    for i in range(500):
        assert "dps" not in decode(raw, decode_key=b"%016d" % i)
