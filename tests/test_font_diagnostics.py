from __future__ import annotations

from PySide6.QtWidgets import QApplication

from korean_ai_workspace.ui.font_diagnostics import DIAGNOSTIC_SAMPLE, FontDiagnosticsDialog
from korean_ai_workspace.ui.font_support import collect_font_diagnostics, format_font_diagnostics


def test_font_diagnostics_contains_runtime_font_facts_without_sensitive_data():
    app = QApplication.instance() or QApplication([])
    diagnostics = collect_font_diagnostics(app)
    report = format_font_diagnostics(diagnostics)
    assert diagnostics["qt"]
    assert diagnostics["pyside6"]
    assert "resolved_font_family" in diagnostics
    assert "malgun_found" in diagnostics
    assert "malgun_supports_korean" in diagnostics
    assert "korean_writing_system_available" in diagnostics
    assert "Fallback candidates:" in report
    assert "api" not in report.lower()
    assert "customer" not in report.lower()
    assert "郵件" not in report


def test_font_diagnostics_dialog_has_real_korean_plain_text_editor():
    app = QApplication.instance() or QApplication([])
    dialog = FontDiagnosticsDialog()
    assert isinstance(dialog.test_editor.toPlainText(), str)
    assert "안녕하세요" in dialog.test_editor.toPlainText()
    assert "한국어 번역 테스트입니다." in dialog.test_editor.toPlainText()
    assert dialog.report.toPlainText()
    dialog.close()
    app.processEvents()
