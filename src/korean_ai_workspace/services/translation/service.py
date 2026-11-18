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
    def __init__(self, provider: AIProvider, glossary_terms: Sequence[GlossaryTerm] | None = None, customer_context: str = ""):
        self.provider = provider
        self.glossary_terms = list(glossary_terms or [])
        self.customer_context = customer_context.strip()

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

    def translate(self, source_text: str, source_language: str = "auto") -> TranslationResult:
        if not source_text.strip():
            raise ValueError("請先輸入要翻譯的內容")
        direction = "韓文→台灣繁體中文" if source_language == "ko" else "台灣繁體中文→自然韓文" if source_language == "zh-TW" else "自動辨識語言並翻譯"
        context = f"目前客戶情境（只可使用此客戶資料）：\n{self.customer_context}\n" if self.customer_context else "目前未選取客戶，不可使用任何客戶專屬資料。\n"
        prompt = f"""請將以下內容進行{direction}的商務翻譯。
{context}請保留價格、數量、日期、型號、交期及商業承諾，不得自行改寫數值或承諾。
詞庫優先順序為：客戶專屬 > 分類 > 全域 > AI 自由翻譯。只有在語境相符時套用詞條，不可盲目替換。
本次可用詞庫：
{self._glossary_instructions()}
請輸出嚴格 JSON，不要 Markdown code fence，欄位為：source_language、target_language、best、formal、natural、friendly。
若語境不足，請在翻譯中以「[需確認]」標示，不要自行猜測。
原文：
{source_text}"""
        raw = self.provider.translate(prompt)
        try:
            payload = json.loads(raw)
            return TranslationResult(source_language=payload["source_language"], target_language=payload["target_language"], best=payload["best"], formal=payload.get("formal", ""), natural=payload.get("natural", ""), friendly=payload.get("friendly", ""))
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise RuntimeError("AI 回傳格式錯誤：需要包含 source_language、target_language、best 的 JSON") from exc
