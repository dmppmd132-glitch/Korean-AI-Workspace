from __future__ import annotations

import sys

import pytest

from korean_ai_workspace.services.global_hotkey import GlobalHotkeyService


def test_default_global_hotkey_is_parseable():
    modifiers, key = GlobalHotkeyService._parse_shortcut(GlobalHotkeyService.DEFAULT_SHORTCUT)
    assert modifiers == GlobalHotkeyService._MOD_CONTROL | GlobalHotkeyService._MOD_SHIFT
    assert key == 0x20


def test_global_hotkey_rejects_shortcut_without_modifier():
    with pytest.raises(ValueError):
        GlobalHotkeyService._parse_shortcut("Space")


def test_global_hotkey_is_disabled_on_non_windows():
    service = GlobalHotkeyService()
    if sys.platform == "win32":
        assert service.start("Ctrl+Shift+F24") is True
        assert service.registered is True
    else:
        assert service.supported is False
        assert service.start() is False
        assert service.registered is False
    service.stop()
