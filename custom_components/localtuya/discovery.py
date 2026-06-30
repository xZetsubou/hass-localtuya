"""Discovery module for Tuya devices.

based on tuya-convert.py from tuya-convert:
    https://github.com/ct-Open-Source/tuya-convert/blob/master/scripts/tuya-discovery.py

Maintained by @xZetsubou
"""

import os
import asyncio
import json
import logging
import socket
from hashlib import md5
from socket import inet_aton

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .core.pytuya import parser

_LOGGER = logging.getLogger(__name__)

UDP_KEY = md5(b"yGAdlopoPVldABfn").digest()

PREFIX_55AA_BIN = b"\x00\x00U\xaa"
PREFIX_6699_BIN = b"\x00\x00\x66\x99"
UDP_COMMAND = b"\x00\x00\x00\x00"

DEFAULT_TIMEOUT = 60.0
DEFAULT_UDP_RCVBUF = 1024 * 1024


def _decode_text(value):
    """Decode bytes payloads into text while keeping text inputs unchanged."""
    if isinstance(value, bytes):
        return value.decode()
    return value


def _extract_55aa_payload(message):
    """Extract 55AA payload from packet length field, fallback to legacy slicing."""
    if len(message) < 24:
        raise ValueError("Packet too short")

    payload_len = int.from_bytes(message[12:16], "big")
    payload_start = 16
    payload_end = payload_start + payload_len

    if payload_end + 8 <= len(message):
        payload = message[payload_start:payload_end]
    else:
        payload = message[20:-8]

    # A few packets include a 4-byte return code prefix before plain JSON payload.
    if len(payload) >= 4 and payload[:4] == b"\x00\x00\x00\x00":
        return payload[4:]
    return payload


def decrypt(msg, key):
    def _unpad(data):
        return data[: -ord(data[len(data) - 1 :])]

    cipher = Cipher(algorithms.AES(key), modes.ECB(), default_backend())
    decryptor = cipher.decryptor()
    return _unpad(decryptor.update(msg) + decryptor.finalize()).decode()


def decrypt_udp(message):
    """Decrypt encrypted UDP broadcasts."""
    if message[:4] == PREFIX_55AA_BIN:
        payload = _extract_55aa_payload(message)
        if message[8:12] == UDP_COMMAND:
            return payload
        return decrypt(payload, UDP_KEY)
    if message[:4] == PREFIX_6699_BIN:
        unpacked = parser.unpack_message(message, hmac_key=UDP_KEY, no_retcode=None)
        payload = unpacked.payload.decode()
        # app sometimes has extra bytes at the end
        while payload and payload[-1] == chr(0):
            payload = payload[:-1]
        return payload
    return decrypt(message, UDP_KEY)


