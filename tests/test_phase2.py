from __future__ import annotations

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.repositories.translation_repository import TranslationRepository
from korean_ai_workspace.services.translation.service import TranslationService
from korean_ai_workspace.ui.main_window import FloatingTranslationWindow, MainWindow, TranslationWorker


class FakeProvider:
    def translate(self, prompt: str) -> str:
        return json.dumps({"source_language": "ko", "target_language": "zh-TW", "best": "最佳", "formal": "正式", "natural": "自然", "friendly": "親切"})


class FailingService:
    def translate(self, _text, _language):
        raise RuntimeError("測試網路錯誤")


def test_history_search_matches_any_translation_variant(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'workspace.db'}"); db.create_all(); repo = TranslationRepository(db)
    repo.add(source_text="안녕하세요", source_language="ko", target_language="zh-TW", best_translation="最佳問候", formal_translation="正式問候", natural_translation="自然問候", friendly_translation="親切問候", provider="test", model="fake")
    assert len(repo.search("自然問候")) == 1
    assert len(repo.search("不存在")) == 0


def test_translation_result_has_four_variants():
    result = TranslationService(FakeProvider()).translate("안녕하세요", "ko")
    assert (result.best, result.formal, result.natural, result.friendly) == ("最佳", "正式", "自然", "親切")


def test_phase2_windows_can_be_constructed_offscreen(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    db = Database(f"sqlite:///{tmp_path / 'workspace.db'}"); db.create_all(); window = MainWindow(TranslationRepository(db))
    assert window.pages.count() == 6
    assert len(window.result_editors) == 4
    assert isinstance(window.floating_window, FloatingTranslationWindow)
    window.close(); window.floating_window.close(); app.quit()


def test_provider_model_and_endpoint_presets_can_be_selected(tmp_path):
    app = QApplication.instance() or QApplication([])
    db = Database(f"sqlite:///{tmp_path / 'workspace.db'}"); db.create_all(); window = MainWindow(TranslationRepository(db))
    assert window.provider.currentData() == "gemini"
    assert window.model.currentText() == "gemini-4-hydrogen"
    assert window.endpoint.currentText() == "https://generativelanguage.googleapis.com/v1beta/openai"
    assert not window.provider.isEnabled()
    assert not window.model.isEnabled()
    assert not window.endpoint.isEnabled()
    assert window.translation_mode.currentData() == "fast"
    window.close(); window.floating_window.close(); app.processEvents()


def test_translation_worker_emits_failure_and_finished_on_exception():
    failures = []; finished = []
    worker = TranslationWorker(FailingService(), "測試", "auto")
    worker.signals.failure.connect(failures.append); worker.signals.finished.connect(lambda: finished.append(True))
    worker.run()
    assert failures == ["測試網路錯誤"]
    assert finished == [True]
