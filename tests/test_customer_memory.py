from __future__ import annotations

import json

import pytest

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.repositories.customer_repository import CustomerRepository
from korean_ai_workspace.repositories.memory_repository import CustomerMemoryRepository
from korean_ai_workspace.services.memory_service import CustomerMemoryService


class FakeProvider:
    def __init__(self, payload): self.payload = payload; self.prompt = ""
    def translate(self, prompt: str) -> str: self.prompt = prompt; return self.payload


def setup(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'workspace.db'}"); db.create_all()
    return db, CustomerRepository(db), CustomerMemoryRepository(db)


def test_memory_isolated_and_unconfirmed_not_in_effective_context(tmp_path):
    _db, customers, memories = setup(tmp_path)
    a = customers.add(company_name="A"); b = customers.add(company_name="B")
    suggestion = memories.add_suggestion(a.id, "偏好正式語氣", "溝通習慣")
    assert memories.search(a.id)[0].status == "待確認"
    assert memories.search(b.id) == []
    memories.confirm(suggestion.id)
    assert [item.content for item in memories.search(a.id, status="已確認")] == ["偏好正式語氣"]
    assert memories.search(b.id, status="已確認") == []


def test_memory_revisions_capture_confirmation_and_update(tmp_path):
    _db, customers, memories = setup(tmp_path)
    customer = customers.add(company_name="客戶")
    item = memories.add_suggestion(customer.id, "原始內容")
    memories.confirm(item.id)
    memories.update(item.id, "更新內容", "合作歷史")
    revisions = memories.revisions(item.id)
    assert [revision.change_type for revision in revisions] == ["修改", "確認", "新增建議"]
    assert revisions[0].content == "更新內容"


def test_ai_suggestion_only_returns_pending_candidates_and_never_persists(tmp_path):
    _db, customers, memories = setup(tmp_path)
    customer = customers.add(company_name="客戶")
    provider = FakeProvider(json.dumps([{"category": "溝通習慣", "content": "偏好簡短回覆"}]))
    service = CustomerMemoryService(provider, "公司：客戶")
    suggestions = service.suggest("請以簡短內容回覆。")
    assert suggestions[0].content == "偏好簡短回覆"
    assert memories.search(customer.id) == []
    assert "只能提出" in provider.prompt


def test_invalid_ai_suggestion_does_not_write_data(tmp_path):
    _db, _customers, _memories = setup(tmp_path)
    with pytest.raises(RuntimeError, match="未寫入"):
        CustomerMemoryService(FakeProvider("不是 JSON")).suggest("郵件")
