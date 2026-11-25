from __future__ import annotations

import json

import pytest

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.models.entities import GlossaryTerm
from korean_ai_workspace.repositories.glossary_repository import GlossaryRepository
from korean_ai_workspace.repositories.translation_repository import TranslationRepository
from korean_ai_workspace.services.ai.config import AIProviderConfig, DEFAULT_API_TIMEOUT_SECONDS, FIXED_ENDPOINT, FIXED_MODEL, FIXED_PROVIDER
from korean_ai_workspace.services.translation.service import TranslationService


class FakeProvider:
    def translate(self, prompt: str) -> str:
        return json.dumps({"source_language": "ko", "target_language": "zh-TW", "best": "您好，這是翻譯結果。", "formal": "正式翻譯", "natural": "自然翻譯", "friendly": "親切翻譯"})


def test_database_creates_and_persists_history(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'workspace.db'}")
    db.create_all()
    repo = TranslationRepository(db)
    item = repo.add(source_text="안녕하세요", source_language="ko", target_language="zh-TW", best_translation="您好", provider="test", model="fake")
    assert item.id == 1
    assert repo.list_recent()[0].source_text == "안녕하세요"


def test_translation_service_returns_structured_result():
    result = TranslationService(FakeProvider()).translate("안녕하세요", "ko")
    assert result.best == "您好，這是翻譯結果。"
    assert result.target_language == "zh-TW"


def test_translation_service_fast_mode_only_requests_best_variant():
    result = TranslationService(FakeProvider(), fast_mode=True).translate("안녕하세요", "ko")
    assert result.best == "您好，這是翻譯結果。"
    assert (result.formal, result.natural, result.friendly) == ("", "", "")


def test_forced_glossary_term_is_applied_to_ai_result():
    class Provider:
        def translate(self, _prompt: str) -> str:
            return json.dumps({"source_language": "ko", "target_language": "zh-TW", "best": "달마 公司"})

    term = GlossaryTerm(korean_text="달마", chinese_text="達磨", category="公司名稱", is_forced=True)
    assert TranslationService(Provider(), [term], fast_mode=True).translate("달마", "ko").best == "達磨 公司"


def test_quality_report_prompt_preserves_fixed_structure_and_terms():
    prompts = []

    class Provider:
        def translate(self, prompt: str) -> str:
            prompts.append(prompt)
            return json.dumps({"source_language": "zh-TW", "target_language": "ko", "best": "안녕하십니까. 대만달마입니다."})

    terms = [GlossaryTerm(korean_text="대만달마", chinese_text="台灣達磨", specified_korean="대만달마", category="公司名稱", is_forced=True)]
    TranslationService(Provider(), terms, fast_mode=True, quality_report_mode=True).translate("台灣達磨的品質異常報告", "zh-TW")
    assert "品質異常報告固定格式" in prompts[0]
    assert "- 발생 원인:" in prompts[0]
    assert "- 개선 대책:" in prompts[0]
    assert "안녕하십니까." in prompts[0]
    assert "감사합니다." in prompts[0]
    assert "不可自行改成「已完成」" in prompts[0]
    assert "대만달마" in prompts[0]


def test_empty_translation_is_rejected():
    with pytest.raises(ValueError):
        TranslationService(FakeProvider()).translate("   ")


def test_provider_config_requires_key_and_model():
    with pytest.raises(ValueError):
        AIProviderConfig("openai", "", "").validate()


def test_provider_config_uses_extended_api_timeout():
    assert AIProviderConfig("openai", "key", "model").timeout_seconds == DEFAULT_API_TIMEOUT_SECONDS
    assert DEFAULT_API_TIMEOUT_SECONDS >= 120


def test_fixed_gemini_configuration_and_default_company_term(tmp_path):
    assert (FIXED_PROVIDER, FIXED_MODEL, FIXED_ENDPOINT) == ("gemini", "gemini-4-hydrogen", "https://generativelanguage.googleapis.com/v1beta/openai")
    db = Database(f"sqlite:///{tmp_path / 'workspace.db'}"); db.create_all(); repo = GlossaryRepository(db)
    repo.ensure_default_terms(); repo.ensure_default_terms()
    terms = repo.search("")
    assert {(term.korean_text, term.chinese_text) for term in terms} >= {("달마", "達磨"), ("대만달마", "台灣達磨"), ("안에 스트립(BF7170843) 혼입이 존재 합니다", "存在內含 Strip(BF7170843) 混入")}
    assert all(term.is_forced for term in terms)
    alarm = next(term for term in terms if term.korean_text.startswith("안에 스트립"))
    assert alarm.is_forbidden is True


def test_sorter_genesem_and_samsung_customer_glossary_terms_are_seeded_once(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'workspace.db'}"); db.create_all(); repo = GlossaryRepository(db)
    repo.ensure_default_terms(); repo.ensure_default_terms()
    terms = repo.search("")
    pairs = {(term.korean_text, term.chinese_text) for term in terms}
    assert {("Genesem Inc.", "Genesem Inc."), ("Sorter", "Sorter"), ("main vacuum pressure error", "主真空壓力錯誤"), ("TeamViewer", "TeamViewer")} <= pairs
    assert {("불량률", "不良率"), ("검사 조건 최적화", "檢驗條件最佳化"), ("물량 반출 제약", "產品出貨限制"), ("밀착 관리", "密切管理／加強管控")} <= pairs
    assert len(terms) == len({term.korean_text for term in terms})
    assert next(term for term in terms if term.korean_text == "Vacuum Air Pressure").is_forbidden is True
    assert next(term for term in terms if term.korean_text == "Overkill").is_forbidden is True
