from __future__ import annotations

from base64 import b64decode, b64encode
import ctypes
from ctypes import POINTER, Structure, byref, c_char
from ctypes.wintypes import DWORD
import sys


class DATA_BLOB(Structure):
    _fields_ = [("cbData", DWORD), ("pbData", POINTER(c_char))]


class SecretCipher:
    """Windows DPAPI-based secret encryption.

    Uses CryptProtectData / CryptUnprotectData to encrypt and decrypt
    secret values. Keys are bound to the current Windows user account.
    """

    def __init__(self, purpose: str = "GoBot") -> None:
        self._purpose = purpose

    def encrypt(self, value: str) -> str:
        if sys.platform != "win32":
            raise RuntimeError("Secret encryption currently requires Windows DPAPI")

        payload = value.encode("utf-8")
        in_blob = DATA_BLOB(len(payload), ctypes.cast(ctypes.create_string_buffer(payload), POINTER(c_char)))
        out_blob = DATA_BLOB()

        if not ctypes.windll.crypt32.CryptProtectData(  # type: ignore[attr-defined]
            byref(in_blob),
            self._purpose,
            None,
            None,
            None,
            0,
            byref(out_blob),
        ):
            raise OSError("Failed to encrypt secret")

        try:
            encrypted = ctypes.string_at(out_blob.pbData, out_blob.cbData)
            return b64encode(encrypted).decode("ascii")
        finally:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)  # type: ignore[attr-defined]

    def decrypt(self, value: str) -> str:
        if sys.platform != "win32":
            raise RuntimeError("Secret encryption currently requires Windows DPAPI")

        payload = b64decode(value.encode("ascii"))
        in_blob = DATA_BLOB(len(payload), ctypes.cast(ctypes.create_string_buffer(payload), POINTER(c_char)))
        out_blob = DATA_BLOB()

        if not ctypes.windll.crypt32.CryptUnprotectData(  # type: ignore[attr-defined]
            byref(in_blob),
            None,
            None,
            None,
            None,
            0,
            byref(out_blob),
        ):
            raise OSError("Failed to decrypt secret")

        try:
            decrypted = ctypes.string_at(out_blob.pbData, out_blob.cbData)
            return decrypted.decode("utf-8")
        finally:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)  # type: ignore[attr-defined]
