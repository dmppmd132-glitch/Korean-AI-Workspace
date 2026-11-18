from __future__ import annotations

import json

import pytest

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.repositories.translation_repository import TranslationRepository
from korean_ai_workspace.services.ai.config import AIProviderConfig
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


def test_empty_translation_is_rejected():
    with pytest.raises(ValueError):
        TranslationService(FakeProvider()).translate("   ")


def test_provider_config_requires_key_and_model():
    with pytest.raises(ValueError):
        AIProviderConfig("openai", "", "").validate()
