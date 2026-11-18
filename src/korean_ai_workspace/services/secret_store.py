from __future__ import annotations

import base64
import ctypes
import os
import sys
from ctypes import wintypes
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


class SecretStoreError(RuntimeError):
    pass


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


class SecretStore:
    """Encrypt small secrets with Windows DPAPI, with a local Fernet fallback for development."""

    def __init__(self, config_directory: Path):
        self.config_directory = Path(config_directory)
        self.config_directory.mkdir(parents=True, exist_ok=True)
        self.fallback_key_path = self.config_directory / "secret.key"

    @property
    def backend(self) -> str:
        return "windows-dpapi" if sys.platform == "win32" else "local-fernet"

    def encrypt(self, value: str) -> str:
        if not value:
            return ""
        raw = value.encode("utf-8")
        if sys.platform == "win32":
            try:
                return "dpapi:v1:" + base64.b64encode(self._dpapi_protect(raw)).decode("ascii")
            except OSError as exc:
                raise SecretStoreError("Windows DPAPI 加密失敗，API Key 未保存") from exc
        token = Fernet(self._fallback_key()).encrypt(raw)
        return "fernet:v1:" + token.decode("ascii")

    def decrypt(self, encrypted: str) -> str:
        if not encrypted:
            return ""
        try:
            prefix, version, payload = encrypted.split(":", 2)
            if version != "v1":
                raise ValueError("不支援的密文版本")
            if prefix == "dpapi":
                if sys.platform != "win32":
                    raise SecretStoreError("此 API Key 使用 Windows DPAPI，只能在原 Windows 環境還原")
                raw = self._dpapi_unprotect(base64.b64decode(payload))
            elif prefix == "fernet":
                raw = Fernet(self._fallback_key()).decrypt(payload.encode("ascii"))
            else:
                raise ValueError("不支援的密文格式")
            return raw.decode("utf-8")
        except (ValueError, InvalidToken, UnicodeDecodeError, OSError) as exc:
            raise SecretStoreError("API Key 解密失敗；可能不是同一台電腦或設定檔已損毀") from exc

    def _fallback_key(self) -> bytes:
        if not self.fallback_key_path.exists():
            self.fallback_key_path.write_bytes(Fernet.generate_key())
            try:
                os.chmod(self.fallback_key_path, 0o600)
            except OSError:
                pass
        return self.fallback_key_path.read_bytes()

    @staticmethod
    def _blob(data: bytes):
        buffer = ctypes.create_string_buffer(data)
        return _DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer

    def _dpapi_protect(self, data: bytes) -> bytes:
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        source, source_buffer = self._blob(data)
        target = _DATA_BLOB()
        if not crypt32.CryptProtectData(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(target)):
            raise OSError(ctypes.get_last_error(), "CryptProtectData failed")
        try:
            return ctypes.string_at(target.pbData, target.cbData)
        finally:
            kernel32.LocalFree(target.pbData)

    def _dpapi_unprotect(self, data: bytes) -> bytes:
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        source, source_buffer = self._blob(data)
        target = _DATA_BLOB()
        if not crypt32.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(target)):
            raise OSError(ctypes.get_last_error(), "CryptUnprotectData failed")
        try:
            return ctypes.string_at(target.pbData, target.cbData)
        finally:
            kernel32.LocalFree(target.pbData)
