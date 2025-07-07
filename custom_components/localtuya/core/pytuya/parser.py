"""Tuya messages parser."""

import logging
import struct
import hmac
import binascii
from hashlib import md5, sha256
from .const import Affix, MessagesFormat, TuyaHeader, TuyaMessage
from .cipher import AESCipher

_LOGGER = logging.getLogger(__name__)


def pack_message(msg: TuyaMessage, hmac_key: bytes = None):
    """Pack a TuyaMessage into bytes."""
    if msg.prefix == Affix.prefix_55aa.value:
        header_fmt = MessagesFormat.HEADER_55AA
        end_fmt = MessagesFormat.END_HMAC if hmac_key else MessagesFormat.END_55AA
        msg_len = len(msg.payload) + struct.calcsize(end_fmt)
        header_data = (msg.prefix, msg.seqno, msg.cmd, msg_len)
    elif msg.prefix == Affix.prefix_6699.value:
        if not hmac_key:
            raise TypeError("key must be provided to pack 6699-format messages")
        header_fmt = MessagesFormat.HEADER_6699
        end_fmt = MessagesFormat.END_6699
        msg_len = len(msg.payload) + (struct.calcsize(end_fmt) - 4) + 12
        if type(msg.retcode) == int:
            msg_len += struct.calcsize(MessagesFormat.RETCODE)
        header_data = (msg.prefix, 0, msg.seqno, msg.cmd, msg_len)
    else:
        raise ValueError(
            "pack_message() cannot handle message format %08X" % msg.prefix
        )

    # Create full message excluding CRC and suffix
    data = struct.pack(header_fmt, *header_data)

    if msg.prefix == Affix.prefix_6699.value:
        cipher = AESCipher(hmac_key)
        if type(msg.retcode) == int:
            raw = struct.pack(MessagesFormat.RETCODE, msg.retcode) + msg.payload
        else:
            raw = msg.payload
        data2 = cipher.encrypt(
            raw,
            use_base64=False,
            pad=False,
            iv=True if not msg.iv else msg.iv,
            header=data[4:],
        )
        data += data2 + Affix.suffix_6699.bin
    else:
        data += msg.payload
        if hmac_key:
            crc = hmac.new(hmac_key, data, sha256).digest()
        else:
            crc = binascii.crc32(data) & 0xFFFFFFFF
        # Calculate CRC, add it together with suffix
        data += struct.pack(end_fmt, crc, Affix.suffix_55aa.value)

    return data


