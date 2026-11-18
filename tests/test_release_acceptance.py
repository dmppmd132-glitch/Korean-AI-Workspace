from __future__ import annotations

import json
import zipfile

import pytest
from sqlalchemy import text

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.repositories.attachment_repository import AttachmentRepository
from korean_ai_workspace.repositories.customer_repository import CustomerRepository
from korean_ai_workspace.repositories.email_repository import EmailRepository
from korean_ai_workspace.repositories.glossary_repository import GlossaryRepository
from korean_ai_workspace.repositories.translation_repository import TranslationRepository
from korean_ai_workspace.services.backup_service import BackupError, BackupService
from korean_ai_workspace.settings.paths import AppPaths


def setup_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("KOREAN_AI_WORKSPACE_HOME", str(tmp_path))
    paths = AppPaths.from_environment()
    database = Database(paths.database_url); database.create_all()
    return paths, database


def test_release_data_persists_after_reopen_and_integrity_check(tmp_path, monkeypatch):
    paths, database = setup_workspace(tmp_path, monkeypatch)
    customers = CustomerRepository(database); glossary = GlossaryRepository(database); emails = EmailRepository(database)
    history = TranslationRepository(database); attachments = AttachmentRepository(database, paths.attachment_directory)
    customer_a = customers.add(company_name="甲公司", contact_name="甲先生")
    customer_b = customers.add(company_name="乙公司", contact_name="乙女士")
    glossary.add(korean_text="납기", chinese_text="甲方交期", customer_id=customer_a.id, category="物流")
    email_a = emails.add(customer_id=customer_a.id, subject="報價", original_content="견적을 부탁드립니다", status="已翻譯")
    email_b = emails.add(customer_id=customer_b.id, subject="交期", original_content="납기를 알려 주세요")
    history.add(source_text="안녕하세요", source_language="ko", target_language="zh-TW", best_translation="您好", provider="test", model="fake", customer_id=customer_a.id)
    first = tmp_path / "報價.txt"; first.write_text("same", encoding="utf-8")
    second = tmp_path / "same-content.bin"; second.write_bytes(b"same")
    attachment_a, _ = attachments.add_file(first, email_a.id)
    attachment_b, duplicate = attachments.add_file(second, email_b.id)
    assert duplicate is True and attachment_a.id == attachment_b.id
    database.engine.dispose()

    reopened = Database(paths.database_url); reopened.create_all()
    assert len(CustomerRepository(reopened).search()) == 2
    assert len(EmailRepository(reopened).search()) == 2
    assert len(TranslationRepository(reopened).list_recent()) == 1
    assert len(GlossaryRepository(reopened).search()) == 1
    with reopened.engine.connect() as connection:
        assert connection.execute(text("PRAGMA integrity_check")).scalar() == "ok"
        assert connection.execute(text("PRAGMA foreign_key_check")).all() == []


def test_backup_manifest_contents_and_corrupt_or_incompatible_rejection(tmp_path, monkeypatch):
    paths, database = setup_workspace(tmp_path, monkeypatch)
    email = EmailRepository(database).add(subject="備份", original_content="內容")
    source = tmp_path / "document.txt"; source.write_text("attachment", encoding="utf-8")
    AttachmentRepository(database, paths.attachment_directory).add_file(source, email.id)
    backup = BackupService(paths).create_backup(tmp_path / "complete.zip")
    with zipfile.ZipFile(backup) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "data/database/workspace.db" in names
        assert any(name.startswith("data/attachments/") for name in names)
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["format"] == "Korean-AI-Workspace-backup"

    corrupt = tmp_path / "corrupt.zip"; corrupt.write_bytes(b"not a zip")
    with pytest.raises(BackupError): BackupService(paths).restore_backup(corrupt)
    incompatible = tmp_path / "incompatible.zip"
    with zipfile.ZipFile(incompatible, "w") as archive:
        archive.writestr("manifest.json", json.dumps({"format": "Korean-AI-Workspace-backup", "version": 999}))
    with pytest.raises(BackupError): BackupService(paths).restore_backup(incompatible)


def test_failed_restore_keeps_original_database_and_attachments(tmp_path, monkeypatch):
    paths, database = setup_workspace(tmp_path, monkeypatch)
    emails = EmailRepository(database); email = emails.add(subject="原始資料", original_content="keep-me")
    source = tmp_path / "original.txt"; source.write_text("original-attachment", encoding="utf-8")
    AttachmentRepository(database, paths.attachment_directory).add_file(source, email.id)
    backup = BackupService(paths).create_backup(tmp_path / "restore.zip")
    service = BackupService(paths)

    def fail_after_database_write(extracted, database_file):
        (paths.database / "workspace.db").write_bytes(database_file.read_bytes())
        raise OSError("simulated restore failure")

    monkeypatch.setattr(service, "_apply_restore", fail_after_database_write)
    with pytest.raises(BackupError, match="原本資料已保留"):
        service.restore_backup(backup)
    database.engine.dispose()
    reopened = Database(paths.database_url); reopened.create_all()
    assert EmailRepository(reopened).get(email.id).original_content == "keep-me"
    assert next(paths.attachments.glob("*" )).read_text(encoding="utf-8") == "original-attachment"
