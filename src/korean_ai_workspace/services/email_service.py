from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Sequence

from korean_ai_workspace.models.entities import GlossaryTerm
from korean_ai_workspace.services.ai.providers import AIProvider


@dataclass(frozen=True)
class EmailAnalysis:
    translated: str
    summary: str
    tone: str
    requirements: str
    important_items: str


@dataclass(frozen=True)
class ReplyDrafts:
    formal: str
    natural: str
    friendly: str


class EmailService:
    def __init__(self, provider: AIProvider, glossary_terms: Sequence[GlossaryTerm] | None = None, customer_context: str = ""):
        self.provider = provider; self.glossary_terms = list(glossary_terms or []); self.customer_context = customer_context.strip()

    def _terms(self) -> str:
        return "\n".join(f"- {term.korean_text} → {term.chinese_text or term.specified_korean or '(依語境)'}" for term in self.glossary_terms) or "（無可用詞條）"

    def analyze(self, original: str) -> EmailAnalysis:
        if not original.strip(): raise ValueError("請先貼上韓文郵件內容")
        prompt = f"""你是商務郵件分析助手。請分析以下韓文郵件，輸出嚴格 JSON，不要 Markdown code fence。
欄位：translated（完整繁體中文翻譯）、summary（摘要）、tone（對方語氣）、requirements（對方需求清單）、important_items（重要事項、日期、數量、價格、交期與承諾）。
客戶情境（只能使用此客戶）：{self.customer_context or '未選取客戶'}
可用詞庫：{self._terms()}
不得自行改動價格、數量、日期、型號、交期及商業承諾；無法確定請標示[需確認]。
韓文郵件：\n{original}"""
        data = self._json(prompt)
        return EmailAnalysis(data["translated"], data["summary"], data["tone"], data["requirements"], data["important_items"])

    def draft_reply(self, original: str, analysis: EmailAnalysis, reply_intent: str) -> ReplyDrafts:
        if not reply_intent.strip(): raise ValueError("請先輸入中文回覆意思")
        prompt = f"""請根據韓文商務郵件與分析內容，產生三種韓文回信草稿，輸出嚴格 JSON，不要 Markdown code fence。
欄位：formal、natural、friendly。全部只能標示為草稿，不可宣稱已寄出。
客戶情境：{self.customer_context or '未選取客戶'}
原郵件：{original}
分析：{analysis.summary}\n{analysis.important_items}
使用者想回覆的中文意思：{reply_intent}
保留原郵件中的價格、數量、日期、型號、交期及承諾；不確定內容標示[需確認]。"""
        data = self._json(prompt); return ReplyDrafts(data["formal"], data["natural"], data["friendly"])

    def _json(self, prompt: str) -> dict:
        try: return json.loads(self.provider.translate(prompt))
        except (json.JSONDecodeError, KeyError, TypeError) as exc: raise RuntimeError("AI 回傳格式錯誤，郵件功能需要有效 JSON") from exc
