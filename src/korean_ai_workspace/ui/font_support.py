from __future__ import annotations

import platform
import sys
from dataclasses import dataclass
from pathlib import Path

import PySide6
from PySide6.QtCore import qVersion
from PySide6.QtGui import QFont, QFontDatabase, QFontInfo, QFontMetrics
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
KOREAN_SAMPLE = "안녕하세요. 감사합니다. 한국어 번역 테스트입니다."
BUNDLED_FONT_FILENAMES = (
    "NotoSansKR-Regular.ttf",
    "NotoSansCJKkr-Regular.otf",
    "NotoSansCJKkr-Regular.ttf",
)


@dataclass(frozen=True)
class LoadedFont:
    path: str
    families: tuple[str, ...]
    loaded: bool
    error: str = ""


def font_resource_directory() -> Path:
    """Return the optional bundled-font directory for source and PyInstaller runs."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "resources" / "fonts"
    return Path(__file__).resolve().parents[3] / "resources" / "fonts"


def load_bundled_fonts(directory: Path | None = None) -> list[LoadedFont]:
    """Load only font files explicitly shipped with the application.

    No font is silently downloaded or installed into Windows. This keeps the
    portable app auditable and allows a licensed font asset to be added later.
    """
    directory = directory or font_resource_directory()
    results: list[LoadedFont] = []
    for filename in BUNDLED_FONT_FILENAMES:
        path = directory / filename
        if not path.is_file():
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        families = tuple(QFontDatabase.applicationFontFamilies(font_id)) if font_id >= 0 else ()
        results.append(LoadedFont(str(path), families, font_id >= 0, "" if font_id >= 0 else "Qt addApplicationFont returned -1"))
    return results


def _font_database_families() -> list[str]:
    return list(QFontDatabase.families())


def _family_supports_korean(family: str) -> bool:
    korean = QFontDatabase.WritingSystem.Korean
    if korean in QFontDatabase.writingSystems(family):
        return True
    return all(QFontMetrics(QFont(family)).inFont(char) for char in "안녕감사한국어")


def available_cjk_families() -> list[str]:
    families = set(_font_database_families())
    selected = [family for family in PREFERRED_FAMILIES if family in families and _family_supports_korean(family)]
    if selected:
        return selected
    # Last-resort discovery for localized Windows font names or future Qt font packages.
    return [family for family in _font_database_families() if _family_supports_korean(family)][:3]


def supported_writing_system_names() -> list[str]:
    """Return writing systems exposed by the current Qt font database."""
    systems = set()
    for family in _font_database_families():
        systems.update(QFontDatabase.writingSystems(family))
    return [system.name for system in sorted(systems, key=lambda item: item.value)]


def configure_application_font(application: QApplication) -> list[str]:
    load_bundled_fonts()
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


def collect_font_diagnostics(application: QApplication) -> dict[str, object]:
    """Collect non-sensitive, runtime-only font facts for user troubleshooting."""
    load_results = load_bundled_fonts()
    app_font = application.font()
    info = QFontInfo(app_font)
    database_families = _font_database_families()
    korean = QFontDatabase.WritingSystem.Korean
    malgun_matches = [family for family in database_families if family.casefold() == "malgun gothic".casefold()]
    malgun_support = bool(malgun_matches and _family_supports_korean(malgun_matches[0]))
    metrics = QFontMetrics(app_font)
    candidate_checks = []
    for candidate in PREFERRED_FAMILIES:
        found = candidate in database_families
        candidate_checks.append({
            "candidate": candidate,
            "found": found,
            "supports_korean": bool(found and _family_supports_korean(candidate)),
            "resolved_family": QFontInfo(QFont(candidate)).family() if found else "",
        })
    return {
        "os": platform.platform(),
        "python": platform.python_version(),
        "qt": qVersion(),
        "pyside6": PySide6.__version__,
        "packaged": bool(getattr(sys, "frozen", False)),
        "application_font_family": app_font.family(),
        "application_font_families": list(app_font.families()),
        "resolved_font_family": info.family(),
        "resolved_font_style": info.styleName(),
        "resolved_font_pixel_size": info.pixelSize(),
        "font_database_family_count": len(database_families),
        "malgun_found": bool(malgun_matches),
        "malgun_families": malgun_matches,
        "malgun_supports_korean": malgun_support,
        "korean_writing_system_available": korean in _writing_systems_for_families(database_families),
        "supported_writing_systems": supported_writing_system_names(),
        "available_cjk_families": available_cjk_families(),
        "fallback_candidates": list(PREFERRED_FAMILIES),
        "fallback_checks": candidate_checks,
        "korean_glyphs_in_current_font": all(metrics.inFont(char) for char in "안녕감사한국어"),
        "bundled_fonts": [
            {"file": result.path, "loaded": result.loaded, "families": list(result.families), "error": result.error}
            for result in load_results
        ],
    }


def _writing_systems_for_families(families: list[str]):
    systems = set()
    for family in families:
        systems.update(QFontDatabase.writingSystems(family))
    return systems


def format_font_diagnostics(diagnostics: dict[str, object]) -> str:
    """Format a copy/paste report without API keys, user text, or customer data."""
    lines = [
        "Korean AI Workspace - Font Diagnostics",
        f"OS: {diagnostics['os']}",
        f"Python: {diagnostics['python']}",
        f"Qt: {diagnostics['qt']}",
        f"PySide6: {diagnostics['pyside6']}",
        f"Packaged EXE: {diagnostics['packaged']}",
        f"Application font family: {diagnostics['application_font_family']}",
        f"Application font families: {', '.join(diagnostics['application_font_families'])}",
        f"QFontInfo resolved family: {diagnostics['resolved_font_family']}",
        f"QFontInfo style: {diagnostics['resolved_font_style']}",
        f"Font database family count: {diagnostics['font_database_family_count']}",
        f"Malgun Gothic found: {diagnostics['malgun_found']}",
        f"Malgun Gothic supports Korean: {diagnostics['malgun_supports_korean']}",
        f"Korean WritingSystem available: {diagnostics['korean_writing_system_available']}",
        f"Available CJK families: {', '.join(diagnostics['available_cjk_families']) or '(none reported)'}",
        f"Fallback candidates: {', '.join(diagnostics['fallback_candidates'])}",
        f"Current font Korean glyph check: {diagnostics['korean_glyphs_in_current_font']}",
    ]
    lines.append("Fallback checks: " + str(diagnostics["fallback_checks"]))
    bundled = diagnostics["bundled_fonts"]
    lines.append("Bundled font loads: " + (str(bundled) if bundled else "(none)"))
    return "\n".join(lines)
