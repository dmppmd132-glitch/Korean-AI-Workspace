from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from korean_ai_workspace.models.entities import Base


class Database:
    def __init__(self, url: str):
        self.engine = create_engine(url, future=True)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    def create_all(self) -> None:
        Base.metadata.create_all(self.engine)
        self._migrate_existing_schema()

    def _migrate_existing_schema(self) -> None:
        """Apply additive SQLite migrations without deleting existing user data."""
        if self.engine.dialect.name != "sqlite":
            return
        inspector = inspect(self.engine)
        tables = set(inspector.get_table_names())
        if "translation_history" in tables:
            columns = {column["name"] for column in inspector.get_columns("translation_history")}
            if "customer_id" not in columns:
                with self.engine.begin() as connection:
                    connection.execute(text("ALTER TABLE translation_history ADD COLUMN customer_id INTEGER"))

    @contextmanager
    def session(self) -> Iterator[Session]:
        db = self.session_factory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
