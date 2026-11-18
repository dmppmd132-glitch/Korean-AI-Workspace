from __future__ import annotations

import csv
import json
import os
import shutil
import tempfile
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

from sqlalchemy import select

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.models.entities import (
    Attachment, Customer, CustomerMemory, CustomerMemoryRevision, EmailAttachmentLink,
    EmailRecord, GlossaryTerm, TranslationFavorite, TranslationHistory,
)


class ExportError(RuntimeError):
    pass


ProgressCallback = Callable[[int, int, str], None]


class DataExportService:
    SCHEMA_VERSION = "1.0"
    SOFTWARE_VERSION = "1.0.0-dev"
    TABLES = {
        "customers": Customer,
        "glossary_terms": GlossaryTerm,
        "translation_history": TranslationHistory,
        "translation_favorites": TranslationFavorite,
        "customer_memories": CustomerMemory,
        "customer_memory_revisions": CustomerMemoryRevision,
        "emails": EmailRecord,
        "attachments": Attachment,
        "email_attachment_links": EmailAttachmentLink,
    }
    LABELS = {
        "customers": "客戶資料", "glossary_terms": "詞庫資料", "translation_history": "翻譯歷史",
        "translation_favorites": "翻譯收藏", "customer_memories": "客戶記憶",
        "customer_memory_revisions": "客戶記憶變更歷史", "emails": "郵件與回覆草稿",
        "attachments": "附件資料清單", "email_attachment_links": "郵件附件關聯",
    }

    def __init__(self, database: Database): self.database = database

    @classmethod
    def categories(cls) -> tuple[str, ...]: return tuple(cls.TABLES)

    def counts(self) -> dict[str, int]:
        with self.database.session() as session:
            return {name: len(session.scalars(select(model)).all()) for name, model in self.TABLES.items()}

    def export(self, destination: str | Path, format_name: str, categories: list[str] | tuple[str, ...] | None = None, progress: ProgressCallback | None = None) -> Path:
        destination = Path(destination)
        selected = list(self.TABLES if categories is None else categories)
        invalid = [item for item in selected if item not in self.TABLES]
        if invalid: raise ExportError(f"不支援的資料類別：{', '.join(invalid)}")
        if not selected: raise ExportError("至少選擇一個資料類別")
        if format_name not in {"csv", "json"}: raise ExportError("匯出格式必須是 CSV 或 JSON")
        destination.parent.mkdir(parents=True, exist_ok=True)
        records = self._read_consistent(selected, progress)
        try:
            if format_name == "json": self._write_json(destination, records)
            elif len(selected) == 1: self._write_csv(destination, selected[0], records[selected[0]])
            else: self._write_csv_zip(destination, records)
        except (OSError, csv.Error, TypeError, ValueError, zipfile.BadZipFile) as exc:
            if destination.exists(): destination.unlink()
            raise ExportError(f"匯出檔案寫入失敗：{exc}") from exc
        return destination

    def _read_consistent(self, selected: list[str], progress: ProgressCallback | None) -> dict[str, list[dict[str, object]]]:
        result: dict[str, list[dict[str, object]]] = {}
        total = len(selected)
        # One ORM session keeps all reads in the same SQLite transaction.
        with self.database.session() as session:
            for index, name in enumerate(selected, 1):
                model = self.TABLES[name]
                rows = session.scalars(select(model).order_by(model.id)).all()
                result[name] = [self._row_to_dict(row) for row in rows]
                if progress: progress(index, total, self.LABELS[name])
        return result

    @staticmethod
    def _row_to_dict(row) -> dict[str, object]:
        values: dict[str, object] = {}
        for column in row.__table__.columns:
            value = getattr(row, column.name)
            if isinstance(value, (datetime, date)): value = value.isoformat()
            values[column.name] = value
        return values

    def _write_json(self, destination: Path, records: dict[str, list[dict[str, object]]]) -> None:
        payload = {"schema_version": self.SCHEMA_VERSION, "software_version": self.SOFTWARE_VERSION, "exported_at": datetime.now(timezone.utc).isoformat(), "attachment_files_included": False, "attachment_export_note": "本次只匯出附件 metadata 與郵件關聯，不包含實體附件檔案。", "data": records}
        self._atomic_write(destination, json.dumps(payload, ensure_ascii=False, indent=2))

    def _write_csv(self, destination: Path, category: str, rows: list[dict[str, object]]) -> None:
        headers = list(rows[0]) if rows else [column.name for column in self.TABLES[category].__table__.columns]
        with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", newline="", delete=False, dir=destination.parent, suffix=".tmp") as handle:
            temporary = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
            writer.writeheader(); writer.writerows({key: self._csv_value(row.get(key)) for key in headers} for row in rows)
        temporary.replace(destination)

    def _write_csv_zip(self, destination: Path, records: dict[str, list[dict[str, object]]]) -> None:
        temporary_dir = Path(tempfile.mkdtemp(prefix="korean-ai-export-", dir=destination.parent))
        temporary_zip = destination.with_suffix(destination.suffix + ".tmp")
        try:
            for category, rows in records.items(): self._write_csv(temporary_dir / f"{category}.csv", category, rows)
            with zipfile.ZipFile(temporary_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for csv_file in temporary_dir.glob("*.csv"): archive.write(csv_file, csv_file.name)
            temporary_zip.replace(destination)
        finally:
            shutil.rmtree(temporary_dir, ignore_errors=True)
            if temporary_zip.exists(): temporary_zip.unlink()

    @staticmethod
    def _csv_value(value: object) -> object:
        if value is None: return ""
        if isinstance(value, bool): return "1" if value else "0"
        return value

    @staticmethod
    def _atomic_write(destination: Path, content: str) -> None:
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        try:
            temporary.write_text(content, encoding="utf-8", newline="")
            os.replace(temporary, destination)
        finally:
            if temporary.exists(): temporary.unlink()
