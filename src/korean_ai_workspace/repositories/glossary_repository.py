from __future__ import annotations

from sqlalchemy import and_, or_, select

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.models.entities import GlossaryTerm


class GlossaryRepository:
    def __init__(self, database: Database):
        self.database = database

    def add(self, **values) -> GlossaryTerm:
        if not values.get("korean_text", "").strip():
            raise ValueError("韓文原文不可為空白")
        record = GlossaryTerm(**values)
        with self.database.session() as session:
            session.add(record); session.flush(); session.refresh(record)
        return record

    def ensure_default_terms(self) -> None:
        """Create safe, global application terms once without touching user data."""
        with self.database.session() as session:
            exists = session.scalar(select(GlossaryTerm.id).where(and_(GlossaryTerm.korean_text == "달마", GlossaryTerm.customer_id.is_(None))))
            if exists is None:
                session.add(GlossaryTerm(korean_text="달마", chinese_text="達磨", category="公司名稱", is_forced=True, notes="系統固定公司名稱翻譯"))

    def update(self, term_id: int, **values) -> GlossaryTerm:
        with self.database.session() as session:
            record = session.get(GlossaryTerm, term_id)
            if record is None:
                raise ValueError("找不到指定詞條")
            for key, value in values.items():
                if hasattr(record, key): setattr(record, key, value)
            if not record.korean_text.strip():
                raise ValueError("韓文原文不可為空白")
            session.flush(); session.refresh(record)
            return record

    def search(self, keyword: str = "", customer_id: int | None = None, category: str = "", limit: int = 300) -> list[GlossaryTerm]:
        statement = select(GlossaryTerm).order_by(GlossaryTerm.korean_text.asc()).limit(limit)
        value = keyword.strip()
        if value:
            pattern = f"%{value}%"
            statement = statement.where(or_(GlossaryTerm.korean_text.like(pattern), GlossaryTerm.chinese_text.like(pattern), GlossaryTerm.specified_korean.like(pattern), GlossaryTerm.notes.like(pattern)))
        if customer_id is not None:
            statement = statement.where(GlossaryTerm.customer_id == customer_id)
        elif customer_id == 0:
            statement = statement.where(GlossaryTerm.customer_id.is_(None))
        if category.strip():
            statement = statement.where(GlossaryTerm.category == category.strip())
        with self.database.session() as session:
            return list(session.scalars(statement))

    def get_effective_terms(self, customer_id: int | None = None, category: str = "") -> list[GlossaryTerm]:
        """Return only global/category terms and the selected customer's terms."""
        statement = select(GlossaryTerm).order_by(GlossaryTerm.customer_id.asc(), GlossaryTerm.category.asc(), GlossaryTerm.korean_text.asc())
        with self.database.session() as session:
            terms = list(session.scalars(statement))
        selected = []
        for term in terms:
            is_global = term.customer_id is None and (not category.strip() or term.category in {category, "其他"})
            is_customer = customer_id is not None and term.customer_id == customer_id
            if is_global or is_customer:
                selected.append(term)
        # Specific customer terms override global/category terms with the same Korean source.
        priority: dict[str, GlossaryTerm] = {}
        for term in selected:
            if term.korean_text not in priority or (customer_id is not None and term.customer_id == customer_id):
                priority[term.korean_text] = term
        return list(priority.values())

    def delete(self, term_id: int) -> None:
        with self.database.session() as session:
            record = session.get(GlossaryTerm, term_id)
            if record is not None:
                session.delete(record)
