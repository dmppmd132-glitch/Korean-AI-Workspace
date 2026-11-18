from __future__ import annotations

import json

from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QApplication, QPlainTextEdit

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.repositories.translation_repository import TranslationRepository
from korean_ai_workspace.ui.font_support import configure_application_font
from korean_ai_workspace.ui.main_window import MainWindow


SAMPLES = [
    "안녕하세요. 감사합니다. 한국어 번역 테스트입니다.",
    "대한민국 서울특별시",
    "거래처 담당자님께",
    "가격 및 납기일을 확인 부탁드립니다.",
]


def test_configured_font_supports_korean_and_mixed_text_offscreen():
    app = QApplication.instance() or QApplication([])
    families = configure_application_font(app)
    # Qt's Windows offscreen platform may expose no named CJK families even
    # though its font engine can resolve the glyphs through system fallback.
    # The functional invariant is rendered glyph coverage, not a particular
    # family name (or a non-empty enumeration from QFontDatabase).
    metrics = QFontMetrics(app.font())
    assert all(metrics.inFont(character) for character in "안녕감사한국어")
    assert families or app.font().families() or app.font().family()


def test_clipboard_paste_preserves_korean_unicode():
    app = QApplication.instance() or QApplication([])
    configure_application_font(app)
    clipboard = app.clipboard(); editor = QPlainTextEdit(); expected = "\n".join(SAMPLES); clipboard.setText(expected); editor.show(); editor.paste()
    assert editor.toPlainText() == expected
    assert "□" not in editor.toPlainText()
    editor.close()


def test_main_window_input_and_all_text_widgets_use_global_font(tmp_path):
    app = QApplication.instance() or QApplication([])
    db = Database(f"sqlite:///{tmp_path / 'workspace.db'}"); db.create_all(); window = MainWindow(TranslationRepository(db))
    # Do not require Linux/Windows family names: QFont may report the generic
    # family while the platform fallback still provides Korean glyphs.
    source_metrics = QFontMetrics(window.source.font())
    assert all(source_metrics.inFont(character) for character in "안녕감사한국어")
    window.source.setPlainText(SAMPLES[0]); assert window.source.toPlainText() == SAMPLES[0]
    assert "□" not in window.floating_window.original_label.text()
    window.close(); window.floating_window.close(); app.processEvents()
