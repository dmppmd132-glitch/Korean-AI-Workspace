from __future__ import annotations

from sqlalchemy import select, update

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.models.entities import EmailRecord


class EmailRepository:
    STATUSES = ("待處理", "已翻譯", "分析完成", "回信撰寫中", "草稿完成", "已完成")

    def __init__(self, database: Database): self.database = database

    def add(self, **values) -> EmailRecord:
        if not values.get("original_content", "").strip(): raise ValueError("原始郵件內容不可為空白")
        record = EmailRecord(**values)
        with self.database.session() as session:
            session.add(record); session.flush(); session.refresh(record)
        return record

    def update(self, email_id: int, **values) -> EmailRecord:
        with self.database.session() as session:
            record = session.get(EmailRecord, email_id)
            if record is None: raise ValueError("找不到指定郵件")
            for key, value in values.items():
                if hasattr(record, key): setattr(record, key, value)
            session.flush(); session.refresh(record)
            return record

    def get(self, email_id: int) -> EmailRecord | None:
        with self.database.session() as session: return session.get(EmailRecord, email_id)

    def search(self, keyword: str = "", customer_id: int | None = None, limit: int = 200) -> list[EmailRecord]:
        statement = select(EmailRecord).order_by(EmailRecord.updated_at.desc()).limit(limit)
        if keyword.strip():
            pattern = f"%{keyword.strip()}%"; statement = statement.where(EmailRecord.subject.like(pattern) | EmailRecord.original_content.like(pattern) | EmailRecord.translated_content.like(pattern))
        if customer_id is not None: statement = statement.where(EmailRecord.customer_id == customer_id)
        with self.database.session() as session: return list(session.scalars(statement))
