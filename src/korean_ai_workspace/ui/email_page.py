from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, QRunnable, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QPlainTextEdit, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout,
    QWidget,
)

from korean_ai_workspace.models.entities import EmailRecord
from korean_ai_workspace.repositories.attachment_repository import AttachmentRepository
from korean_ai_workspace.repositories.customer_repository import CustomerRepository
from korean_ai_workspace.repositories.email_repository import EmailRepository
from korean_ai_workspace.repositories.glossary_repository import GlossaryRepository
from korean_ai_workspace.services.email_service import EmailAnalysis, EmailService, ReplyDrafts


class EmailWorkerSignals(QObject):
    success = Signal(object)
    failure = Signal(str)


class EmailWorker(QRunnable):
    def __init__(self, task: Callable[[], object]):
        super().__init__(); self.task = task; self.signals = EmailWorkerSignals()

    @Slot()
    def run(self):
        try: self.signals.success.emit(self.task())
        except Exception as exc: self.signals.failure.emit(str(exc))


class EmailPage(QWidget):
    def __init__(self, email_repository: EmailRepository, attachment_repository: AttachmentRepository, customer_repository: CustomerRepository, glossary_repository: GlossaryRepository, provider_factory: Callable, customer_context: Callable[[int | None], str], glossary_terms: Callable[[int | None], list], thread_pool, parent=None):
        super().__init__(parent); self.email_repository = email_repository; self.attachment_repository = attachment_repository; self.customer_repository = customer_repository; self.glossary_repository = glossary_repository; self.provider_factory = provider_factory; self.customer_context = customer_context; self.glossary_terms = glossary_terms; self.thread_pool = thread_pool; self.email_id: int | None = None; self._build_ui(); self.refresh_customers(); self.refresh_emails()

    def _build_ui(self):
        layout = QVBoxLayout(self); title = QLabel("商務郵件中心"); title.setObjectName("heading"); layout.addWidget(title); layout.addWidget(QLabel("第一版採手動貼上韓文郵件，不串 Gmail/Outlook；AI 產生內容一律標示為草稿。"))
        top = QHBoxLayout(); self.email_search = QLineEdit(); self.email_search.setPlaceholderText("搜尋主旨或郵件內容…"); find = QPushButton("搜尋郵件"); find.clicked.connect(self.refresh_emails); new = QPushButton("新增郵件"); new.clicked.connect(self.clear_form); top.addWidget(self.email_search, 1); top.addWidget(find); top.addWidget(new); layout.addLayout(top)
        self.email_table = QTableWidget(0, 4); self.email_table.setHorizontalHeaderLabels(["狀態", "主旨", "客戶", "更新時間"]); self.email_table.setSelectionBehavior(QTableWidget.SelectRows); self.email_table.setEditTriggers(QTableWidget.NoEditTriggers); self.email_table.cellDoubleClicked.connect(self.load_email_row); self.email_table.horizontalHeader().setStretchLastSection(True); layout.addWidget(self.email_table, 1)
        form = QFormLayout(); self.customer = QComboBox(); self.subject = QLineEdit(); self.status = QComboBox(); self.status.addItems(EmailRepository.STATUSES); self.original = QPlainTextEdit(); self.original.setPlaceholderText("貼上韓文郵件內容…"); self.original.setMinimumHeight(130); form.addRow("客戶", self.customer); form.addRow("主旨", self.subject); form.addRow("狀態", self.status); layout.addLayout(form); layout.addWidget(QLabel("韓文原始郵件")); layout.addWidget(self.original)
        actions = QHBoxLayout(); analyze = QPushButton("翻譯並分析郵件"); analyze.setObjectName("primary"); analyze.clicked.connect(self.analyze_email); save = QPushButton("保存郵件"); save.clicked.connect(self.save_email); actions.addWidget(analyze); actions.addWidget(save); actions.addStretch(); layout.addLayout(actions)
        self.analysis_tabs = QTabWidget(); self.analysis_editors = {}
        for key, title_text in (("translated", "完整翻譯"), ("summary", "摘要"), ("tone", "語氣分析"), ("requirements", "對方需求"), ("important_items", "重要事項")):
            editor = QPlainTextEdit(); editor.setReadOnly(True); self.analysis_editors[key] = editor; self.analysis_tabs.addTab(editor, title_text)
        layout.addWidget(self.analysis_tabs, 2)
        layout.addWidget(QLabel("中文回覆意思")); self.reply_intent = QPlainTextEdit(); self.reply_intent.setPlaceholderText("輸入你想用中文回覆的內容…"); self.reply_intent.setMaximumHeight(90); layout.addWidget(self.reply_intent); draft_actions = QHBoxLayout(); draft = QPushButton("產生韓文回信草稿"); draft.setObjectName("primary"); draft.clicked.connect(self.generate_draft); save_draft = QPushButton("保存目前草稿"); save_draft.clicked.connect(self.save_draft); draft_actions.addWidget(draft); draft_actions.addWidget(save_draft); draft_actions.addStretch(); layout.addLayout(draft_actions)
        self.draft_tabs = QTabWidget(); self.draft_editors = {}
        for key, title_text in (("formal", "正式草稿"), ("natural", "自然草稿"), ("friendly", "親切草稿")):
            editor = QPlainTextEdit(); self.draft_editors[key] = editor; self.draft_tabs.addTab(editor, title_text)
        layout.addWidget(self.draft_tabs, 2)
        layout.addWidget(QLabel("附件（單檔上限 100 MB；不解析、不上傳給 AI）")); attachment_actions = QHBoxLayout(); add_attachment = QPushButton("加入附件"); add_attachment.clicked.connect(self.add_attachment); open_attachment = QPushButton("開啟附件"); open_attachment.clicked.connect(self.open_attachment); remove_link = QPushButton("解除郵件關聯"); remove_link.clicked.connect(self.remove_attachment_link); delete_file = QPushButton("刪除實體檔案"); delete_file.clicked.connect(self.delete_attachment_file); attachment_actions.addWidget(add_attachment); attachment_actions.addWidget(open_attachment); attachment_actions.addWidget(remove_link); attachment_actions.addWidget(delete_file); attachment_actions.addStretch(); layout.addLayout(attachment_actions); self.attachments = QTableWidget(0, 3); self.attachments.setHorizontalHeaderLabels(["檔名", "大小", "SHA-256"]); self.attachments.setSelectionBehavior(QTableWidget.SelectRows); self.attachments.setEditTriggers(QTableWidget.NoEditTriggers); self.attachments.horizontalHeader().setStretchLastSection(True); layout.addWidget(self.attachments, 1)

    def refresh_customers(self):
        current = self.customer.currentData() if hasattr(self, "customer") and self.customer.count() else None; self.customer.clear(); self.customer.addItem("未指定客戶", None)
        for record in self.customer_repository.search(): self.customer.addItem(f"{record.company_name}｜{record.contact_name}", record.id)
        if current is not None:
            index = self.customer.findData(current)
            if index >= 0: self.customer.setCurrentIndex(index)

    def refresh_emails(self):
        if not hasattr(self, "email_table"): return
        self.records = self.email_repository.search(self.email_search.text() if hasattr(self, "email_search") else ""); names = {c.id: c.company_name for c in self.customer_repository.search()}; self.email_table.setRowCount(len(self.records))
        for row, record in enumerate(self.records):
            updated = record.updated_at.strftime("%Y-%m-%d %H:%M") if record.updated_at else ""
            for column, value in enumerate([record.status, record.subject, names.get(record.customer_id, "未指定"), updated]): self.email_table.setItem(row, column, QTableWidgetItem(value))
        self.email_table.resizeColumnsToContents()

    def load_email_row(self, row: int, _column: int): self.load_record(self.records[row])

    def load_record(self, record: EmailRecord):
        self.email_id = record.id; index = self.customer.findData(record.customer_id); self.customer.setCurrentIndex(index if index >= 0 else 0); self.subject.setText(record.subject); self.original.setPlainText(record.original_content); self.status.setCurrentText(record.status); self.reply_intent.setPlainText(record.reply_intent); self._set_analysis(record); self.draft_editors["formal"].setPlainText(record.draft_formal); self.draft_editors["natural"].setPlainText(record.draft_natural); self.draft_editors["friendly"].setPlainText(record.draft_friendly); self.refresh_attachments()

    def clear_form(self):
        self.email_id = None; self.customer.setCurrentIndex(0); self.subject.clear(); self.status.setCurrentText("待處理"); self.original.clear(); self.reply_intent.clear();
        for editor in self.analysis_editors.values(): editor.clear()
        for editor in self.draft_editors.values(): editor.clear()
        self.attachments.setRowCount(0)

    def _ensure_email(self) -> int:
        content = self.original.toPlainText().strip()
        if not content: raise ValueError("請先貼上韓文郵件內容")
        values = {"customer_id": self.customer.currentData(), "subject": self.subject.text(), "original_content": content, "status": self.status.currentText()}
        if self.email_id is None: self.email_id = self.email_repository.add(**values).id
        else: self.email_repository.update(self.email_id, **values)
        return self.email_id

    def _service(self) -> EmailService:
        customer_id = self.customer.currentData(); return EmailService(self.provider_factory(), self.glossary_terms(customer_id), self.customer_context(customer_id))

    def analyze_email(self):
        try: self._ensure_email(); service = self._service(); original = self.original.toPlainText(); self.status.setCurrentText("已翻譯"); self.status.setEnabled(False); self.email_repository.update(self.email_id, status="已翻譯")
        except Exception as exc: QMessageBox.warning(self, "郵件分析設定錯誤", str(exc)); return
        for editor in self.analysis_editors.values(): editor.setPlainText("分析中…")
        worker = EmailWorker(lambda: service.analyze(original)); worker.signals.success.connect(self.analysis_done); worker.signals.failure.connect(self.operation_failed); self.thread_pool.start(worker)

    @Slot(object)
    def analysis_done(self, analysis: EmailAnalysis):
        self.status.setEnabled(True); self._set_analysis_values(analysis); self.email_repository.update(self.email_id, translated_content=analysis.translated, analysis_json=json.dumps(asdict(analysis), ensure_ascii=False), status="分析完成"); self.refresh_emails()

    def _set_analysis_values(self, analysis: EmailAnalysis):
        for key in self.analysis_editors: self.analysis_editors[key].setPlainText(getattr(analysis, key))

    def _set_analysis(self, record: EmailRecord):
        if record.analysis_json:
            try: self._set_analysis_values(EmailAnalysis(**json.loads(record.analysis_json)))
            except (TypeError, json.JSONDecodeError): pass
        else:
            for editor in self.analysis_editors.values(): editor.clear()

    def generate_draft(self):
        try:
            if self.email_id is None: self._ensure_email()
            analysis = EmailAnalysis(*(self.analysis_editors[key].toPlainText() for key in ("translated", "summary", "tone", "requirements", "important_items"))); service = self._service(); original = self.original.toPlainText(); intent = self.reply_intent.toPlainText(); self.email_repository.update(self.email_id, reply_intent=intent, status="回信撰寫中")
        except Exception as exc: QMessageBox.warning(self, "回信草稿設定錯誤", str(exc)); return
        for editor in self.draft_editors.values(): editor.setPlainText("產生草稿中…")
        worker = EmailWorker(lambda: service.draft_reply(original, analysis, intent)); worker.signals.success.connect(self.draft_done); worker.signals.failure.connect(self.operation_failed); self.thread_pool.start(worker)

    @Slot(object)
    def draft_done(self, drafts: ReplyDrafts):
        self.draft_editors["formal"].setPlainText(drafts.formal); self.draft_editors["natural"].setPlainText(drafts.natural); self.draft_editors["friendly"].setPlainText(drafts.friendly); self.email_repository.update(self.email_id, draft_formal=drafts.formal, draft_natural=drafts.natural, draft_friendly=drafts.friendly, status="草稿完成"); self.status.setCurrentText("草稿完成"); self.refresh_emails()

    def save_email(self):
        try: self._ensure_email(); self.refresh_emails(); QMessageBox.information(self, "保存完成", "郵件原文與目前資料已保存。")
        except Exception as exc: QMessageBox.warning(self, "保存失敗", str(exc))

    def save_draft(self):
        if self.email_id is None: QMessageBox.warning(self, "尚未建立郵件", "請先保存郵件或產生回信草稿。"); return
        selected = self.draft_tabs.currentWidget().toPlainText(); self.email_repository.update(self.email_id, selected_draft=selected, reply_intent=self.reply_intent.toPlainText(), draft_formal=self.draft_editors["formal"].toPlainText(), draft_natural=self.draft_editors["natural"].toPlainText(), draft_friendly=self.draft_editors["friendly"].toPlainText(), status="草稿完成"); self.status.setCurrentText("草稿完成"); self.refresh_emails(); QMessageBox.information(self, "草稿已保存", "目前選取的韓文回信已保存為草稿，並未寄出。")

    def add_attachment(self):
        try: email_id = self._ensure_email()
        except Exception as exc: QMessageBox.warning(self, "附件關聯失敗", str(exc)); return
        path, _ = QFileDialog.getOpenFileName(self, "選擇附件");
        if not path: return
        try:
            attachment, duplicate = self.attachment_repository.add_file(path, email_id); self.refresh_attachments(); message = "內容相同的附件已存在，已共用既有附件。" if duplicate else "附件已複製保存並建立郵件關聯。"; QMessageBox.information(self, "附件完成", message)
        except Exception as exc: QMessageBox.warning(self, "附件失敗", str(exc))

    def refresh_attachments(self):
        if self.email_id is None: self.attachments.setRowCount(0); return
        records = self.attachment_repository.list_for_email(self.email_id); self.attachment_records = records; self.attachments.setRowCount(len(records))
        for row, record in enumerate(records):
            size = f"{record.size_bytes / 1024 / 1024:.2f} MB" if record.size_bytes >= 1024 * 1024 else f"{record.size_bytes / 1024:.1f} KB"
            for column, value in enumerate([record.original_name, size, record.sha256]): self.attachments.setItem(row, column, QTableWidgetItem(value))

    def _selected_attachment(self):
        row = self.attachments.currentRow(); return self.attachment_records[row] if row >= 0 and row < len(getattr(self, "attachment_records", [])) else None
    def open_attachment(self):
        record = self._selected_attachment();
        if record: QDesktopServices.openUrl(QUrl.fromLocalFile(record.stored_path))
    def remove_attachment_link(self):
        record = self._selected_attachment();
        if record and self.email_id is not None: self.attachment_repository.remove_link(self.email_id, record.id); self.refresh_attachments()
    def delete_attachment_file(self):
        record = self._selected_attachment();
        if not record: return
        try: self.attachment_repository.delete_file(record.id); self.refresh_attachments(); QMessageBox.information(self, "刪除完成", "附件實體檔案已刪除。")
        except Exception as exc: QMessageBox.warning(self, "無法刪除附件", str(exc))
    @Slot(str)
    def operation_failed(self, message: str):
        self.status.setEnabled(True); QMessageBox.warning(self, "AI 操作失敗", message)
