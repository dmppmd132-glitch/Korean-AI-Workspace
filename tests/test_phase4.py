from __future__ import annotations

import json
from pathlib import Path

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.repositories.attachment_repository import AttachmentRepository
from korean_ai_workspace.repositories.customer_repository import CustomerRepository
from korean_ai_workspace.repositories.email_repository import EmailRepository
from korean_ai_workspace.repositories.glossary_repository import GlossaryRepository
from korean_ai_workspace.services.email_service import EmailAnalysis, EmailService
from korean_ai_workspace.models.entities import EmailAttachmentLink


class EmailFakeProvider:
    def __init__(self): self.prompts: list[str] = []
    def translate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if "產生三種韓文回信草稿" in prompt:
            return json.dumps({"formal": "正式韓文草稿", "natural": "自然韓文草稿", "friendly": "親切韓文草稿"}, ensure_ascii=False)
        return json.dumps({"translated": "完整翻譯", "summary": "客戶摘要", "tone": "正式", "requirements": "需要報價", "important_items": "交期：[需確認]"}, ensure_ascii=False)


def setup(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'workspace.db'}"); db.create_all()
    return db, CustomerRepository(db), GlossaryRepository(db), EmailRepository(db), AttachmentRepository(db, tmp_path / "attachments")


def test_email_analysis_and_reply_drafts_are_structured(tmp_path):
    _db, customers, glossary, emails, _attachments = setup(tmp_path)
    customer = customers.add(company_name="郵件客戶", communication_tone="正式")
    provider = EmailFakeProvider(); service = EmailService(provider, glossary.get_effective_terms(customer.id), "公司：郵件客戶")
    analysis = service.analyze("납기와 견적을 알려 주세요")
    assert analysis.translated == "完整翻譯"
    drafts = service.draft_reply("납기와 견적을 알려 주세요", analysis, "我們會在明天提供報價")
    assert drafts.natural == "自然韓文草稿"
    record = emails.add(customer_id=customer.id, subject="報價詢問", original_content="납기와 견적을 알려 주세요", translated_content=analysis.translated, analysis_json=json.dumps(analysis.__dict__, ensure_ascii=False), status="分析完成")
    emails.update(record.id, draft_natural=drafts.natural, status="草稿完成")
    saved = emails.get(record.id)
    assert saved is not None and saved.status == "草稿完成" and saved.customer_id == customer.id
    assert all("郵件客戶" in prompt or "납기" in prompt for prompt in provider.prompts)


def test_attachment_sha256_dedup_and_relation_delete(tmp_path):
    _db, customers, _glossary, emails, attachments = setup(tmp_path)
    customer = customers.add(company_name="附件客戶")
    email = emails.add(customer_id=customer.id, subject="附件", original_content="內容")
    source = tmp_path / "quote.txt"; source.write_text("same-content", encoding="utf-8")
    first, duplicate_first = attachments.add_file(source, email.id)
    second, duplicate_second = attachments.add_file(source, email.id)
    assert first.id == second.id and duplicate_first is False and duplicate_second is True
    assert len(attachments.list_for_email(email.id)) == 1
    attachments.remove_link(email.id, first.id)
    attachments.delete_file(first.id)
    assert attachments.get(first.id) is None
    assert not Path(first.stored_path).exists()


def test_attachment_is_not_deleted_while_still_linked(tmp_path):
    _db, _customers, _glossary, emails, attachments = setup(tmp_path)
    email = emails.add(subject="附件", original_content="內容")
    source = tmp_path / "file.txt"; source.write_text("content", encoding="utf-8")
    record, _ = attachments.add_file(source, email.id)
    try:
        attachments.delete_file(record.id)
    except ValueError as exc:
        assert "仍被郵件使用" in str(exc)
    else:
        raise AssertionError("linked attachment must not be physically deleted")


def test_deleting_email_cascades_link_but_keeps_shared_attachment(tmp_path):
    db, _customers, _glossary, emails, attachments = setup(tmp_path)
    first_email = emails.add(subject="第一封", original_content="內容")
    second_email = emails.add(subject="第二封", original_content="內容")
    source = tmp_path / "shared.txt"; source.write_text("shared", encoding="utf-8")
    record, _ = attachments.add_file(source, first_email.id)
    attachments.add_file(source, second_email.id)
    with db.session() as session:
        session.delete(session.get(type(first_email), first_email.id))
    assert len(attachments.list_for_email(second_email.id)) == 1
    with db.session() as session:
        assert session.query(EmailAttachmentLink).filter_by(email_id=first_email.id).count() == 0
    assert attachments.get(record.id) is not None
