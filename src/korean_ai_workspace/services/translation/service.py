from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Sequence

from korean_ai_workspace.models.entities import GlossaryTerm
from korean_ai_workspace.services.ai.providers import AIProvider


@dataclass(frozen=True)
class TranslationResult:
    source_language: str
    target_language: str
    best: str
    formal: str
    natural: str
    friendly: str


class TranslationService:
    def __init__(self, provider: AIProvider, glossary_terms: Sequence[GlossaryTerm] | None = None, customer_context: str = "", fast_mode: bool = False, quality_report_mode: bool = False):
        self.provider = provider
        self.glossary_terms = list(glossary_terms or [])
        self.customer_context = customer_context.strip()
        self.fast_mode = fast_mode
        self.quality_report_mode = quality_report_mode

    def _glossary_instructions(self) -> str:
        if not self.glossary_terms:
            return "目前沒有符合範圍的詞庫詞條，請依一般語境翻譯。"
        lines = []
        for term in self.glossary_terms:
            scope = "客戶專屬" if term.customer_id is not None else "全域／分類"
            rule = "禁止翻譯，保留原文" if term.is_forbidden else f"指定繁中：{term.chinese_text or '(未指定)'}；指定韓文：{term.specified_korean or '(未指定)'}"
            if term.is_forced: rule += "；強制套用（僅在語境相符時）"
            lines.append(f"- [{scope}] {term.korean_text}：{rule}")
        return "\n".join(lines)

    def _apply_forced_terms(self, text: str, source_language: str) -> str:
        if source_language == "zh-TW":
            return text
        for term in self.glossary_terms:
            if term.is_forced and term.chinese_text and term.korean_text:
                text = text.replace(term.korean_text, term.chinese_text)
        return text

    def translate(self, source_text: str, source_language: str = "auto") -> TranslationResult:
        if not source_text.strip():
            raise ValueError("請先輸入要翻譯的內容")
        direction = "韓文→台灣繁體中文" if source_language == "ko" else "台灣繁體中文→自然韓文" if source_language == "zh-TW" else "自動辨識語言並翻譯"
        context = f"目前客戶情境（只可使用此客戶資料）：\n{self.customer_context}\n" if self.customer_context else "目前未選取客戶，不可使用任何客戶專屬資料。\n"
        output_instruction = (
            "請輸出嚴格 JSON，不要 Markdown code fence，欄位為：source_language、target_language、best。"
            if self.fast_mode else
            "請輸出嚴格 JSON，不要 Markdown code fence，欄位為：source_language、target_language、best、formal、natural、friendly。"
        )
        format_instruction = """
本次使用「品質異常報告固定格式」：中文→韓文時請維持正式、客觀、可寄給原廠的品質報告語氣與段落結構。
請使用一致的正式敬體（합니다／하였습니다／드립니다），不可混用筆記式「함」或口語；若原文是「將進行／預計」，必須保留預定語氣，不可自行改成「已完成」，反之亦然。
請依序保留：正式問候「안녕하십니까.」、寄件人、異常現象／警報、異常畫面說明、發生原因、改善對策、重新處理／資料驗證結果、結語「감사합니다.」。若原文沒有問候或寄件人，不要自行捏造姓名。
條列標題固定使用「- 발생 원인:」與「- 개선 대책:」，冒號不可省略；不可刪除技術原因、完整 Alarm 原文、錯誤代碼、LOT、Tmp、數字或後續流程結果，不可新增原文沒有的責任承諾。
公司名稱、人名、系統功能名稱、Alarm 名稱、製程名稱與 Gathering 必須優先採用詞庫指定韓文；設定詞條標記為禁止翻譯或完整 Alarm 時，必須逐字保留（包含空格、括號、代碼與英文）。無法確認的內部術語保留原文並以 [需確認] 標示，不要自行臆測。
""" if self.quality_report_mode and source_language in {"zh-TW", "auto"} else ""
        prompt = f"""請將以下內容進行{direction}的商務翻譯。
{context}請保留價格、數量、日期、型號、交期及商業承諾，不得自行改寫數值或承諾。
{format_instruction}
詞庫優先順序為：客戶專屬 > 分類 > 全域 > AI 自由翻譯。只有在語境相符時套用詞條，不可盲目替換。
本次可用詞庫：
{self._glossary_instructions()}
{output_instruction}
若語境不足，請在翻譯中以「[需確認]」標示，不要自行猜測。
原文：
{source_text}"""
        raw = self.provider.translate(prompt)
        try:
            payload = json.loads(raw)
            return TranslationResult(source_language=payload["source_language"], target_language=payload["target_language"], best=self._apply_forced_terms(payload["best"], source_language), formal="" if self.fast_mode else self._apply_forced_terms(payload.get("formal", ""), source_language), natural="" if self.fast_mode else self._apply_forced_terms(payload.get("natural", ""), source_language), friendly="" if self.fast_mode else self._apply_forced_terms(payload.get("friendly", ""), source_language))
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise RuntimeError("AI 回傳格式錯誤：需要包含 source_language、target_language、best 的 JSON") from exc
