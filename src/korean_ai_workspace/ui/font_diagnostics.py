from __future__ import annotations

from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QPlainTextEdit, QVBoxLayout

from korean_ai_workspace.ui.font_support import KOREAN_SAMPLE, collect_font_diagnostics, format_font_diagnostics


DIAGNOSTIC_SAMPLE = (
    "안녕하세요. 감사합니다.\n\n"
    "한국어 번역 테스트입니다.\n\n"
    "고객님께서 요청하신 내용을 확인했습니다."
)


class FontDiagnosticsDialog(QDialog):
    """Visible runtime font check; copied output contains no application data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("韓文字型診斷")
        self.resize(900, 700)
        self._build_ui()
        self.refresh_diagnostics()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        heading = QLabel("韓文字型診斷")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        layout.addWidget(QLabel("下方測試區是真正的 QPlainTextEdit。診斷報告只包含作業系統、Qt 與字型資訊，不會讀取 API Key、郵件、客戶或翻譯內容。"))
        self.test_editor = QPlainTextEdit(DIAGNOSTIC_SAMPLE)
        self.test_editor.setReadOnly(True)
        self.test_editor.setMinimumHeight(160)
        self.test_editor.setPlaceholderText(KOREAN_SAMPLE)
        layout.addWidget(QLabel("韓文實際顯示測試區"))
        layout.addWidget(self.test_editor)
        self.report = QPlainTextEdit()
        self.report.setReadOnly(True)
        self.report.setLineWrapMode(QPlainTextEdit.NoWrap)
        layout.addWidget(QLabel("Qt runtime 診斷結果"))
        layout.addWidget(self.report, 1)
        buttons = QHBoxLayout()
        copy_button = QPushButton("複製診斷資訊")
        copy_button.clicked.connect(self.copy_report)
        refresh_button = QPushButton("重新檢查")
        refresh_button.clicked.connect(self.refresh_diagnostics)
        close_button = QPushButton("關閉")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(copy_button)
        buttons.addWidget(refresh_button)
        buttons.addStretch()
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

    def refresh_diagnostics(self):
        self.diagnostics = collect_font_diagnostics(QApplication.instance())
        self.report.setPlainText(format_font_diagnostics(self.diagnostics))

    def copy_report(self):
        QApplication.instance().clipboard().setText(self.report.toPlainText())
        QMessageBox.information(self, "已複製", "診斷資訊已複製。內容不包含 API Key、郵件、客戶或翻譯資料。")
