from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QPlainTextEdit, QStackedWidget, QStatusBar, QToolBar,
    QVBoxLayout, QWidget,
)

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


class MainWindow(QMainWindow):
    def __init__(self, repository: TranslationRepository):
        super().__init__()
        self.repository = repository
        self.thread_pool = QThreadPool.globalInstance()
        self.setWindowTitle("Korean AI Workspace｜韓文 AI 翻譯與商務工作站")
        self.resize(1180, 760)
        self._build_ui()

    def _build_ui(self):
        toolbar = QToolBar("工具列")
        self.addToolBar(toolbar)
        test_action = QAction("測試 AI 連線", self)
        test_action.triggered.connect(self.test_connection)
        toolbar.addAction(test_action)
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        root = QWidget(); layout = QHBoxLayout(root); layout.setContentsMargins(0, 0, 0, 0)
        nav = QWidget(); nav.setFixedWidth(220); nav_layout = QVBoxLayout(nav)
        title = QLabel("Korean AI\nWorkspace"); title.setObjectName("brand")
        nav_layout.addWidget(title)
        self.pages = QStackedWidget()
        items = [("翻譯中心", self._translation_page()), ("郵件中心", self._info_page("郵件中心", "第一階段先完成手動翻譯核心，郵件工作流程將於第四階段實作。")), ("客戶中心", self._info_page("客戶中心", "客戶資料隔離與記憶系統將於第三階段實作。")), ("詞庫中心", self._info_page("詞庫中心", "全域、分類及客戶詞庫將於第三階段實作。")), ("AI 引擎中心", self._ai_page()), ("系統管理中心", self._info_page("系統管理中心", "備份、還原、快捷鍵及安全設定將於第五階段實作。"))]
        for index, (name, page) in enumerate(items):
            button = QPushButton(name); button.setCheckable(True); button.clicked.connect(lambda checked, i=index: self.pages.setCurrentIndex(i))
            nav_layout.addWidget(button)
            self.pages.addWidget(page)
        nav_layout.addStretch(); nav_layout.addWidget(QLabel("V1.0｜第一階段"))
        layout.addWidget(nav); layout.addWidget(self.pages, 1)
        self.setCentralWidget(root)
        self.setStyleSheet("""
            QMainWindow { background: #f4f7fb; } QWidget { font-family: 'Microsoft JhengHei', 'Noto Sans CJK TC'; font-size: 14px; }
            #brand { font-size: 20px; font-weight: 700; color: #17324d; padding: 16px 8px; }
            QPushButton { padding: 9px 12px; text-align: left; border: 0; border-radius: 6px; }
            QPushButton:hover { background: #dceaf5; } QLineEdit, QPlainTextEdit, QComboBox { background: white; border: 1px solid #c8d4df; border-radius: 5px; padding: 7px; }
            QPushButton#primary { background: #176b87; color: white; text-align: center; font-weight: bold; }
            QLabel#heading { font-size: 24px; font-weight: 700; color: #17324d; }
        """)

    def _translation_page(self):
        page = QWidget(); outer = QVBoxLayout(page)
        heading = QLabel("翻譯中心"); heading.setObjectName("heading"); outer.addWidget(heading)
        outer.addWidget(QLabel("保留原文並以目前選擇的 AI Provider 產生基本雙向翻譯。API 失敗時原文不會被覆蓋。"))
        form = QFormLayout(); self.provider = QComboBox(); self.provider.addItems(["openai", "gemini", "openai_compatible"]); self.api_key = QLineEdit(); self.api_key.setEchoMode(QLineEdit.Password); self.model = QLineEdit("gpt-4o-mini"); self.endpoint = QLineEdit("https://api.openai.com/v1"); self.language = QComboBox(); self.language.addItem("自動辨識", "auto"); self.language.addItem("韓文 → 繁中", "ko"); self.language.addItem("繁中 → 韓文", "zh-TW")
        form.addRow("服務商", self.provider); form.addRow("API Key（不會保存）", self.api_key); form.addRow("模型", self.model); form.addRow("Endpoint", self.endpoint); form.addRow("翻譯方向", self.language); outer.addLayout(form)
        outer.addWidget(QLabel("原文")); self.source = QPlainTextEdit(); self.source.setPlaceholderText("貼上韓文或台灣繁體中文內容…"); outer.addWidget(self.source, 2)
        bar = QHBoxLayout(); translate = QPushButton("開始翻譯"); translate.setObjectName("primary"); translate.clicked.connect(self.translate); clear = QPushButton("清除"); clear.clicked.connect(self.source.clear); bar.addWidget(translate); bar.addWidget(clear); bar.addStretch(); outer.addLayout(bar)
        outer.addWidget(QLabel("最佳翻譯")); self.result = QPlainTextEdit(); self.result.setReadOnly(True); outer.addWidget(self.result, 2)
        return page

    def _ai_page(self):
        return self._info_page("AI 引擎中心", "目前第一階段支援 OpenAI、Gemini（可使用相容 Endpoint）及其他 OpenAI Chat Completions 相容服務。API Key 只在本次執行期間使用；安全保存將於第五階段加入 Windows DPAPI。")

    def _info_page(self, title: str, message: str):
        page = QWidget(); layout = QVBoxLayout(page); heading = QLabel(title); heading.setObjectName("heading"); layout.addWidget(heading); label = QLabel(message); label.setWordWrap(True); layout.addWidget(label); layout.addStretch(); return page

    def _provider(self):
        return build_provider(AIProviderConfig(self.provider.currentText(), self.api_key.text(), self.model.text(), self.endpoint.text()))

    def translate(self):
        try: service = TranslationService(self._provider())
        except Exception as exc: QMessageBox.warning(self, "設定錯誤", str(exc)); return
        self.result.setPlainText("翻譯中…"); self.status.showMessage("正在呼叫 AI API…")
        worker = TranslationWorker(service, self.source.toPlainText(), self.language.currentData()); worker.signals.success.connect(self._translation_done); worker.signals.failure.connect(self._translation_failed); self.thread_pool.start(worker)

    @Slot(object)
    def _translation_done(self, result: TranslationResult):
        self.result.setPlainText(result.best); self.status.showMessage("翻譯完成，已保存原文與最佳翻譯至本機資料庫。")
        self.repository.add(source_text=self.source.toPlainText(), source_language=result.source_language, target_language=result.target_language, best_translation=result.best, formal_translation=result.formal, natural_translation=result.natural, friendly_translation=result.friendly, provider=self.provider.currentText(), model=self.model.text())

    @Slot(str)
    def _translation_failed(self, message: str):
        self.result.clear(); self.status.showMessage("翻譯失敗，原文未被覆蓋。", 8000); QMessageBox.warning(self, "翻譯失敗", message)

    def test_connection(self):
        try: response = self._provider().test_connection(); QMessageBox.information(self, "AI 連線測試", f"服務回應：{response}")
        except (ValueError, AIProviderError, Exception) as exc: QMessageBox.warning(self, "AI 連線測試失敗", str(exc))
