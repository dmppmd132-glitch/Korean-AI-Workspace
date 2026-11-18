from __future__ import annotations

import csv
import json
import zipfile

import pytest
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QApplication

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.models.entities import (
    Attachment, Customer, CustomerMemory, CustomerMemoryRevision, EmailAttachmentLink,
    EmailRecord, GlossaryTerm, TranslationFavorite, TranslationHistory,
)
from korean_ai_workspace.services.export_service import DataExportService, ExportError
from korean_ai_workspace.ui.export_dialog import ExportDialog


def setup(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'workspace.db'}"); db.create_all(); return db, DataExportService(db)


def seed(db):
    with db.session() as session:
        customer = Customer(company_name='台灣, "測試" 公司\n第二行', korean_company_name="한국 회사", email="client@example.com")
        session.add(customer); session.flush()
        session.add(GlossaryTerm(korean_text="납기", chinese_text='交期, "重要"', customer_id=customer.id, category="物流"))
        history = TranslationHistory(source_text='原文, "含逗號"\n換行', source_language="ko", target_language="zh-TW", best_translation="最佳 번역", formal_translation="正式", natural_translation="自然", friendly_translation="親切", provider="test", model="model", customer_id=customer.id)
        session.add(history); session.flush()
        session.add(TranslationFavorite(translation_history_id=history.id, source_text=history.source_text, source_language="ko", target_language="zh-TW", translation_text=history.best_translation, variant_type="best", provider="test", model="model", customer_id=customer.id))
        email = EmailRecord(customer_id=customer.id, subject="報價", original_content="郵件內容", translated_content="翻譯", analysis_json='{"summary":"摘要"}', reply_intent="回覆", draft_formal="正式回信", draft_natural="自然回信", draft_friendly="親切回信", selected_draft="正式回信", status="草稿完成")
        session.add(email); session.flush()
        memory = CustomerMemory(customer_id=customer.id, category="合作歷史", content="已確認記憶", status="已確認", source_email_id=email.id); session.add(memory); session.flush()
        session.add(CustomerMemoryRevision(memory_id=memory.id, customer_id=customer.id, category=memory.category, content=memory.content, status=memory.status, change_type="新增"))
        attachment = Attachment(sha256="a" * 64, original_name="報價,附件.txt", stored_path="data/attachments/fake.txt", size_bytes=12, mime_type="text/plain"); session.add(attachment); session.flush(); session.add(EmailAttachmentLink(email_id=email.id, attachment_id=attachment.id))


def test_single_csv_is_utf8_bom_and_preserves_special_characters(tmp_path):
    db, exporter = setup(tmp_path); seed(db); output = exporter.export(tmp_path / "customers.csv", "csv", ["customers"])
    raw = output.read_bytes(); assert raw.startswith(b"\xef\xbb\xbf")
    with output.open("r", encoding="utf-8-sig", newline="") as handle: rows = list(csv.DictReader(handle))
    assert rows[0]["company_name"] == '台灣, "測試" 公司\n第二行'


def test_all_csv_is_zip_with_every_selected_category(tmp_path):
    db, exporter = setup(tmp_path); seed(db); output = exporter.export(tmp_path / "all.zip", "csv", list(DataExportService.categories()))
    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
    assert "customers.csv" in names and "translation_favorites.csv" in names and "email_attachment_links.csv" in names


def test_json_preserves_schema_all_fields_relations_and_excludes_secrets(tmp_path):
    db, exporter = setup(tmp_path); seed(db); output = exporter.export(tmp_path / "data.json", "json")
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"
    assert payload["data"]["customers"][0]["id"] == 1
    assert payload["data"]["translation_favorites"][0]["translation_history_id"] == 1
    assert payload["data"]["email_attachment_links"][0]["attachment_id"] == 1
    assert payload["attachment_files_included"] is False
    serialized = output.read_text(encoding="utf-8").lower()
    assert "api_key" not in serialized and "bearer" not in serialized and "password" not in serialized


def test_empty_database_exports_and_invalid_selection_is_rejected(tmp_path):
    _db, exporter = setup(tmp_path)
    output = exporter.export(tmp_path / "empty.json", "json", ["customers"])
    assert json.loads(output.read_text(encoding="utf-8"))["data"]["customers"] == []
    with pytest.raises(ExportError): exporter.export(tmp_path / "none.json", "json", [])


def test_export_does_not_modify_database_and_progress_reports_categories(tmp_path):
    db, exporter = setup(tmp_path); seed(db); progress = []
    output = exporter.export(tmp_path / "data.zip", "csv", ["customers", "emails"], lambda current, total, label: progress.append((current, total, label)))
    assert output.exists(); assert [item[0] for item in progress] == [1, 2]; assert exporter.counts()["customers"] == 1


def test_export_dialog_is_constructible_offscreen(tmp_path):
    app = QApplication.instance() or QApplication([])
    db, exporter = setup(tmp_path)
    dialog = ExportDialog(exporter, QThreadPool.globalInstance())
    assert dialog.format_combo.currentData() == "json"
    assert len(dialog.checks) == len(DataExportService.categories())
    dialog.close(); app.processEvents()
