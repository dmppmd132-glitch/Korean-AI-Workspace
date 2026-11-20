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
            ("대만달마", "台灣達磨", "대만달마", "公司名稱", "公司專用公司名稱：中文轉韓文固定使用 대만달마", False),
            ("달마", "達磨", "달마", "公司名稱", "公司專用公司名稱備援詞條", False),
            ("고명원", "高明元", "고명원", "人名", "姓名需依公司正式用法確認；預設保留韓文寫法", False),
            ("Tmp 저장 예외 처리", "Tmp 儲存例外處理", "Tmp 저장 예외 처리", "系統名稱", "系統功能名稱，禁止自行改寫", False),
            ("Tmp 저장 예외 미처리(표준 미준수)", "Tmp 儲存例外未處理（標準未遵守）", "Tmp 저장 예외 미처리(표준 미준수)", "系統名稱", "系統 Alarm 名稱，禁止自行改寫", False),
            ("안에 스트립(BF7170843) 혼입이 존재 합니다", "存在內含 Strip(BF7170843) 混入", "안에 스트립(BF7170843) 혼입이 존재 합니다", "系統名稱", "完整 Alarm 原文，禁止翻譯或改寫", True),
            ("Alarm", "Alarm", "Alarm", "系統名稱", "系統警報固定保留英文", True),
            ("46L LASER 공정", "46L LASER 製程", "46L LASER 공정", "品質報告", "案例一固定製程名稱", False),
            ("자동 백업 기능", "自動備份功能", "자동 백업 기능", "系統名稱", "案例一固定系統功能", False),
            ("설정 오류", "設定錯誤", "설정 오류", "品質報告", "品質報告固定原因", False),
            ("이전 데이터 1건", "舊資料一筆", "이전 데이터 1건", "品質報告", "保留資料數量", False),
            ("중복 업로드", "重複上傳", "중복 업로드", "系統操作", "系統操作固定術語", False),
            ("Gathering 처리", "Gathering 處理", "Gathering 처리", "系統操作", "固定保留 Gathering", False),
            ("시스템 백업 설정", "系統備份設定", "시스템 백업 설정", "系統名稱", "案例一改善對策術語", False),
            ("설정 파라미터", "設定參數", "설정 파라미터", "系統操作", "案例一改善對策術語", False),
            ("개선 대책 적용", "改善對策套用", "개선 대책 적용", "品質報告", "改善對策固定術語", False),
            ("데이터 재검증", "數據重新驗證", "데이터 재검증", "品質報告", "品質報告結尾固定術語", False),
            ("46M VRS 공정", "46M VRS 製程", "46M VRS 공정", "品質報告", "案例二固定製程名稱", False),
            ("Gathering 완료", "Gathering 完成", "Gathering 완료", "系統操作", "案例二流程術語", False),
            ("공정 완료 처리", "完工處理", "공정 완료 처리", "系統操作", "完工操作固定術語", False),
            ("예기치 않은 Shutdown", "非預期 Shutdown", "예기치 않은 Shutdown", "系統名稱", "程式異常固定術語", False),
            ("VRS 검사 프로그램", "VRS 檢查程式", "VRS 검사 프로그램", "系統名稱", "案例二固定程式名稱", False),
            ("일부 데이터 오류", "部分資料錯誤", "일부 데이터 오류", "品質報告", "案例二異常原因術語", False),
            ("즉시 검사를 중단", "立即停止檢查", "즉시 검사를 중단", "品質報告", "改善對策固定動作", False),
            ("관리자에게 보고", "通報管理人員", "관리자에게 보고", "品質報告", "改善對策固定動作", False),
            ("Gathering 처리를 재진행", "重新 Gathering 處理", "Gathering 처리를 재진행", "品質報告", "案例二結尾固定術語", False),
            ("후속 프로세스", "後續流程", "후속 프로세스", "品質報告", "品質報告結尾固定術語", False),
        )
        with self.database.session() as session:
            for korean_text, chinese_text, specified_korean, category, notes, is_forbidden in defaults:
                exists = session.scalar(select(GlossaryTerm.id).where(and_(GlossaryTerm.korean_text == korean_text, GlossaryTerm.customer_id.is_(None))))
                if exists is None:
                    session.add(GlossaryTerm(korean_text=korean_text, chinese_text=chinese_text, specified_korean=specified_korean, category=category, is_forced=True, is_forbidden=is_forbidden, notes=notes))

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
