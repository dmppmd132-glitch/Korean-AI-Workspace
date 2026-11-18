from __future__ import annotations

import sys
from ctypes import wintypes

from PySide6.QtCore import QObject, QTimer, Signal


class GlobalHotkeyError(RuntimeError):
    pass


class GlobalHotkeyService(QObject):
    """Register a process-wide Windows hotkey and emit triggered on WM_HOTKEY."""

    triggered = Signal()
    DEFAULT_SHORTCUT = "Ctrl+Shift+Space"
    _HOTKEY_ID = 0x4B41
    _MOD_CONTROL = 0x0002
    _MOD_SHIFT = 0x0004
    _MOD_ALT = 0x0001
    _WM_HOTKEY = 0x0312
    _PM_REMOVE = 0x0001

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._registered = False
        self._user32 = None
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._poll_messages)

    @property
    def supported(self) -> bool:
        return sys.platform == "win32"

    @property
    def registered(self) -> bool:
        return self._registered

    def start(self, shortcut: str = DEFAULT_SHORTCUT) -> bool:
        if not self.supported:
            return False
        if self._registered:
            return True
        modifiers, key = self._parse_shortcut(shortcut)
        import ctypes

        self._user32 = ctypes.windll.user32
        if not self._user32.RegisterHotKey(None, self._HOTKEY_ID, modifiers, key):
            error = ctypes.get_last_error()
            raise GlobalHotkeyError(f"無法啟用全域快捷鍵 {shortcut}，可能已被其他程式使用（Windows error {error}）")
        self._registered = True
        self._timer.start()
        return True

    def stop(self) -> None:
        if self._registered and self._user32 is not None:
            self._user32.UnregisterHotKey(None, self._HOTKEY_ID)
        self._registered = False
        self._timer.stop()

    def _poll_messages(self) -> None:
        if not self._registered or self._user32 is None:
            return
        import ctypes

        class _POINT(ctypes.Structure):
            _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

        class _MSG(ctypes.Structure):
            _fields_ = [
                ("hwnd", wintypes.HWND),
                ("message", wintypes.UINT),
                ("wParam", wintypes.WPARAM),
                ("lParam", wintypes.LPARAM),
                ("time", wintypes.DWORD),
                ("pt", _POINT),
            ]

        message = _MSG()
        while self._user32.PeekMessageW(ctypes.byref(message), None, self._WM_HOTKEY, self._WM_HOTKEY, self._PM_REMOVE):
            if message.message == self._WM_HOTKEY and message.wParam == self._HOTKEY_ID:
                self.triggered.emit()

    @classmethod
    def _parse_shortcut(cls, shortcut: str) -> tuple[int, int]:
        tokens = {token.strip().lower() for token in shortcut.split("+") if token.strip()}
        modifiers = 0
        if "ctrl" in tokens or "control" in tokens:
            modifiers |= cls._MOD_CONTROL
        if "shift" in tokens:
            modifiers |= cls._MOD_SHIFT
        if "alt" in tokens:
            modifiers |= cls._MOD_ALT
        key_tokens = tokens - {"ctrl", "control", "shift", "alt", "win", "meta"}
        if len(key_tokens) != 1 or not modifiers:
            raise ValueError("全域快捷鍵必須包含一個 Ctrl、Shift 或 Alt 修飾鍵及一個按鍵")
        key_name = next(iter(key_tokens))
        if len(key_name) == 1 and key_name.isalpha():
            key = ord(key_name.upper())
        elif len(key_name) == 1 and key_name.isdigit():
            key = ord(key_name)
        elif key_name.startswith("f") and key_name[1:].isdigit() and 1 <= int(key_name[1:]) <= 24:
            key = 0x70 + int(key_name[1:]) - 1
        else:
            key = {"space": 0x20, "enter": 0x0D, "escape": 0x1B, "tab": 0x09}.get(key_name, 0)
        if not key:
            raise ValueError(f"不支援的全域快捷鍵按鍵：{key_name}")
        return modifiers, key
