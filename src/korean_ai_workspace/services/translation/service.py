from __future__ import annotations

import json
from dataclasses import dataclass

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
    def __init__(self, provider: AIProvider):
        self.provider = provider

    def translate(self, source_text: str, source_language: str = "auto") -> TranslationResult:
        if not source_text.strip():
            raise ValueError("請先輸入要翻譯的內容")
        direction = "韓文→台灣繁體中文" if source_language == "ko" else "台灣繁體中文→自然韓文" if source_language == "zh-TW" else "自動辨識語言並翻譯"
        prompt = f"""請將以下內容進行{direction}的商務翻譯。
請保留價格、數量、日期、型號、交期及商業承諾，不得自行改寫數值或承諾。
請輸出嚴格 JSON，不要 Markdown code fence，欄位為：source_language、target_language、best、formal、natural、friendly。
若語境不足，請在翻譯中以「[需確認]」標示，不要自行猜測。
原文：
{source_text}"""
        raw = self.provider.translate(prompt)
        try:
            payload = json.loads(raw)
            return TranslationResult(
                source_language=payload["source_language"], target_language=payload["target_language"],
                best=payload["best"], formal=payload.get("formal", ""),
                natural=payload.get("natural", ""), friendly=payload.get("friendly", ""),
            )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise RuntimeError("AI 回傳格式錯誤：需要包含 source_language、target_language、best 的 JSON") from exc
