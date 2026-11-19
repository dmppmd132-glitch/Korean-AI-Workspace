from __future__ import annotations

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QPlainTextEdit, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from korean_ai_workspace.models.entities import Customer, GlossaryTerm
from korean_ai_workspace.repositories.customer_repository import CustomerRepository
from korean_ai_workspace.repositories.glossary_repository import GlossaryRepository
from korean_ai_workspace.repositories.memory_repository import CustomerMemoryRepository


class CustomerPage(QWidget):
    data_changed = Signal()

    def __init__(self, repository: CustomerRepository, memory_repository: CustomerMemoryRepository | None = None, parent=None):
        super().__init__(parent); self.repository = repository; self.memory_repository = memory_repository or CustomerMemoryRepository(repository.database); self.selected_id: int | None = None; self.selected_memory_id: int | None = None; self._build_ui(); self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self); title = QLabel("客戶中心"); title.setObjectName("heading"); layout.addWidget(title)
        layout.addWidget(QLabel("每位客戶資料獨立保存；翻譯時只會使用目前選取客戶的資料與專屬詞庫。"))
        bar = QHBoxLayout(); self.search = QLineEdit(); self.search.setPlaceholderText("搜尋公司、韓文公司名、聯絡人、Email 或產業…"); find = QPushButton("搜尋"); find.clicked.connect(self.refresh); self.search.returnPressed.connect(self.refresh); bar.addWidget(self.search, 1); bar.addWidget(find); layout.addLayout(bar)
        self.table = QTableWidget(0, 4); self.table.setHorizontalHeaderLabels(["公司名稱", "韓文公司名稱", "聯絡人", "Email"]); self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.cellClicked.connect(self.select_row); self.table.horizontalHeader().setStretchLastSection(True); layout.addWidget(self.table, 2)
        form = QGridLayout(); self.company = QLineEdit(); self.korean_company = QLineEdit(); self.contact = QLineEdit(); self.email = QLineEdit(); self.job_title = QLineEdit(); self.industry = QLineEdit(); self.tone = QLineEdit(); self.info = QPlainTextEdit(); self.info.setMaximumHeight(65); self.notes = QPlainTextEdit(); self.notes.setMaximumHeight(65)
        fields = [("公司名稱*", self.company), ("韓文公司名稱", self.korean_company), ("聯絡人", self.contact), ("Email", self.email), ("職稱", self.job_title), ("產業分類", self.industry), ("溝通語氣", self.tone)]
        for index, (label, widget) in enumerate(fields): form.addWidget(QLabel(label), index // 2, (index % 2) * 2); form.addWidget(widget, index // 2, (index % 2) * 2 + 1)
        form.addWidget(QLabel("公司資料"), 4, 0); form.addWidget(self.info, 4, 1, 1, 3); form.addWidget(QLabel("重要備註"), 5, 0); form.addWidget(self.notes, 5, 1, 1, 3); layout.addLayout(form)
        actions = QHBoxLayout(); new = QPushButton("新增空白"); new.clicked.connect(self.clear_form); save = QPushButton("保存客戶"); save.setObjectName("primary"); save.clicked.connect(self.save); delete = QPushButton("刪除客戶"); delete.clicked.connect(self.delete); actions.addWidget(new); actions.addWidget(save); actions.addWidget(delete); actions.addStretch(); layout.addLayout(actions)
        memory_box = QVBoxLayout(); memory_box.addWidget(QLabel("客戶記憶（待確認建議不會進入翻譯或郵件 AI context）")); memory_filter = QHBoxLayout(); self.memory_search = QLineEdit(); self.memory_search.setPlaceholderText("搜尋目前客戶的記憶…"); self.memory_status = QComboBox(); self.memory_status.addItem("全部狀態", ""); [self.memory_status.addItem(item, item) for item in CustomerMemoryRepository.STATUSES]; memory_find = QPushButton("搜尋記憶"); memory_find.clicked.connect(self.refresh_memory); memory_filter.addWidget(self.memory_search, 1); memory_filter.addWidget(self.memory_status); memory_filter.addWidget(memory_find); memory_box.addLayout(memory_filter)
        self.memory_table = QTableWidget(0, 4); self.memory_table.setHorizontalHeaderLabels(["分類", "內容", "狀態", "來源郵件 ID"]); self.memory_table.setSelectionBehavior(QTableWidget.SelectRows); self.memory_table.setEditTriggers(QTableWidget.NoEditTriggers); self.memory_table.cellClicked.connect(self.select_memory); self.memory_table.horizontalHeader().setStretchLastSection(True); memory_box.addWidget(self.memory_table)
        memory_form = QGridLayout(); self.memory_category = QComboBox(); self.memory_category.addItems(CustomerMemoryRepository.CATEGORIES); self.memory_content = QPlainTextEdit(); self.memory_content.setMaximumHeight(52); memory_form.addWidget(QLabel("分類"), 0, 0); memory_form.addWidget(self.memory_category, 0, 1); memory_form.addWidget(QLabel("內容*"), 0, 2); memory_form.addWidget(self.memory_content, 0, 3); memory_box.addLayout(memory_form)
        memory_actions = QHBoxLayout(); memory_new = QPushButton("新增待確認建議"); memory_new.clicked.connect(self.clear_memory_form); memory_save = QPushButton("保存修改"); memory_save.clicked.connect(self.save_memory); memory_confirm = QPushButton("確認記憶"); memory_confirm.clicked.connect(self.confirm_memory); memory_reject = QPushButton("拒絕建議"); memory_reject.clicked.connect(self.reject_memory); memory_delete = QPushButton("刪除"); memory_delete.clicked.connect(self.delete_memory); [memory_actions.addWidget(button) for button in (memory_new, memory_save, memory_confirm, memory_reject, memory_delete)]; memory_actions.addStretch(); memory_box.addLayout(memory_actions); layout.addLayout(memory_box, 2)

    def refresh(self):
        self.records = self.repository.search(self.search.text() if hasattr(self, "search") else ""); self.table.setRowCount(len(self.records))
        for row, record in enumerate(self.records):
            for column, value in enumerate([record.company_name, record.korean_company_name, record.contact_name, record.email]): self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents(); self.refresh_memory()

    def select_row(self, row: int, _column: int):
        record = self.records[row]; self.selected_id = record.id; self._load(record); self.clear_memory_form(); self.refresh_memory()

    def refresh_memory(self):
        if not hasattr(self, "memory_table"): return
        records = self.memory_repository.search(self.selected_id, self.memory_search.text(), self.memory_status.currentData()) if self.selected_id else []
        self.memory_records = records; self.memory_table.setRowCount(len(records))
        for row, record in enumerate(records):
            for column, value in enumerate([record.category, record.content, record.status, str(record.source_email_id or "")]): self.memory_table.setItem(row, column, QTableWidgetItem(value))
        self.memory_table.resizeColumnsToContents()

    def select_memory(self, row: int, _column: int):
        record = self.memory_records[row]; self.selected_memory_id = record.id; self.memory_category.setCurrentText(record.category); self.memory_content.setPlainText(record.content)

    def clear_memory_form(self):
        self.selected_memory_id = None; self.memory_category.setCurrentText("其他"); self.memory_content.clear(); self.memory_table.clearSelection()

    def save_memory(self):
        if not self.selected_id: QMessageBox.information(self, "請先選取客戶", "客戶記憶必須歸屬於目前選取的客戶。"); return
        try:
            if self.selected_memory_id is None: self.memory_repository.add_suggestion(self.selected_id, self.memory_content.toPlainText(), self.memory_category.currentText())
            else: self.memory_repository.update(self.selected_memory_id, self.memory_content.toPlainText(), self.memory_category.currentText())
        except Exception as exc: QMessageBox.warning(self, "保存記憶失敗", str(exc)); return
        self.refresh_memory(); self.clear_memory_form(); self.data_changed.emit()

    def confirm_memory(self):
        if not self.selected_memory_id: return
        try: self.memory_repository.confirm(self.selected_memory_id)
        except Exception as exc: QMessageBox.warning(self, "確認失敗", str(exc)); return
        self.refresh_memory(); self.clear_memory_form(); self.data_changed.emit()

    def reject_memory(self):
        if not self.selected_memory_id: return
        try: self.memory_repository.reject(self.selected_memory_id)
        except Exception as exc: QMessageBox.warning(self, "拒絕失敗", str(exc)); return
        self.refresh_memory(); self.clear_memory_form(); self.data_changed.emit()

    def delete_memory(self):
        if not self.selected_memory_id: return
        self.memory_repository.delete(self.selected_memory_id); self.refresh_memory(); self.clear_memory_form(); self.data_changed.emit()

    def _load(self, record: Customer):
        self.company.setText(record.company_name); self.korean_company.setText(record.korean_company_name); self.contact.setText(record.contact_name); self.email.setText(record.email); self.job_title.setText(record.job_title); self.industry.setText(record.industry); self.tone.setText(record.communication_tone); self.info.setPlainText(record.company_info); self.notes.setPlainText(record.notes)

    def clear_form(self):
        self.selected_id = None
        for widget in (self.company, self.korean_company, self.contact, self.email, self.job_title, self.industry, self.tone): widget.clear()
        self.info.clear(); self.notes.clear(); self.table.clearSelection()

    def _values(self):
        return {"company_name": self.company.text(), "korean_company_name": self.korean_company.text(), "contact_name": self.contact.text(), "email": self.email.text(), "job_title": self.job_title.text(), "industry": self.industry.text(), "communication_tone": self.tone.text(), "company_info": self.info.toPlainText(), "notes": self.notes.toPlainText()}

    def save(self):
        try:
            if self.selected_id is None: self.repository.add(**self._values())
            else: self.repository.update(self.selected_id, **self._values())
        except Exception as exc: QMessageBox.warning(self, "保存失敗", str(exc)); return
        self.refresh(); self.clear_form(); self.data_changed.emit()

    def delete(self):
        if self.selected_id is None: return
        if QMessageBox.question(self, "確認刪除", "確定刪除此客戶？客戶專屬詞條會先被保留為未指定客戶，避免資料遺失。") != QMessageBox.Yes: return
        self.repository.delete(self.selected_id); self.refresh(); self.clear_form(); self.data_changed.emit()


class GlossaryPage(QWidget):
    data_changed = Signal()
    CATEGORIES = ["公司名稱", "採購", "製造", "物流", "報價", "付款", "品質管理", "產品名稱", "品牌名稱", "型號", "其他"]

    def __init__(self, repository: GlossaryRepository, customer_repository: CustomerRepository, parent=None):
        super().__init__(parent); self.repository = repository; self.customer_repository = customer_repository; self.selected_id: int | None = None; self._build_ui(); self.refresh_customers(); self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self); title = QLabel("詞庫中心"); title.setObjectName("heading"); layout.addWidget(title); layout.addWidget(QLabel("優先權：客戶專屬詞庫 > 分類詞庫 > 全域詞庫。詞條只會在符合目前客戶範圍時送入 AI。"))
        filters = QHBoxLayout(); self.search = QLineEdit(); self.search.setPlaceholderText("搜尋韓文、繁中、指定翻譯或備註…"); self.scope = QComboBox(); self.scope.currentIndexChanged.connect(self.refresh); self.category_filter = QComboBox(); self.category_filter.addItem("全部分類", ""); self.category_filter.addItems(self.CATEGORIES); self.category_filter.currentIndexChanged.connect(self.refresh); find = QPushButton("搜尋"); find.clicked.connect(self.refresh); filters.addWidget(self.search, 1); filters.addWidget(QLabel("範圍")); filters.addWidget(self.scope); filters.addWidget(self.category_filter); filters.addWidget(find); layout.addLayout(filters)
        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(["韓文原文", "指定繁中", "指定韓文", "範圍", "分類"]); self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.cellClicked.connect(self.select_row); self.table.horizontalHeader().setStretchLastSection(True); layout.addWidget(self.table, 2)
        form = QGridLayout(); self.korean = QLineEdit(); self.chinese = QLineEdit(); self.specified = QLineEdit(); self.category = QComboBox(); self.category.setEditable(True); self.category.addItems(self.CATEGORIES); self.customer = QComboBox(); self.forbidden = QCheckBox("禁止翻譯"); self.forced = QCheckBox("強制套用"); self.notes = QPlainTextEdit(); self.notes.setMaximumHeight(55); self.example = QPlainTextEdit(); self.example.setMaximumHeight(55)
        form.addWidget(QLabel("韓文原文*"), 0, 0); form.addWidget(self.korean, 0, 1); form.addWidget(QLabel("指定繁中"), 0, 2); form.addWidget(self.chinese, 0, 3); form.addWidget(QLabel("指定韓文翻譯"), 1, 0); form.addWidget(self.specified, 1, 1); form.addWidget(QLabel("分類"), 1, 2); form.addWidget(self.category, 1, 3); form.addWidget(QLabel("所屬客戶"), 2, 0); form.addWidget(self.customer, 2, 1); form.addWidget(self.forbidden, 2, 2); form.addWidget(self.forced, 2, 3); form.addWidget(QLabel("備註"), 3, 0); form.addWidget(self.notes, 3, 1, 1, 3); form.addWidget(QLabel("使用範例"), 4, 0); form.addWidget(self.example, 4, 1, 1, 3); layout.addLayout(form)
        actions = QHBoxLayout(); new = QPushButton("新增空白"); new.clicked.connect(self.clear_form); save = QPushButton("保存詞條"); save.setObjectName("primary"); save.clicked.connect(self.save); delete = QPushButton("刪除詞條"); delete.clicked.connect(self.delete); actions.addWidget(new); actions.addWidget(save); actions.addWidget(delete); actions.addStretch(); layout.addLayout(actions)

    def refresh_customers(self):
        current = self.customer.currentData() if hasattr(self, "customer") and self.customer.count() else None
        self.customer.clear(); self.customer.addItem("全域詞庫（未指定客戶）", None)
        for record in self.customer_repository.search(): self.customer.addItem(record.company_name, record.id)
        if current is not None:
            index = self.customer.findData(current)
            if index >= 0: self.customer.setCurrentIndex(index)
        self.scope.clear(); self.scope.addItem("全部詞條", "all"); self.scope.addItem("全域詞庫", 0)
        for record in self.customer_repository.search(): self.scope.addItem(f"客戶：{record.company_name}", record.id)

    def refresh(self):
        if not hasattr(self, "table"): return
        scope = self.scope.currentData() if self.scope.count() else "all"; customer_id = None if scope == "all" else (None if scope == 0 else int(scope)); category = self.category_filter.currentData() or ""
        self.records = self.repository.search(self.search.text(), customer_id=customer_id if scope != "all" else None, category=category)
        if scope == 0: self.records = [record for record in self.records if record.customer_id is None]
        self.table.setRowCount(len(self.records))
        customers = {record.id: record.company_name for record in self.customer_repository.search()}
        for row, record in enumerate(self.records):
            scope_text = "全域" if record.customer_id is None else customers.get(record.customer_id, "未知客戶")
            for column, value in enumerate([record.korean_text, record.chinese_text, record.specified_korean, scope_text, record.category]): self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def select_row(self, row: int, _column: int):
        record = self.records[row]; self.selected_id = record.id; self.korean.setText(record.korean_text); self.chinese.setText(record.chinese_text); self.specified.setText(record.specified_korean); self.category.setCurrentText(record.category); self.customer.setCurrentIndex(max(0, self.customer.findData(record.customer_id))); self.forbidden.setChecked(record.is_forbidden); self.forced.setChecked(record.is_forced); self.notes.setPlainText(record.notes); self.example.setPlainText(record.example)

    def clear_form(self):
        self.selected_id = None; self.korean.clear(); self.chinese.clear(); self.specified.clear(); self.category.setCurrentText("其他"); self.customer.setCurrentIndex(0); self.forbidden.setChecked(False); self.forced.setChecked(False); self.notes.clear(); self.example.clear(); self.table.clearSelection()

    def _values(self):
        return {"korean_text": self.korean.text(), "chinese_text": self.chinese.text(), "specified_korean": self.specified.text(), "category": self.category.currentText() or "其他", "customer_id": self.customer.currentData(), "is_forbidden": self.forbidden.isChecked(), "is_forced": self.forced.isChecked(), "notes": self.notes.toPlainText(), "example": self.example.toPlainText()}

    def save(self):
        try:
            if self.selected_id is None: self.repository.add(**self._values())
            else: self.repository.update(self.selected_id, **self._values())
        except Exception as exc: QMessageBox.warning(self, "保存失敗", str(exc)); return
        self.refresh(); self.clear_form(); self.data_changed.emit()

    def delete(self):
        if self.selected_id is None: return
        if QMessageBox.question(self, "確認刪除", "確定刪除此詞條？") != QMessageBox.Yes: return
        self.repository.delete(self.selected_id); self.refresh(); self.clear_form(); self.data_changed.emit()
