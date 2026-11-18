from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Sequence

from korean_ai_workspace.models.entities import GlossaryTerm
from korean_ai_workspace.services.ai.providers import AIProvider
from korean_ai_workspace.repositories.memory_repository import CustomerMemoryRepository


@dataclass(frozen=True)
class MemorySuggestion:
    category: str
    content: str


class CustomerMemoryService:
    def __init__(self, provider: AIProvider, customer_context: str = "", glossary_terms: Sequence[GlossaryTerm] | None = None):
        self.provider = provider; self.customer_context = customer_context.strip(); self.glossary_terms = list(glossary_terms or [])

    def suggest(self, email_text: str) -> list[MemorySuggestion]:
        if not email_text.strip(): raise ValueError("郵件內容不可為空白")
        prompt = f"""你是客戶記憶建議助手。請從以下商務郵件提出可能值得保存的客戶記憶，輸出嚴格 JSON 陣列，不要 Markdown。
每個項目只有 category 與 content；category 必須是：{', '.join(CustomerMemoryRepository.CATEGORIES)}。
只能提出可由郵件明確支持的事實；價格、數量、日期、交期與商業承諾不確定時不要猜測，必要時加上[需確認]。
這些只是待使用者確認的建議，不能表示已確認。
客戶情境：{self.customer_context or '未指定'}
郵件：{email_text}"""
        try:
            payload = json.loads(self.provider.translate(prompt))
            if not isinstance(payload, list): raise ValueError("不是陣列")
            return [MemorySuggestion(str(item.get("category", "其他")), str(item.get("content", "")).strip()) for item in payload if isinstance(item, dict) and str(item.get("content", "")).strip()]
        except (json.JSONDecodeError, TypeError, ValueError, AttributeError) as exc:
            raise RuntimeError("AI 回傳的客戶記憶建議格式錯誤，未寫入任何正式記憶") from exc
