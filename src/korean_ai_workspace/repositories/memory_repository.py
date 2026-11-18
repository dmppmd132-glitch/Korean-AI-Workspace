from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.models.entities import CustomerMemory, CustomerMemoryRevision


class CustomerMemoryRepository:
    STATUSES = ("待確認", "已確認", "已拒絕")
    CATEGORIES = ("基本資料", "溝通習慣", "專業術語", "合作歷史", "重要商業事項", "其他")

    def __init__(self, database: Database): self.database = database

    def add_suggestion(self, customer_id: int, content: str, category: str = "其他", source_email_id: int | None = None) -> CustomerMemory:
        if not content.strip(): raise ValueError("記憶內容不可為空白")
        if category not in self.CATEGORIES: category = "其他"
        record = CustomerMemory(customer_id=customer_id, content=content.strip(), category=category, source_email_id=source_email_id, status="待確認")
        with self.database.session() as session:
            session.add(record); session.flush(); session.refresh(record)
            self._revision(session, record, "新增建議")
        return record

    def update(self, memory_id: int, content: str, category: str, source_email_id: int | None = None) -> CustomerMemory:
        if not content.strip(): raise ValueError("記憶內容不可為空白")
        with self.database.session() as session:
            record = session.get(CustomerMemory, memory_id)
            if record is None: raise ValueError("找不到指定記憶")
            record.content = content.strip(); record.category = category if category in self.CATEGORIES else "其他"; record.source_email_id = source_email_id
            session.flush(); session.refresh(record); self._revision(session, record, "修改")
            return record

    def confirm(self, memory_id: int) -> CustomerMemory:
        with self.database.session() as session:
            record = session.get(CustomerMemory, memory_id)
            if record is None: raise ValueError("找不到指定記憶")
            record.status = "已確認"; record.confirmed_at = datetime.now(timezone.utc)
            session.flush(); session.refresh(record); self._revision(session, record, "確認")
            return record

    def reject(self, memory_id: int) -> CustomerMemory:
        with self.database.session() as session:
            record = session.get(CustomerMemory, memory_id)
            if record is None: raise ValueError("找不到指定記憶")
            record.status = "已拒絕"; record.confirmed_at = None
            session.flush(); session.refresh(record); self._revision(session, record, "拒絕")
            return record

    def search(self, customer_id: int, keyword: str = "", status: str = "") -> list[CustomerMemory]:
        statement = select(CustomerMemory).where(CustomerMemory.customer_id == customer_id).order_by(CustomerMemory.updated_at.desc())
        if keyword.strip(): statement = statement.where(CustomerMemory.content.like(f"%{keyword.strip()}%"))
        if status: statement = statement.where(CustomerMemory.status == status)
        with self.database.session() as session: return list(session.scalars(statement))

    def revisions(self, memory_id: int) -> list[CustomerMemoryRevision]:
        statement = select(CustomerMemoryRevision).where(CustomerMemoryRevision.memory_id == memory_id).order_by(CustomerMemoryRevision.changed_at.desc())
        with self.database.session() as session: return list(session.scalars(statement))

    def delete(self, memory_id: int) -> None:
        with self.database.session() as session: session.execute(delete(CustomerMemory).where(CustomerMemory.id == memory_id))

    @staticmethod
    def _revision(session, record: CustomerMemory, change_type: str) -> None:
        session.add(CustomerMemoryRevision(memory_id=record.id, customer_id=record.customer_id, content=record.content, category=record.category, status=record.status, change_type=change_type))
