from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TranslationHistory(Base):
    __tablename__ = "translation_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_language: Mapped[str] = mapped_column(String(16), nullable=False)
    target_language: Mapped[str] = mapped_column(String(16), nullable=False)
    best_translation: Mapped[str] = mapped_column(Text, nullable=False)
    formal_translation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    natural_translation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    friendly_translation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
