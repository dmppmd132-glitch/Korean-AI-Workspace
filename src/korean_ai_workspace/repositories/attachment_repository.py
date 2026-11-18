from __future__ import annotations

import hashlib
import mimetypes
import shutil
from pathlib import Path

from sqlalchemy import delete, select

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.models.entities import Attachment, EmailAttachmentLink


MAX_ATTACHMENT_BYTES = 100 * 1024 * 1024


class AttachmentRepository:
    def __init__(self, database: Database, attachment_dir: Path):
        self.database = database; self.attachment_dir = attachment_dir; self.attachment_dir.mkdir(parents=True, exist_ok=True)

    def add_file(self, source: str | Path, email_id: int) -> tuple[Attachment, bool]:
        source_path = Path(source)
        if not source_path.is_file(): raise ValueError("附件檔案不存在")
        size = source_path.stat().st_size
        if size > MAX_ATTACHMENT_BYTES: raise ValueError("單一附件不可超過 100 MB")
        digest = hashlib.sha256();
        with source_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""): digest.update(chunk)
        sha = digest.hexdigest(); duplicate = False; copied_path: Path | None = None
        try:
            with self.database.session() as session:
                attachment = session.scalar(select(Attachment).where(Attachment.sha256 == sha))
                if attachment is None:
                    safe_name = f"{sha[:16]}_{source_path.name}"; stored = self.attachment_dir / safe_name; shutil.copy2(source_path, stored); copied_path = stored
                    attachment = Attachment(sha256=sha, original_name=source_path.name, stored_path=str(stored), size_bytes=size, mime_type=mimetypes.guess_type(source_path.name)[0] or "")
                    session.add(attachment); session.flush()
                else: duplicate = True
                existing = session.scalar(select(EmailAttachmentLink).where(EmailAttachmentLink.email_id == email_id, EmailAttachmentLink.attachment_id == attachment.id))
                if existing is None: session.add(EmailAttachmentLink(email_id=email_id, attachment_id=attachment.id))
                session.refresh(attachment)
                return attachment, duplicate
        except Exception:
            if copied_path is not None and copied_path.exists():
                copied_path.unlink()
            raise

    def list_for_email(self, email_id: int) -> list[Attachment]:
        statement = select(Attachment).join(EmailAttachmentLink, Attachment.id == EmailAttachmentLink.attachment_id).where(EmailAttachmentLink.email_id == email_id).order_by(Attachment.original_name)
        with self.database.session() as session: return list(session.scalars(statement))

    def remove_link(self, email_id: int, attachment_id: int) -> None:
        with self.database.session() as session: session.execute(delete(EmailAttachmentLink).where(EmailAttachmentLink.email_id == email_id, EmailAttachmentLink.attachment_id == attachment_id))

    def delete_file(self, attachment_id: int) -> None:
        with self.database.session() as session:
            attachment = session.get(Attachment, attachment_id)
            if attachment is None: return
            linked = session.scalar(select(EmailAttachmentLink).where(EmailAttachmentLink.attachment_id == attachment_id))
            if linked is not None: raise ValueError("附件仍被郵件使用，請先移除所有郵件關聯")
            path = Path(attachment.stored_path); session.delete(attachment)
            if path.exists(): path.unlink()

    def get(self, attachment_id: int) -> Attachment | None:
        with self.database.session() as session: return session.get(Attachment, attachment_id)
