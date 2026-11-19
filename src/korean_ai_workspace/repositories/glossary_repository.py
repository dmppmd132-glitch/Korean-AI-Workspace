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
        defaults = (
            ("대만달마", "台灣達磨", "대만달마", "公司名稱", "公司專用公司名稱：中文轉韓文固定使用 대만달마"),
            ("달마", "達磨", "달마", "公司名稱", "公司專用公司名稱備援詞條"),
            ("고명원", "高明元", "고명원", "人名", "姓名需依公司正式用法確認；預設保留韓文寫法"),
            ("Tmp 저장 예외 처리", "Tmp 儲存例外處理", "Tmp 저장 예외 처리", "系統名稱", "系統功能名稱，禁止自行改寫"),
            ("Tmp 저장 예외 미처리(표준 미준수)", "Tmp 儲存例外未處理（標準未遵守）", "Tmp 저장 예외 미처리(표준 미준수)", "系統名稱", "系統 Alarm 名稱，禁止自行改寫"),
            ("LOT 번호", "LOT 編號", "LOT 번호", "品質報告", "製造與品質報告固定術語"),
            ("화면 응답 지연", "畫面延遲", "화면 응답 지연", "品質報告", "正式品質報告用語"),
            ("입력 형식 초과", "格式溢位", "입력 형식 초과", "品質報告", "輸入欄位超出格式或位數限制"),
            ("시스템 버퍼", "系統緩衝區", "시스템 버퍼", "系統名稱", "系統技術術語"),
            ("키보드 입력 신호", "鍵盤輸入訊號", "키보드 입력 신호", "系統名稱", "系統技術術語"),
            ("후속 프로세스", "後續流程", "후속 프로세스", "品質報告", "品質報告結尾固定術語"),
        )
        with self.database.session() as session:
            for korean_text, chinese_text, specified_korean, category, notes in defaults:
                exists = session.scalar(select(GlossaryTerm.id).where(and_(GlossaryTerm.korean_text == korean_text, GlossaryTerm.customer_id.is_(None))))
                if exists is None:
                    session.add(GlossaryTerm(korean_text=korean_text, chinese_text=chinese_text, specified_korean=specified_korean, category=category, is_forced=True, notes=notes))

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
