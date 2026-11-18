from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QPlainTextEdit, QStackedWidget,
    QStatusBar, QTableWidget, QTableWidgetItem, QTabWidget, QToolBar, QVBoxLayout,
    QWidget,
)

from korean_ai_workspace.models.entities import TranslationHistory
from korean_ai_workspace.repositories.translation_repository import TranslationRepository
from korean_ai_workspace.services.ai.config import AIProviderConfig
from korean_ai_workspace.services.ai.providers import AIProviderError, build_provider
from korean_ai_workspace.services.translation.service import TranslationResult, TranslationService


class WorkerSignals(QObject):
    success = Signal(object)
    failure = Signal(str)


class TranslationWorker(QRunnable):
    def __init__(self, service: TranslationService, text: str, language: str):
        super().__init__()
        self.service, self.text, self.language = service, text, language
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            self.signals.success.emit(self.service.translate(self.text, self.language))
        except Exception as exc:
            self.signals.failure.emit(str(exc))


class FloatingTranslationWindow(QWidget):
    """Reusable translation popup. New results replace its contents."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("快速翻譯結果")
        self.resize(560, 460)
        self._pinned = False
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.original_label = QLabel()
        self.original_label.setWordWrap(True)
        self.original_label.setMaximumHeight(90)
        layout.addWidget(QLabel("原文"))
        layout.addWidget(self.original_label)
        self.tabs = QTabWidget()
        self.outputs: dict[str, QPlainTextEdit] = {}
        for key, title in (("best", "最佳翻譯"), ("formal", "正式版本"), ("natural", "自然版本"), ("friendly", "親切版本")):
            editor = QPlainTextEdit(); editor.setReadOnly(True); self.outputs[key] = editor
            self.tabs.addTab(editor, title)
        layout.addWidget(self.tabs, 1)
        actions = QHBoxLayout()
        copy_button = QPushButton("複製目前版本"); copy_button.clicked.connect(self.copy_current)
        self.pin_button = QPushButton("釘選"); self.pin_button.setCheckable(True); self.pin_button.toggled.connect(self.set_pinned)
        close_button = QPushButton("關閉"); close_button.clicked.connect(self.hide)
        actions.addWidget(copy_button); actions.addWidget(self.pin_button); actions.addStretch(); actions.addWidget(close_button)
        layout.addLayout(actions)

    def show_result(self, source_text: str, result: TranslationResult):
        self.original_label.setText(source_text)
        for key, editor in self.outputs.items():
            editor.setPlainText(getattr(result, key))
        self.adjustSize()
        self.show(); self.raise_(); self.activateWindow()
        if not self._pinned:
            self._timer.start(8000)

    def copy_current(self):
        editor = self.outputs.get(self.tabs.currentWidget() and next((key for key, value in self.outputs.items() if value is self.tabs.currentWidget()), "best"))
        if editor:
            QApplication.clipboard().setText(editor.toPlainText())

    def set_pinned(self, pinned: bool):
        self._pinned = pinned
        self.pin_button.setText("已釘選" if pinned else "釘選")
        if pinned:
            self._timer.stop()
        elif self.isVisible():
            self._timer.start(8000)

    def enterEvent(self, event):
        self._timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._pinned:
            self._timer.start(8000)
        super().leaveEvent(event)


class HistoryDialog(QDialog):
    load_requested = Signal(object)

    def __init__(self, repository: TranslationRepository, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.setWindowTitle("翻譯歷史搜尋")
        self.resize(900, 520)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        bar = QHBoxLayout(); self.search_box = QLineEdit(); self.search_box.setPlaceholderText("搜尋原文、最佳翻譯、正式、自然或親切版本…")
        search_button = QPushButton("搜尋"); search_button.clicked.connect(self.refresh); self.search_box.returnPressed.connect(self.refresh)
        bar.addWidget(self.search_box, 1); bar.addWidget(search_button); layout.addLayout(bar)
        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(["時間", "原文", "最佳翻譯", "方向", "模型"]); self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.cellDoubleClicked.connect(self.load_row)
        self.table.horizontalHeader().setStretchLastSection(True); layout.addWidget(self.table, 1)
        hint = QLabel("雙擊項目可載入四種翻譯結果至主畫面。搜尋在本機 SQLite 執行，不會傳送給 AI。"); hint.setWordWrap(True); layout.addWidget(hint)

    def refresh(self):
        self.records = self.repository.search(self.search_box.text() if hasattr(self, "search_box") else "")
        self.table.setRowCount(len(self.records))
        for row, record in enumerate(self.records):
            timestamp = record.created_at.strftime("%Y-%m-%d %H:%M") if isinstance(record.created_at, datetime) else str(record.created_at)
            values = [timestamp, record.source_text, record.best_translation, f"{record.source_language} → {record.target_language}", record.model]
            for column, value in enumerate(values): self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def load_row(self, row: int, _column: int):
        self.load_requested.emit(self.records[row])
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, repository: TranslationRepository):
        super().__init__()
        self.repository = repository
        self.thread_pool = QThreadPool.globalInstance()
        self.floating_window = FloatingTranslationWindow(self)
        self.setWindowTitle("Korean AI Workspace｜韓文 AI 翻譯與商務工作站")
        self.resize(1180, 800)
        self._build_ui()

    def _build_ui(self):
        toolbar = QToolBar("工具列"); self.addToolBar(toolbar)
        test_action = QAction("測試 AI 連線", self); test_action.triggered.connect(self.test_connection); toolbar.addAction(test_action)
        history_action = QAction("翻譯歷史", self); history_action.triggered.connect(self.open_history); toolbar.addAction(history_action)
        self.status = QStatusBar(); self.setStatusBar(self.status)
        root = QWidget(); layout = QHBoxLayout(root); layout.setContentsMargins(0, 0, 0, 0)
        nav = QWidget(); nav.setFixedWidth(220); nav_layout = QVBoxLayout(nav)
        title = QLabel("Korean AI\nWorkspace"); title.setObjectName("brand"); nav_layout.addWidget(title)
        self.pages = QStackedWidget()
        items = [("翻譯中心", self._translation_page()), ("郵件中心", self._info_page("郵件中心", "第一階段先完成手動翻譯核心，郵件工作流程將於第四階段實作。")), ("客戶中心", self._info_page("客戶中心", "客戶資料隔離與記憶系統將於第三階段實作。")), ("詞庫中心", self._info_page("詞庫中心", "全域、分類及客戶詞庫將於第三階段實作。")), ("AI 引擎中心", self._ai_page()), ("系統管理中心", self._info_page("系統管理中心", "備份、還原、快捷鍵及安全設定將於第五階段實作。"))]
        self.nav_buttons = []
        for index, (name, page) in enumerate(items):
            button = QPushButton(name); button.setCheckable(True); button.clicked.connect(lambda checked, i=index: self.pages.setCurrentIndex(i)); self.nav_buttons.append(button); nav_layout.addWidget(button); self.pages.addWidget(page)
        self.nav_buttons[0].setChecked(True)
        nav_layout.addStretch(); nav_layout.addWidget(QLabel("V1.0｜第二階段")); layout.addWidget(nav); layout.addWidget(self.pages, 1); self.setCentralWidget(root)
        self.setStyleSheet("""
            QMainWindow { background: #f4f7fb; } QWidget { font-family: 'Microsoft JhengHei', 'Noto Sans CJK TC'; font-size: 14px; }
            #brand { font-size: 20px; font-weight: 700; color: #17324d; padding: 16px 8px; }
            QPushButton { padding: 9px 12px; text-align: left; border: 0; border-radius: 6px; }
            QPushButton:hover { background: #dceaf5; } QLineEdit, QPlainTextEdit, QComboBox, QTableWidget { background: white; border: 1px solid #c8d4df; border-radius: 5px; padding: 7px; }
            QPushButton#primary { background: #176b87; color: white; text-align: center; font-weight: bold; }
            QLabel#heading { font-size: 24px; font-weight: 700; color: #17324d; }
        """)

    def _translation_page(self):
        page = QWidget(); outer = QVBoxLayout(page)
        heading = QLabel("翻譯中心"); heading.setObjectName("heading"); outer.addWidget(heading)
        outer.addWidget(QLabel("一次保存最佳、正式、自然與親切四種版本；翻譯完成後會更新同一個浮動視窗。"))
        form = QFormLayout(); self.provider = QComboBox(); self.provider.addItems(["openai", "gemini", "openai_compatible"]); self.api_key = QLineEdit(); self.api_key.setEchoMode(QLineEdit.Password); self.model = QLineEdit("gpt-4o-mini"); self.endpoint = QLineEdit("https://api.openai.com/v1"); self.language = QComboBox(); self.language.addItem("自動辨識", "auto"); self.language.addItem("韓文 → 繁中", "ko"); self.language.addItem("繁中 → 韓文", "zh-TW")
        form.addRow("服務商", self.provider); form.addRow("API Key（不會保存）", self.api_key); form.addRow("模型", self.model); form.addRow("Endpoint", self.endpoint); form.addRow("翻譯方向", self.language); outer.addLayout(form)
        outer.addWidget(QLabel("原文")); self.source = QPlainTextEdit(); self.source.setPlaceholderText("貼上韓文或台灣繁體中文內容…"); outer.addWidget(self.source, 2)
        bar = QHBoxLayout(); translate = QPushButton("開始翻譯"); translate.setObjectName("primary"); translate.clicked.connect(self.translate); clear = QPushButton("清除"); clear.clicked.connect(self.source.clear); history = QPushButton("搜尋歷史"); history.clicked.connect(self.open_history); bar.addWidget(translate); bar.addWidget(clear); bar.addWidget(history); bar.addStretch(); outer.addLayout(bar)
        outer.addWidget(QLabel("四種翻譯結果")); self.result_tabs = QTabWidget(); self.result_editors = {}
        for key, title in (("best", "最佳翻譯"), ("formal", "正式版本"), ("natural", "自然版本"), ("friendly", "親切版本")):
            editor = QPlainTextEdit(); editor.setReadOnly(True); self.result_editors[key] = editor; self.result_tabs.addTab(editor, title)
        outer.addWidget(self.result_tabs, 3)
        return page

    def _ai_page(self): return self._info_page("AI 引擎中心", "目前第一階段支援 OpenAI、Gemini（可使用相容 Endpoint）及其他 OpenAI Chat Completions 相容服務。API Key 只在本次執行期間使用；安全保存將於第五階段加入 Windows DPAPI。")
    def _info_page(self, title: str, message: str):
        page = QWidget(); layout = QVBoxLayout(page); heading = QLabel(title); heading.setObjectName("heading"); layout.addWidget(heading); label = QLabel(message); label.setWordWrap(True); layout.addWidget(label); layout.addStretch(); return page
    def _provider(self): return build_provider(AIProviderConfig(self.provider.currentText(), self.api_key.text(), self.model.text(), self.endpoint.text()))

    def translate(self):
        try: service = TranslationService(self._provider())
        except Exception as exc: QMessageBox.warning(self, "設定錯誤", str(exc)); return
        source_text = self.source.toPlainText(); self.status.showMessage("正在呼叫 AI API…")
        for editor in self.result_editors.values(): editor.setPlainText("翻譯中…")
        worker = TranslationWorker(service, source_text, self.language.currentData()); worker.signals.success.connect(lambda result, text=source_text: self._translation_done(text, result)); worker.signals.failure.connect(self._translation_failed); self.thread_pool.start(worker)

    @Slot(str, object)
    def _translation_done(self, source_text: str, result: TranslationResult):
        for key, editor in self.result_editors.items(): editor.setPlainText(getattr(result, key))
        self.repository.add(source_text=source_text, source_language=result.source_language, target_language=result.target_language, best_translation=result.best, formal_translation=result.formal, natural_translation=result.natural, friendly_translation=result.friendly, provider=self.provider.currentText(), model=self.model.text())
        self.floating_window.show_result(source_text, result)
        self.status.showMessage("翻譯完成，四種版本已保存並更新浮動翻譯視窗。")

    @Slot(str)
    def _translation_failed(self, message: str):
        for editor in self.result_editors.values(): editor.clear()
        self.status.showMessage("翻譯失敗，原文未被覆蓋。", 8000); QMessageBox.warning(self, "翻譯失敗", message)

    def open_history(self):
        dialog = HistoryDialog(self.repository, self); dialog.load_requested.connect(self.load_history_record); dialog.exec()

    @Slot(object)
    def load_history_record(self, record: TranslationHistory):
        self.source.setPlainText(record.source_text)
        result = TranslationResult(record.source_language, record.target_language, record.best_translation, record.formal_translation, record.natural_translation, record.friendly_translation)
        for key, editor in self.result_editors.items(): editor.setPlainText(getattr(result, key))
        self.floating_window.show_result(record.source_text, result); self.status.showMessage("已從翻譯歷史載入四種版本。")

    def test_connection(self):
        try: response = self._provider().test_connection(); QMessageBox.information(self, "AI 連線測試", f"服務回應：{response}")
        except Exception as exc: QMessageBox.warning(self, "AI 連線測試失敗", str(exc))
