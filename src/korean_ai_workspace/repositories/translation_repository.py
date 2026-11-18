from __future__ import annotations

from sqlalchemy import or_, select

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

    def search(self, keyword: str = "", limit: int = 100) -> list[TranslationHistory]:
        """Search original text and all saved translation variants locally."""
        statement = select(TranslationHistory).order_by(TranslationHistory.created_at.desc()).limit(limit)
        value = keyword.strip()
        if value:
            pattern = f"%{value}%"
            statement = statement.where(or_(
                TranslationHistory.source_text.like(pattern),
                TranslationHistory.best_translation.like(pattern),
                TranslationHistory.formal_translation.like(pattern),
                TranslationHistory.natural_translation.like(pattern),
                TranslationHistory.friendly_translation.like(pattern),
            ))
        with self.database.session() as session:
            return list(session.scalars(statement))
