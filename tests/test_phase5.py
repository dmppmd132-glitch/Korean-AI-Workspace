from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.repositories.attachment_repository import AttachmentRepository
from korean_ai_workspace.repositories.translation_repository import TranslationRepository
from korean_ai_workspace.services.ai.config import AIProviderConfig
from korean_ai_workspace.services.backup_service import BackupError, BackupService
from korean_ai_workspace.services.secret_store import SecretStore
from korean_ai_workspace.services.settings_store import SettingsStore
from korean_ai_workspace.settings.paths import AppPaths
from korean_ai_workspace.ui.main_window import MainWindow


def paths_for(tmp_path, monkeypatch) -> AppPaths:
    monkeypatch.setenv("KOREAN_AI_WORKSPACE_HOME", str(tmp_path))
    return AppPaths.from_environment()


def test_secret_store_round_trip_never_writes_plaintext(tmp_path):
    secret = "sk-test-secret-123"
    store = SecretStore(tmp_path / "config")
    encrypted = store.encrypt(secret)
    assert encrypted != secret
    assert store.decrypt(encrypted) == secret
    assert secret not in encrypted


def test_settings_store_encrypts_api_key_and_loads_it(tmp_path):
    store = SettingsStore(tmp_path / "config")
    config = AIProviderConfig("openai", "sk-settings-secret", "test-model", "https://example.test/v1")
    store.save_provider(config)
    raw = store.path.read_text(encoding="utf-8")
    assert "sk-settings-secret" not in raw
    assert json.loads(raw)["encrypted_api_key"]
    loaded = store.load_provider()
    assert loaded is not None and loaded.api_key == config.api_key and loaded.model == config.model


def test_backup_and_restore_database_attachments_and_settings(tmp_path, monkeypatch):
    paths = paths_for(tmp_path, monkeypatch)
    database = Database(paths.database_url); database.create_all()
    translations = TranslationRepository(database)
    translations.add(source_text="原始資料", source_language="ko", target_language="zh-TW", best_translation="備份翻譯", provider="test", model="fake")
    source = tmp_path / "source.txt"; source.write_text("attachment-data", encoding="utf-8")
    attachment = AttachmentRepository(database, paths.attachment_directory)
    email_id = 1
    # The attachment repository only needs a link target for this test, so use a real email row.
    from korean_ai_workspace.repositories.email_repository import EmailRepository
    email = EmailRepository(database).add(original_content="郵件內容", subject="備份")
    attachment.add_file(source, email.id)
    SettingsStore(paths.config).save_provider(AIProviderConfig("openai", "backup-secret", "model", "https://example.test/v1"))
    backup = BackupService(paths).create_backup(tmp_path / "backup.zip")
    assert backup.exists()
    database.engine.dispose()
    restored_paths = paths_for(tmp_path / "restored", monkeypatch)
    restored_database = Database(restored_paths.database_url); restored_database.create_all()
    # Copy the archive into the second portable root and restore there.
    BackupService(restored_paths).restore_backup(backup)
    restored_database.engine.dispose()
    check_db = Database(restored_paths.database_url); check_db.create_all()
    assert TranslationRepository(check_db).list_recent()[0].source_text == "原始資料"
    assert list(restored_paths.attachments.glob("*"))[0].read_text(encoding="utf-8") == "attachment-data"
    assert SettingsStore(restored_paths.config).load_provider().api_key == "backup-secret"


def test_backup_rejects_path_traversal(tmp_path, monkeypatch):
    paths = paths_for(tmp_path, monkeypatch)
    archive_path = tmp_path / "unsafe.zip"
    manifest = {"format": "Korean-AI-Workspace-backup", "version": 1}
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        archive.writestr("../outside.txt", "unsafe")
    with pytest.raises(BackupError):
        BackupService(paths).restore_backup(archive_path)


def test_phase5_system_management_page_is_constructible_offscreen(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    paths = paths_for(tmp_path, monkeypatch)
    database = Database(paths.database_url); database.create_all()
    window = MainWindow(TranslationRepository(database), paths=paths)
    assert window.pages.count() == 6
    assert {button.text() for button in window.pages.widget(5).findChildren(QPushButton)} >= {"保存目前 AI 設定（加密）", "建立手動備份", "從備份還原"}
    assert window.settings_store.secrets.backend in {"windows-dpapi", "local-fernet"}
    window.close(); window.floating_window.close(); app.quit()
