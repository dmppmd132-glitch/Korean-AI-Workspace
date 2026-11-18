from __future__ import annotations

import json

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.models.entities import GlossaryTerm
from korean_ai_workspace.repositories.customer_repository import CustomerRepository
from korean_ai_workspace.repositories.glossary_repository import GlossaryRepository
from korean_ai_workspace.repositories.translation_repository import TranslationRepository
from korean_ai_workspace.services.translation.service import TranslationService


class InspectingProvider:
    def __init__(self): self.prompt = ""
    def translate(self, prompt: str) -> str:
        self.prompt = prompt
        return json.dumps({"source_language": "ko", "target_language": "zh-TW", "best": "最佳", "formal": "正式", "natural": "自然", "friendly": "親切"})


def setup_repositories(tmp_path):
    database = Database(f"sqlite:///{tmp_path / 'workspace.db'}"); database.create_all()
    return database, CustomerRepository(database), GlossaryRepository(database), TranslationRepository(database)


def test_customer_and_glossary_are_persisted_and_isolated(tmp_path):
    _db, customers, glossary, _history = setup_repositories(tmp_path)
    customer_a = customers.add(company_name="A 公司", korean_company_name="A사")
    customer_b = customers.add(company_name="B 公司")
    glossary.add(korean_text="납기", chinese_text="A 交期", customer_id=customer_a.id, category="物流")
    glossary.add(korean_text="납기", chinese_text="B 交期", customer_id=customer_b.id, category="物流")
    glossary.add(korean_text="견적", chinese_text="報價", customer_id=None, category="報價")
    a_terms = glossary.get_effective_terms(customer_a.id, "物流")
    b_terms = glossary.get_effective_terms(customer_b.id, "物流")
    assert [term.chinese_text for term in a_terms] == ["A 交期"]
    assert [term.chinese_text for term in b_terms] == ["B 交期"]
    assert all(term.customer_id != customer_b.id for term in a_terms)


def test_customer_glossary_is_added_to_translation_prompt(tmp_path):
    _db, customers, glossary, _history = setup_repositories(tmp_path)
    customer = customers.add(company_name="測試公司", communication_tone="正式")
    glossary.add(korean_text="납기", chinese_text="指定交期", is_forced=True, customer_id=customer.id, category="物流")
    provider = InspectingProvider()
    result = TranslationService(provider, glossary.get_effective_terms(customer.id, "物流"), "公司：測試公司").translate("납기", "ko")
    assert result.best == "最佳"
    assert "指定交期" in provider.prompt
    assert "公司：測試公司" in provider.prompt
    assert "不可使用任何客戶專屬資料" not in provider.prompt


def test_deleting_customer_unassigns_terms_without_deleting_them(tmp_path):
    _db, customers, glossary, _history = setup_repositories(tmp_path)
    customer = customers.add(company_name="待刪除公司")
    term = glossary.add(korean_text="테스트", chinese_text="測試", customer_id=customer.id)
    customers.delete(customer.id)
    remaining = glossary.search("測試")
    assert len(remaining) == 1
    assert remaining[0].id == term.id
    assert remaining[0].customer_id is None
