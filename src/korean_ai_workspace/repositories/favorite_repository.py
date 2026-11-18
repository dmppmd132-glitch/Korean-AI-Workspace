from __future__ import annotations

from sqlalchemy import delete, or_, select

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.models.entities import TranslationFavorite, TranslationHistory


class FavoriteRepository:
    VARIANTS = {"best": "最佳翻譯", "formal": "正式版本", "natural": "自然版本", "friendly": "親切版本"}

    def __init__(self, database: Database): self.database = database

    def add_from_history(self, history: TranslationHistory, variant_type: str) -> TranslationFavorite:
        if history is None: raise ValueError("找不到翻譯歷史")
        if variant_type not in self.VARIANTS: raise ValueError("不支援的翻譯版本")
        text = getattr(history, f"{variant_type}_translation")
        return self.add_snapshot(history.source_text, history.source_language, history.target_language, text, variant_type, history.provider, history.model, history.customer_id, history.id)

    def add_snapshot(self, source_text: str, source_language: str, target_language: str, translation_text: str, variant_type: str, provider: str = "", model: str = "", customer_id: int | None = None, translation_history_id: int | None = None) -> TranslationFavorite:
        if not source_text.strip() or not translation_text.strip(): raise ValueError("原文與翻譯內容不可為空白")
        if variant_type not in self.VARIANTS: raise ValueError("不支援的翻譯版本")
        with self.database.session() as session:
            if translation_history_id is not None:
                existing = session.scalar(select(TranslationFavorite).where(TranslationFavorite.translation_history_id == translation_history_id, TranslationFavorite.variant_type == variant_type))
                if existing is not None: return existing
            record = TranslationFavorite(translation_history_id=translation_history_id, source_text=source_text, source_language=source_language, target_language=target_language, translation_text=translation_text, variant_type=variant_type, provider=provider, model=model, customer_id=customer_id)
            session.add(record); session.flush(); session.refresh(record); return record

    def list(self, keyword: str = "", source_language: str = "", variant_type: str = "", customer_id: int | None = None, limit: int = 500) -> list[TranslationFavorite]:
        statement = select(TranslationFavorite).order_by(TranslationFavorite.created_at.desc()).limit(limit)
        if source_language: statement = statement.where(TranslationFavorite.source_language == source_language)
        if variant_type: statement = statement.where(TranslationFavorite.variant_type == variant_type)
        if customer_id is not None: statement = statement.where(TranslationFavorite.customer_id == customer_id)
        value = keyword.strip()
        if value:
            pattern = f"%{value}%"
            statement = statement.where(or_(TranslationFavorite.source_text.like(pattern), TranslationFavorite.translation_text.like(pattern)))
        with self.database.session() as session: return list(session.scalars(statement))

    def get(self, favorite_id: int) -> TranslationFavorite | None:
        with self.database.session() as session: return session.get(TranslationFavorite, favorite_id)

    def delete(self, favorite_id: int) -> None:
        with self.database.session() as session: session.execute(delete(TranslationFavorite).where(TranslationFavorite.id == favorite_id))
