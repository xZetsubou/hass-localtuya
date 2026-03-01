"""Constants for pytuya."""

from enum import IntEnum, Enum
from dataclasses import dataclass
from enum import Enum


class MessagesFormat:
    """Formats definitions for Tuya Devices messages."""

    RECV_HEADER = ">5I"  # Received message header: prefix, seqno, cmd, length, retcode
    HEADER = ">4I"  # Standard header: prefix, seqno, cmd, length
    HEADER_55AA = HEADER  # Same as HEADER, used for 0x55AA
    HEADER_6699 = ">IHIII"  # Header for 0x6699: prefix, unknown, seqno, cmd, length
    RETCODE = ">I"  # Return code: 1 uint32
    END = ">2I"  # End of message: crc, suffix
    END_55AA = END  # Same as END, used for 0x55AA
    END_HMAC = ">32sI"  # End with HMAC: 32-byte hmac, suffix
    END_6699 = ">16sI"  # End for 0x6699: 16-byte tag, suffix


@dataclass
class AffixData:
    value: int
    bin: bytes


class Affix:
    # 55aa common protocols.
    prefix_55aa = AffixData(0x000055AA, b"\x00\x00U\xaa")
    suffix_55aa = AffixData(0x0000AA55, b"\x00\x00\xaaU")
    # 6699 new protocols.
    prefix_6699 = AffixData(0x00006699, b"\x00\x00\x66\x99")
    suffix_6699 = AffixData(0x00009966, b"\x00\x00\x99\x66")

    prefixes = (prefix_55aa, prefix_6699)
    suffixes = (suffix_55aa, suffix_6699)


# Tuya Packet Format
# TuyaHeader = namedtuple("TuyaHeader", "prefix seqno cmd length total_length")
@dataclass
class TuyaHeader:
    prefix: int
    seqno: int
    cmd: int
    length: int
    total_length: int


@dataclass
class MessagePayload:
    # MessagePayload = namedtuple("MessagePayload", "cmd payload")
    cmd: int
    payload: bytes


@dataclass
class TuyaMessage:
    # MessagePayload = namedtuple("MessagePayload", "cmd payload")
    seqno: int
    cmd: int
    retcode: int
    payload: bytes
    crc: int
    crc_good: bool = True
    prefix: int = 0x55AA
    iv: bool = None


class SubdeviceState(IntEnum):
    ONLINE = 1
    OFFLINE = 2
    ABSENT = 3


# Tuya Command Types
# REF: https://github.com/tuya/tuya-iotos-embeded-sdk-wifi-ble-bk7231n/blob/master/sdk/include/lan_protocol.h
class CMDType(IntEnum):
    """Tuya commands type."""

    AP_CONFIG = 1  # FRM_TP_CFG_WF      # only used for ap 3.0 network config
    ACTIVE = 2  # FRM_TP_ACTV (discard) # WORK_MODE_CMD
    SESS_KEY_NEG_START = 3  # FRM_SECURITY_TYPE3 # negotiate session key
    SESS_KEY_NEG_RESP = 4  # FRM_SECURITY_TYPE4 # negotiate session key response
    SESS_KEY_NEG_FINISH = 5  # FRM_SECURITY_TYPE5 # finalize session key negotiation
    UNBIND = 6  # FRM_TP_UNBIND_DEV  # DATA_QUERT_CMD - issue command
    CONTROL = 7  # FRM_TP_CMD         # STATE_UPLOAD_CMD
    STATUS = 8  # FRM_TP_STAT_REPORT # STATE_QUERY_CMD
    HEART_BEAT = 9  # FRM_TP_HB
    DP_QUERY = 10  # FRM_QUERY_STAT      # UPDATE_START_CMD - get data points
    QUERY_WIFI = 11  # FRM_SSID_QUERY (discard) # UPDATE_TRANS_CMD
    TOKEN_BIND = 12  # FRM_USER_BIND_REQ   # GET_ONLINE_TIME_CMD - system time (GMT)
    CONTROL_NEW = 13  # FRM_TP_NEW_CMD      # FACTORY_MODE_CMD
    ENABLE_WIFI = 14  # FRM_ADD_SUB_DEV_CMD # WIFI_TEST_CMD
    WIFI_INFO = 15  # FRM_CFG_WIFI_INFO
    DP_QUERY_NEW = 16  # FRM_QUERY_STAT_NEW
    SCENE_EXECUTE = 17  # FRM_SCENE_EXEC
    UPDATEDPS = 18  # FRM_LAN_QUERY_DP    # Request refresh of DPS
    UDP_NEW = 19  # FR_TYPE_ENCRYPTION
    AP_CONFIG_NEW = 20  # FRM_AP_CFG_WF_V40
    BOARDCAST_LPV34 = 35  # FR_TYPE_BOARDCAST_LPV34
    LAN_EXT_STREAM = 64  # FRM_LAN_EXT_STREAM
