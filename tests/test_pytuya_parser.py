"""Test for localtuya pytuya parser."""

import struct

import pytest

from custom_components.localtuya.core.pytuya.const import (
    MAX_PAYLOAD_LENGTH,
    Affix,
    MessagesFormat,
)
from custom_components.localtuya.core.pytuya.parser import DecodeError, parse_header


def _header_55aa(payload_len: int) -> bytes:
    return struct.pack(
        MessagesFormat.HEADER_55AA, Affix.prefix_55aa.value, 0, 8, payload_len
    )


def _header_6699(payload_len: int) -> bytes:
    return struct.pack(
        MessagesFormat.HEADER_6699, Affix.prefix_6699.value, 0, 0, 8, payload_len
    )


@pytest.mark.parametrize("make_header", [_header_55aa, _header_6699])
@pytest.mark.parametrize("payload_len", [2683, 4795, MAX_PAYLOAD_LENGTH])
def test_parse_header_accepts_large_payloads(make_header, payload_len):
    """Frames over the old 2000-byte ceiling are valid (e.g. vacuum room lists)."""
    header = parse_header(make_header(payload_len))
    assert header.cmd == 8
    assert header.length == payload_len


@pytest.mark.parametrize("make_header", [_header_55aa, _header_6699])
@pytest.mark.parametrize("payload_len", [MAX_PAYLOAD_LENGTH + 1, 4154224665])
def test_parse_header_rejects_corrupt_lengths(make_header, payload_len):
    """Absurd lengths from a desynced stream are still rejected."""
    with pytest.raises(DecodeError):
        parse_header(make_header(payload_len))