def unpack_message(
    data: bytes, hmac_key=None, header=None, no_retcode=False, logger=_LOGGER
):
    """Unpack bytes into a TuyaMessage."""
    if header is None:
        header = parse_header(data)

    if header.prefix == Affix.prefix_55aa.value:
        # 4-word header plus return code
        header_len = struct.calcsize(MessagesFormat.HEADER_55AA)
        end_fmt = MessagesFormat.END_HMAC if hmac_key else MessagesFormat.END_55AA
        retcode_len = 0 if no_retcode else struct.calcsize(MessagesFormat.RETCODE)
        msg_len = header_len + header.length
    elif header.prefix == Affix.prefix_6699.value:
        if not hmac_key:
            raise TypeError("key must be provided to unpack 6699-format messages")
        header_len = struct.calcsize(MessagesFormat.HEADER_6699)
        end_fmt = MessagesFormat.END_6699
        retcode_len = 0
        msg_len = header_len + header.length + 4
    else:
        raise ValueError(
            "unpack_message() cannot handle message format %08X" % header.prefix
        )

    if len(data) < msg_len:
        logger.debug(
            "unpack_message(): not enough data to unpack payload! need %d but only have %d",
            header_len + header.length,
            len(data),
        )
        raise DecodeError(f"Not enough data to unpack payload: {data}")

    end_len = struct.calcsize(end_fmt)
    # the retcode is technically part of the payload, but strip it as we do not want it here
    retcode = (
        0
        if not retcode_len
        else struct.unpack(
            MessagesFormat.RETCODE, data[header_len : header_len + retcode_len]
        )[0]
    )
    payload = data[header_len + retcode_len : msg_len]
    crc, suffix = struct.unpack(end_fmt, payload[-end_len:])
    payload = payload[:-end_len]

    if header.prefix == Affix.prefix_55aa.value:
        if hmac_key:
            have_crc = hmac.new(
                hmac_key, data[: (header_len + header.length) - end_len], sha256
            ).digest()
        else:
            have_crc = (
                binascii.crc32(data[: (header_len + header.length) - end_len])
                & 0xFFFFFFFF
            )

        if suffix != Affix.prefix_55aa.value:
            logger.debug(
                "Suffix prefix wrong! %08X != %08X", suffix, Affix.suffix_55aa.value
            )

        if crc != have_crc:
            if hmac_key:
                logger.debug(
                    "HMAC checksum wrong! %r != %r",
                    binascii.hexlify(have_crc),
                    binascii.hexlify(crc),
                )
            else:
                logger.debug("CRC wrong! %08X != %08X", have_crc, crc)
        crc_good = crc == have_crc
        iv = None
    elif header.prefix == Affix.prefix_6699.value:
        iv = payload[:12]
        payload = payload[12:]
        try:
            cipher = AESCipher(hmac_key)
            payload = cipher.decrypt(
                payload,
                use_base64=False,
                decode_text=False,
                iv=iv,
                header=data[4:header_len],
                tag=crc,
            )
            crc_good = True
        except:
            crc_good = False

        retcode_len = struct.calcsize(MessagesFormat.RETCODE)
        if no_retcode is False:
            pass
        elif (
            no_retcode is None
            and payload[0:1] != b"{"
            and payload[retcode_len : retcode_len + 1] == b"{"
        ):
            retcode_len = struct.calcsize(MessagesFormat.RETCODE)
        else:
            retcode_len = 0
        if retcode_len:
            retcode = struct.unpack(MessagesFormat.RETCODE, payload[:retcode_len])[0]
            payload = payload[retcode_len:]

    return TuyaMessage(
        header.seqno, header.cmd, retcode, payload, crc, crc_good, header.prefix, iv
    )


def parse_header(data: bytes, logger=_LOGGER):
    """Unpack bytes into a TuyaHeader."""
    if data[:4] == Affix.prefix_6699.bin:
        fmt = MessagesFormat.HEADER_6699
    elif data[:4] == Affix.prefix_55aa.bin:
        fmt = MessagesFormat.HEADER_55AA
    else:
        err = f"Prefix Does not match! {prefix} known {set(p for p in Affix.prefixes)}"
        logger.error(err)
        raise DecodeError(err)

    header_len = struct.calcsize(fmt)

    if len(data) < header_len:
        err = "Not enough data to unpack header"
        logger.error(err)
        raise DecodeError(err)

    unpacked = struct.unpack(fmt, data[:header_len])
    prefix = unpacked[0]

    if prefix == Affix.prefix_55aa.value:
        prefix, seqno, cmd, payload_len = unpacked
        total_length = payload_len + header_len
    elif prefix == Affix.prefix_6699.value:
        prefix, unknown, seqno, cmd, payload_len = unpacked
        # seqno |= unknown << 32
        total_length = payload_len + header_len + len(Affix.suffix_6699.bin)
    else:
        err = f"Prefix Does not match! {prefix} known {set(p for p in Affix.prefixes)}"
        logger.error(err)
        raise DecodeError(err)

    # sanity check. currently the max payload length is somewhere around 300 bytes
    if payload_len > 2000:
        err = f"Header claims the packet size is over 2000 bytes!  It is most likely corrupt. Claimed size: {payload_len} bytes. fmt: {fmt} unpacked: {unpacked}"
        logger.error(err)
        raise DecodeError(err)

    return TuyaHeader(prefix, seqno, cmd, payload_len, total_length)


class DecodeError(Exception):
    """Specific Exception caused by decoding error."""

    pass
