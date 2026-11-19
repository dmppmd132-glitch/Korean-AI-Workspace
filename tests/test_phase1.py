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
    terms = repo.search("달마", category="公司名稱")
    assert len(terms) == 1
    assert (terms[0].chinese_text, terms[0].is_forced) == ("達磨", True)
