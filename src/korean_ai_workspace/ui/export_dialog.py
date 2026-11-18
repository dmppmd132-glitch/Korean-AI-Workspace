from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QMessageBox, QProgressBar, QPushButton, QVBoxLayout

from korean_ai_workspace.services.export_service import DataExportService, ExportError


class ExportSignals(QObject):
    progress = Signal(int, int, str)
    success = Signal(str)
    failure = Signal(str)


class ExportWorker(QRunnable):
    def __init__(self, service: DataExportService, destination: str, format_name: str, categories: list[str]):
        super().__init__(); self.service = service; self.destination = destination; self.format_name = format_name; self.categories = categories; self.signals = ExportSignals()

    @Slot()
    def run(self):
        try:
            path = self.service.export(self.destination, self.format_name, self.categories, self.signals.progress.emit); self.signals.success.emit(str(path))
        except Exception as exc: self.signals.failure.emit(str(exc))


class ExportDialog(QDialog):
    def __init__(self, service: DataExportService, thread_pool: QThreadPool, parent=None):
        super().__init__(parent); self.service = service; self.thread_pool = thread_pool; self.worker = None; self.setWindowTitle("本機資料匯出"); self.resize(620, 620); self._build_ui(); self._refresh_counts()

    def _build_ui(self):
        layout = QVBoxLayout(self); heading = QLabel("本機資料匯出"); heading.setObjectName("heading"); layout.addWidget(heading); warning = QLabel("匯出資料可能包含客戶個人資訊、商業郵件、報價、交易紀錄及其他機密，請妥善保管匯出檔案。匯出只在本機執行，不會傳送至雲端或 AI API。"); warning.setWordWrap(True); layout.addWidget(warning)
        form = QFormLayout(); self.format_combo = QComboBox(); self.format_combo.addItem("JSON（完整結構）", "json"); self.format_combo.addItem("CSV（單一類別或 ZIP）", "csv"); self.format_combo.currentIndexChanged.connect(self._update_extension); form.addRow("格式", self.format_combo); layout.addLayout(form)
        layout.addWidget(QLabel("資料類別（可複選；全選 CSV 會產生 ZIP）")); self.checks = {}
        for category in self.service.categories():
            check = QCheckBox(self.service.LABELS[category]); check.setChecked(True); check.stateChanged.connect(self._refresh_counts); self.checks[category] = check; layout.addWidget(check)
        self.count_label = QLabel(); self.count_label.setWordWrap(True); layout.addWidget(self.count_label); attachment_note = QLabel("附件實體檔案：本版本不會自動複製附件內容，只匯出附件 metadata 與郵件關聯清單。"); attachment_note.setWordWrap(True); layout.addWidget(attachment_note)
        path_row = QHBoxLayout(); self.path_label = QLabel("尚未選擇目的地"); self.path_label.setWordWrap(True); choose = QPushButton("選擇目的地"); choose.clicked.connect(self.choose_destination); path_row.addWidget(self.path_label, 1); path_row.addWidget(choose); layout.addLayout(path_row)
        self.progress = QProgressBar(); self.progress.setVisible(False); layout.addWidget(self.progress); actions = QHBoxLayout(); self.export_button = QPushButton("確認並開始匯出"); self.export_button.setObjectName("primary"); self.export_button.clicked.connect(self.start_export); cancel = QPushButton("關閉"); cancel.clicked.connect(self.reject); actions.addWidget(self.export_button); actions.addWidget(cancel); layout.addLayout(actions)

    def _selected(self): return [category for category, check in self.checks.items() if check.isChecked()]

    def _refresh_counts(self):
        counts = self.service.counts(); selected = self._selected(); self.count_label.setText("預計匯出：" + "、".join(f"{self.service.LABELS[item]} {counts[item]} 筆" for item in selected) if selected else "請至少選擇一個資料類別")

    def _update_extension(self):
        if self.path_label.text() != "尚未選擇目的地": self.path_label.setText(str(self._default_path()))

    def _default_path(self):
        from datetime import datetime
        suffix = ".json" if self.format_combo.currentData() == "json" else (".csv" if len(self._selected()) == 1 else ".zip")
        return Path.cwd() / f"korean-ai-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}-v{self.service.SOFTWARE_VERSION}{suffix}"

    def choose_destination(self):
        suffix = "JSON (*.json)" if self.format_combo.currentData() == "json" else ("CSV (*.csv)" if len(self._selected()) == 1 else "ZIP (*.zip)")
        path, _ = QFileDialog.getSaveFileName(self, "選擇匯出目的地", str(self._default_path()), suffix)
        if path: self.path_label.setText(path)

    def start_export(self):
        selected = self._selected()
        if not selected: QMessageBox.warning(self, "未選擇資料", "請至少選擇一個資料類別。"); return
        if self.path_label.text() == "尚未選擇目的地": self.path_label.setText(str(self._default_path()))
        if QMessageBox.question(self, "確認匯出", "匯出可能包含客戶個人資訊、商業郵件及交易紀錄，且不包含 API Key 或其他登入憑證。確定開始嗎？") != QMessageBox.Yes: return
        self.export_button.setEnabled(False); self.progress.setVisible(True); self.progress.setRange(0, len(selected)); self.progress.setValue(0); self.worker = ExportWorker(self.service, self.path_label.text(), self.format_combo.currentData(), selected); self.worker.signals.progress.connect(self.on_progress); self.worker.signals.success.connect(self.on_success); self.worker.signals.failure.connect(self.on_failure); self.thread_pool.start(self.worker)

    @Slot(int, int, str)
    def on_progress(self, current: int, total: int, label: str): self.progress.setRange(0, total); self.progress.setValue(current); self.progress.setFormat(f"正在匯出：{label}（{current}/{total}）")

    @Slot(str)
    def on_success(self, path: str): self.export_button.setEnabled(True); QMessageBox.information(self, "匯出完成", f"匯出完成：\n{path}"); self.accept()

    @Slot(str)
    def on_failure(self, message: str): self.export_button.setEnabled(True); self.progress.setVisible(False); QMessageBox.warning(self, "匯出失敗", message)
