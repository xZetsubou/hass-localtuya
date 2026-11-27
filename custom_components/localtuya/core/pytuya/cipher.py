""""""

import logging
import base64
import time
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

_LOGGER = logging.getLogger(__name__)


class AESCipher:
    """Cipher module for Tuya communication."""

    def __init__(self, key):
        """Initialize a new AESCipher."""
        self.block_size = 16
        self.key = key
        self.cipher = Cipher(algorithms.AES(key), modes.ECB(), default_backend())

    def encrypt(self, raw, use_base64=True, pad=True, iv=False, header=None):
        """Encrypt data to be sent to device."""
        if iv:
            if iv is True:
                if _LOGGER.isEnabledFor(logging.DEBUG):
                    iv = b"0123456789ab"
                else:
                    iv = str(time.time() * 10)[:12].encode("utf8")
            encryptor = Cipher(algorithms.AES(self.key), modes.GCM(iv)).encryptor()
            if header:
                encryptor.authenticate_additional_data(header)
            crypted_text = encryptor.update(raw) + encryptor.finalize()
            crypted_text = iv + crypted_text + encryptor.tag
        else:
            encryptor = self.cipher.encryptor()
            if pad:
                raw = self._pad(raw)
            crypted_text = encryptor.update(raw) + encryptor.finalize()
        return base64.b64encode(crypted_text) if use_base64 else crypted_text

    def decrypt(
        self, enc, use_base64=True, decode_text=True, iv=False, header=None, tag=None
    ):
        """Decrypt data from device."""
        if not iv:
            if use_base64:
                enc = base64.b64decode(enc)

        if iv:
            if iv is True:
                iv = enc[:12]
                enc = enc[12:]
            if tag is None:
                decryptor = Cipher(
                    algorithms.AES(self.key), modes.CTR(iv + b"\x00\x00\x00\x02")
                ).decryptor()
            else:
                decryptor = Cipher(
                    algorithms.AES(self.key), modes.GCM(iv, tag)
                ).decryptor()
            if header and (tag is not None):
                decryptor.authenticate_additional_data(header)
            raw = decryptor.update(enc) + decryptor.finalize()
        else:
            decryptor = self.cipher.decryptor()
            raw = decryptor.update(enc) + decryptor.finalize()
            raw = self._unpad(raw)

        return raw.decode("utf-8") if decode_text else raw

    def _pad(self, data):
        padnum = self.block_size - len(data) % self.block_size
        return data + padnum * chr(padnum).encode()

    @staticmethod
    def _unpad(data):
        return data[: -ord(data[len(data) - 1 :])]
