from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.repositories.translation_repository import TranslationRepository
from korean_ai_workspace.repositories.customer_repository import CustomerRepository
from korean_ai_workspace.repositories.glossary_repository import GlossaryRepository
from korean_ai_workspace.repositories.email_repository import EmailRepository
from korean_ai_workspace.repositories.attachment_repository import AttachmentRepository
from korean_ai_workspace.settings.paths import AppPaths
from korean_ai_workspace.ui.main_window import MainWindow


def main() -> int:
    paths = AppPaths.from_environment()
    database = Database(paths.database_url)
    database.create_all()
    app = QApplication(sys.argv)
    app.setApplicationName("Korean AI Workspace")
    window = MainWindow(TranslationRepository(database), CustomerRepository(database), GlossaryRepository(database), EmailRepository(database), AttachmentRepository(database, paths.attachment_directory), paths)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
