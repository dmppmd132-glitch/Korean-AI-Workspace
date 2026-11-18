from __future__ import annotations

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication


# Windows normally provides Malgun Gothic; Linux development images commonly use Noto CJK.
PREFERRED_FAMILIES = (
    "Malgun Gothic",
    "Noto Sans CJK KR",
    "Noto Sans CJK TC",
    "Microsoft JhengHei",
    "Microsoft YaHei",
    "Arial Unicode MS",
    "Segoe UI",
)


def available_cjk_families() -> list[str]:
    families = set(QFontDatabase.families())
    korean = QFontDatabase.WritingSystem.Korean
    selected = [family for family in PREFERRED_FAMILIES if family in families and korean in QFontDatabase.writingSystems(family)]
    if selected: return selected
    # Last-resort discovery for localized Windows font names or future Qt font packages.
    return [family for family in QFontDatabase.families() if korean in QFontDatabase.writingSystems(family)][:3]


def configure_application_font(application: QApplication) -> list[str]:
    families = available_cjk_families()
    font = QFont()
    # Some offscreen/platform font engines cannot enumerate installed fonts.
    # Keep an explicit ordered request in that case; the native font engine
    # can still resolve the first installed family and its glyph fallback.
    font.setFamilies(families or list(PREFERRED_FAMILIES))
    font.setPointSize(10)
    application.setFont(font)
    return families


def selected_ui_font_family() -> str:
    families = available_cjk_families()
    return families[0] if families else PREFERRED_FAMILIES[0]
