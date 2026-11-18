from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from korean_ai_workspace.settings.paths import AppPaths


class BackupError(RuntimeError):
    pass


class BackupService:
    FORMAT_VERSION = 1

    def __init__(self, paths: AppPaths):
        self.paths = paths

    def create_backup(self, destination: str | Path | None = None) -> Path:
        target = Path(destination) if destination else self.paths.backups / f"korean-ai-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
        target.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "format": "Korean-AI-Workspace-backup",
            "version": self.FORMAT_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "contains": ["database", "attachments", "encrypted_settings"],
        }
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            database = self.paths.database / "workspace.db"
            if database.exists():
                archive.write(database, "data/database/workspace.db")
            settings = self.paths.config / "settings.json"
            if settings.exists():
                archive.write(settings, "config/settings.json")
            fallback_key = self.paths.config / "secret.key"
            if fallback_key.exists():
                archive.write(fallback_key, "config/secret.key")
            if self.paths.attachments.exists():
                for file_path in self.paths.attachments.rglob("*"):
                    if file_path.is_file():
                        archive.write(file_path, f"data/attachments/{file_path.relative_to(self.paths.attachments).as_posix()}")
        return target

    def restore_backup(self, source: str | Path) -> None:
        source_path = Path(source)
        if not source_path.is_file():
            raise BackupError("找不到備份檔案")
        with tempfile.TemporaryDirectory(prefix="korean-ai-restore-") as temp_dir:
            temp_path = Path(temp_dir)
            try:
                with zipfile.ZipFile(source_path) as archive:
                    self._validate_archive(archive)
                    archive.extractall(temp_path)
            except (zipfile.BadZipFile, OSError) as exc:
                raise BackupError("備份檔案不是有效的 ZIP 或無法讀取") from exc
            manifest_path = temp_path / "manifest.json"
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if manifest.get("format") != "Korean-AI-Workspace-backup" or manifest.get("version") != self.FORMAT_VERSION:
                    raise ValueError("版本不相容")
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                raise BackupError("備份格式不相容或 manifest 損毀") from exc
            database = temp_path / "data" / "database" / "workspace.db"
            if not database.is_file():
                raise BackupError("備份缺少資料庫檔案")
            self.paths.database.mkdir(parents=True, exist_ok=True)
            self.paths.config.mkdir(parents=True, exist_ok=True)
            self.paths.attachments.mkdir(parents=True, exist_ok=True)
            rollback = temp_path / "rollback"
            self._snapshot_current(rollback)
            try:
                self._apply_restore(temp_path, database)
            except Exception as exc:
                try:
                    self._restore_snapshot(rollback)
                except Exception as rollback_exc:
                    raise BackupError("還原失敗，且無法完整回復原資料，請立即使用其他備份") from rollback_exc
                raise BackupError("還原失敗，原本資料已保留") from exc

    def _snapshot_current(self, destination: Path) -> None:
        (destination / "data" / "database").mkdir(parents=True, exist_ok=True)
        (destination / "data").mkdir(parents=True, exist_ok=True)
        (destination / "config").mkdir(parents=True, exist_ok=True)
        current_db = self.paths.database / "workspace.db"
        if current_db.exists():
            shutil.copy2(current_db, destination / "data" / "database" / "workspace.db")
        if self.paths.attachments.exists():
            shutil.copytree(self.paths.attachments, destination / "data" / "attachments", dirs_exist_ok=True)
        for name in ("settings.json", "secret.key"):
            current = self.paths.config / name
            if current.exists():
                shutil.copy2(current, destination / "config" / name)

    def _apply_restore(self, extracted: Path, database: Path) -> None:
        database_target = self.paths.database / "workspace.db"
        temporary_database = self.paths.database / "workspace.db.restore.tmp"
        shutil.copy2(database, temporary_database)
        temporary_database.replace(database_target)
        for name in ("settings.json", "secret.key"):
            target = self.paths.config / name
            source = extracted / "config" / name
            if source.exists():
                temporary = self.paths.config / f"{name}.restore.tmp"
                shutil.copy2(source, temporary)
                temporary.replace(target)
            elif target.exists():
                target.unlink()
        if self.paths.attachments.exists():
            shutil.rmtree(self.paths.attachments)
        self.paths.attachments.mkdir(parents=True, exist_ok=True)
        restored_attachments = extracted / "data" / "attachments"
        if restored_attachments.exists():
            shutil.copytree(restored_attachments, self.paths.attachments, dirs_exist_ok=True)

    def _restore_snapshot(self, snapshot: Path) -> None:
        current_db = self.paths.database / "workspace.db"
        snapshot_db = snapshot / "data" / "database" / "workspace.db"
        if snapshot_db.exists():
            shutil.copy2(snapshot_db, current_db)
        elif current_db.exists():
            current_db.unlink()
        if self.paths.attachments.exists():
            shutil.rmtree(self.paths.attachments)
        snapshot_attachments = snapshot / "data" / "attachments"
        if snapshot_attachments.exists():
            shutil.copytree(snapshot_attachments, self.paths.attachments)
        else:
            self.paths.attachments.mkdir(parents=True, exist_ok=True)
        self.paths.config.mkdir(parents=True, exist_ok=True)
        for name in ("settings.json", "secret.key"):
            target = self.paths.config / name
            source = snapshot / "config" / name
            if source.exists():
                shutil.copy2(source, target)
            elif target.exists():
                target.unlink()

    @staticmethod
    def _validate_archive(archive: zipfile.ZipFile) -> None:
        names = {info.filename for info in archive.infolist()}
        if "manifest.json" not in names:
            raise BackupError("備份缺少 manifest.json")
        allowed_roots = ("manifest.json", "data/database/", "data/attachments/", "config/")
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            if path.is_absolute() or ".." in path.parts or not info.filename.startswith(allowed_roots):
                raise BackupError("備份包含不安全的檔案路徑")
            # ZIP symlinks could escape the extraction directory on some platforms.
            if ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise BackupError("備份不可包含符號連結")
