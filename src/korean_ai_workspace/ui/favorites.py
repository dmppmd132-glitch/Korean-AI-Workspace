from __future__ import annotations

from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QPlainTextEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from korean_ai_workspace.repositories.customer_repository import CustomerRepository
from korean_ai_workspace.repositories.favorite_repository import FavoriteRepository


class FavoriteDetailDialog(QDialog):
    def __init__(self, record, parent=None):
        super().__init__(parent); self.setWindowTitle("收藏完整內容"); self.resize(700, 420)
        layout = QFormLayout(self); layout.addRow("翻譯版本", QLabel(FavoriteRepository.VARIANTS.get(record.variant_type, record.variant_type))); layout.addRow("翻譯方向", QLabel(f"{record.source_language} → {record.target_language}")); layout.addRow("模型", QLabel(f"{record.provider} / {record.model}")); source = QPlainTextEdit(record.source_text); source.setReadOnly(True); translated = QPlainTextEdit(record.translation_text); translated.setReadOnly(True); layout.addRow("原文", source); layout.addRow("譯文", translated)


class FavoritePage(QWidget):
    def __init__(self, repository: FavoriteRepository, customer_repository: CustomerRepository, parent=None):
        super().__init__(parent); self.repository = repository; self.customer_repository = customer_repository; self.records = []; self._build_ui(); self.refresh_customers(); self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self); heading = QLabel("翻譯收藏"); heading.setObjectName("heading"); layout.addWidget(heading); layout.addWidget(QLabel("收藏是翻譯結果的獨立快照，之後重新翻譯不會改變既有收藏。"))
        filters = QHBoxLayout(); self.search = QLineEdit(); self.search.setPlaceholderText("搜尋原文或譯文…"); self.language = QComboBox(); self.language.addItem("全部方向", ""); self.language.addItem("韓文 → 繁中", "ko"); self.language.addItem("繁中 → 韓文", "zh-TW"); self.variant = QComboBox(); self.variant.addItem("全部版本", ""); [self.variant.addItem(label, key) for key, label in FavoriteRepository.VARIANTS.items()]; self.customer = QComboBox(); find = QPushButton("搜尋"); find.clicked.connect(self.refresh); self.search.returnPressed.connect(self.refresh); filters.addWidget(self.search, 1); filters.addWidget(self.language); filters.addWidget(self.variant); filters.addWidget(self.customer); filters.addWidget(find); layout.addLayout(filters)
        self.table = QTableWidget(0, 6); self.table.setHorizontalHeaderLabels(["收藏日期", "方向", "版本", "原文", "譯文", "客戶"]); self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.cellDoubleClicked.connect(self.open_detail); self.table.horizontalHeader().setStretchLastSection(True); layout.addWidget(self.table, 1)
        actions = QHBoxLayout(); copy_source = QPushButton("複製原文"); copy_source.clicked.connect(self.copy_source); copy_translation = QPushButton("複製譯文"); copy_translation.clicked.connect(self.copy_translation); detail = QPushButton("開啟完整內容"); detail.clicked.connect(self.open_selected); delete = QPushButton("取消收藏"); delete.clicked.connect(self.delete_selected); actions.addWidget(copy_source); actions.addWidget(copy_translation); actions.addWidget(detail); actions.addWidget(delete); actions.addStretch(); layout.addLayout(actions)

    def refresh_customers(self):
        current = self.customer.currentData() if self.customer.count() else None; self.customer.clear(); self.customer.addItem("全部客戶", None)
        for record in self.customer_repository.search(): self.customer.addItem(record.company_name, record.id)
        if current is not None:
            index = self.customer.findData(current)
            if index >= 0: self.customer.setCurrentIndex(index)

    def refresh(self):
        if not hasattr(self, "table"): return
        self.records = self.repository.list(self.search.text(), self.language.currentData(), self.variant.currentData(), self.customer.currentData()); names = {record.id: record.company_name for record in self.customer_repository.search()}; self.table.setRowCount(len(self.records))
        for row, record in enumerate(self.records):
            timestamp = record.created_at.strftime("%Y-%m-%d %H:%M") if record.created_at else ""
            values = [timestamp, f"{record.source_language} → {record.target_language}", FavoriteRepository.VARIANTS.get(record.variant_type, record.variant_type), record.source_text, record.translation_text, names.get(record.customer_id, "未指定")]
            for column, value in enumerate(values): self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def _selected(self):
        row = self.table.currentRow()
        return self.records[row] if 0 <= row < len(self.records) else None

    def open_detail(self, row: int, _column: int):
        if 0 <= row < len(self.records): FavoriteDetailDialog(self.records[row], self).exec()

    def open_selected(self):
        record = self._selected()
        if record: FavoriteDetailDialog(record, self).exec()

    def copy_source(self):
        record = self._selected()
        if record: QApplication.clipboard().setText(record.source_text)

    def copy_translation(self):
        record = self._selected()
        if record: QApplication.clipboard().setText(record.translation_text)

    def delete_selected(self):
        record = self._selected()
        if not record: return
        if QMessageBox.question(self, "確認取消收藏", "只刪除收藏快照，不會刪除翻譯歷史。是否繼續？") != QMessageBox.Yes: return
        self.repository.delete(record.id); self.refresh()