class TuyaDiscovery(asyncio.DatagramProtocol):
    """Datagram handler listening for Tuya broadcast messages."""

    def __init__(self, callback=None, progress_callback=None):
        """Initialize a new BaseDiscovery."""
        self.devices = {}
        self.stats = {
            "packets_total": 0,
            "packets_decrypted": 0,
            "packets_json": 0,
            "decode_failures": 0,
            "json_failures": 0,
            "devices_new": 0,
            "devices_ip_updated": 0,
            "devices_missing_fields": 0,
        }
        self._listeners = []
        self._callback = callback
        self._progress_callback = progress_callback
        self.log_messages = []

    def _socket_for_port(self, port):
        """Build UDP socket with receive buffer tuned for bursty discovery traffic."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if os.name != "nt" and hasattr(socket, "SO_REUSEPORT"):
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                # Ignore platforms where REUSEPORT exists but is restricted.
                pass
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, DEFAULT_UDP_RCVBUF)
        sock.bind(("0.0.0.0", port))
        sock.setblocking(False)
        return sock

    def sorted_devices(self):
        """Return devices sorted by IP for deterministic display in UI."""
        return dict(
            sorted(
                self.devices.items(),
                key=lambda item: inet_aton(item[1].get("ip", "0.0.0.0")),
            )
        )

    def _record_progress(self, message, progress=None):
        """Store and forward progress messages while scanning."""
        self.log_messages.append(message)
        if self._progress_callback:
            try:
                self._progress_callback(message, progress)
            except TypeError:
                self._progress_callback(message)

    async def start(self):
        """Start discovery by listening to broadcasts."""
        loop = asyncio.get_running_loop()
        listener = loop.create_datagram_endpoint(lambda: self, sock=self._socket_for_port(6666))
        encrypted_listener = loop.create_datagram_endpoint(
            lambda: self, sock=self._socket_for_port(6667)
        )
        self._listeners = await asyncio.gather(listener, encrypted_listener)

        # Some Tuya app broadcasts can arrive on UDP 7000.
        try:
            tuya_app_listener = await loop.create_datagram_endpoint(
                lambda: self,
                sock=self._socket_for_port(7000),
            )
            self._listeners.append(tuya_app_listener)
        except OSError as ex:
            _LOGGER.debug("Could not listen on UDP 7000: %s", ex)

        # Some devices/apps also broadcast on UDP 53115.
        try:
            tuya_alt_listener = await loop.create_datagram_endpoint(
                lambda: self,
                sock=self._socket_for_port(53115),
            )
            self._listeners.append(tuya_alt_listener)
        except OSError as ex:
            _LOGGER.debug("Could not listen on UDP 53115: %s", ex)

        self._record_progress("Aguardando broadcasts...", 0.0)
        _LOGGER.debug("Listening to broadcasts on UDP port 6666, 6667, 7000, 53115")

    def close(self):
        """Stop discovery."""
        self._callback = None
        for transport, _ in self._listeners:
            transport.close()

    def datagram_received(self, data, addr):
        """Handle received broadcast message."""
        self.stats["packets_total"] += 1
        source_ip = addr[0] if addr else "unknown"
        try:
            try:
                data = decrypt_udp(data)
                self.stats["packets_decrypted"] += 1
            except Exception:  # pylint: disable=broad-except
                self.stats["decode_failures"] += 1
                data = _decode_text(data)

            data = _decode_text(data)
            decoded = json.loads(data)
            self.stats["packets_json"] += 1
            self.device_found(decoded)
        except json.JSONDecodeError as ex:
            self.stats["json_failures"] += 1
            _LOGGER.debug(
                "Failed to decode broadcast from %r: %r [%s]", source_ip, data, ex
            )
        except Exception as ex:  # pylint: disable=broad-except
            # _LOGGER.debug("Bordcast from app from ip: %s", addr[0])
            _LOGGER.debug(
                "Failed to decode broadcast from %r: %r [%s]", source_ip, data, ex
            )

    def device_found(self, device):
        """Discover a new device."""
        gwid, ip = device.get("gwId"), device.get("ip")
        if not gwid:
            self.stats["devices_missing_fields"] += 1
            return

        # If device found but the ip changed.
        if gwid in self.devices and (self.devices[gwid].get("ip") != ip):
            self.stats["devices_ip_updated"] += 1
            self.devices.pop(gwid)

        if gwid not in self.devices:
            self.devices[gwid] = device
            self.stats["devices_new"] += 1

            self._record_progress(
                f"Dispositivo encontrado: {device.get('gwId')} em {device.get('ip')}"
            )
            _LOGGER.debug("Discovered device: %s", device)
        if self._callback:
            self._callback(device)


async def discover(progress_callback=None):
    """Discover and return devices on local network."""
    discovery = TuyaDiscovery(progress_callback=progress_callback)
    try:
        discovery._record_progress("Iniciando varredura Tuya", 0.0)
        await discovery.start()
        started_at = asyncio.get_running_loop().time()
        while True:
            elapsed = asyncio.get_running_loop().time() - started_at
            remaining = max(DEFAULT_TIMEOUT - elapsed, 0)
            progress = min(elapsed / DEFAULT_TIMEOUT, 1.0)
            discovery._record_progress(
                f"Aguardando broadcasts por {remaining:.0f}s", progress
            )
            if elapsed >= DEFAULT_TIMEOUT:
                break
            await asyncio.sleep(min(1.0, remaining))
    finally:
        stats = discovery.stats
        discovery._record_progress(
            "Resumo: "
            f"pacotes={stats['packets_total']}, "
            f"decriptados={stats['packets_decrypted']}, "
            f"json={stats['packets_json']}, "
            f"novos={stats['devices_new']}, "
            f"ip_atualizado={stats['devices_ip_updated']}, "
            f"falha_decode={stats['decode_failures']}, "
            f"falha_json={stats['json_failures']}"
        )
        discovery._record_progress("Varredura concluída", 1.0)
        discovery.close()
    return discovery.sorted_devices(), discovery.log_messages
