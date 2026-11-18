from __future__ import annotations

from sqlalchemy import select

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.models.entities import TranslationHistory


class TranslationRepository:
    def __init__(self, database: Database):
        self.database = database

    def add(self, **values) -> TranslationHistory:
        record = TranslationHistory(**values)
        with self.database.session() as session:
            session.add(record)
            session.flush()
            session.refresh(record)
        return record

    def list_recent(self, limit: int = 50) -> list[TranslationHistory]:
        with self.database.session() as session:
            return list(session.scalars(
                select(TranslationHistory)
                .order_by(TranslationHistory.created_at.desc())
                .limit(limit)
            ))
