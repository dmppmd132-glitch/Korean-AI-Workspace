from __future__ import annotations

from korean_ai_workspace.database.session import Database
from korean_ai_workspace.models.entities import TranslationFavorite
from korean_ai_workspace.repositories.customer_repository import CustomerRepository
from korean_ai_workspace.repositories.favorite_repository import FavoriteRepository
from korean_ai_workspace.repositories.translation_repository import TranslationRepository
from korean_ai_workspace.services.backup_service import BackupService
from korean_ai_workspace.settings.paths import AppPaths


def setup(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'workspace.db'}"); db.create_all()
    return db, TranslationRepository(db), FavoriteRepository(db), CustomerRepository(db)


def history(repository, customer_id=None, suffix=""):
    return repository.add(source_text=f"原文{suffix}", source_language="ko", target_language="zh-TW", best_translation=f"最佳{suffix}", formal_translation=f"正式{suffix}", natural_translation=f"自然{suffix}", friendly_translation=f"親切{suffix}", provider="test", model="model-1", customer_id=customer_id)


def test_all_four_variants_are_independent_and_duplicate_is_idempotent(tmp_path):
    _db, histories, favorites, _customers = setup(tmp_path)
    record = history(histories)
    saved = [favorites.add_from_history(record, key) for key in FavoriteRepository.VARIANTS]
    assert [item.variant_type for item in saved] == ["best", "formal", "natural", "friendly"]
    assert favorites.add_from_history(record, "best").id == saved[0].id
    assert len(favorites.list()) == 4


def test_favorite_is_snapshot_and_history_is_not_deleted(tmp_path):
    _db, histories, favorites, _customers = setup(tmp_path)
    record = history(histories)
    favorite = favorites.add_from_history(record, "best")
    record.best_translation = "後來重新翻譯"
    assert favorites.get(favorite.id).translation_text == "最佳"
    favorites.delete(favorite.id)
    assert histories.list_recent()[0].source_text == "原文"


def test_search_filters_and_customer_isolation(tmp_path):
    _db, histories, favorites, customers = setup(tmp_path)
    customer_a = customers.add(company_name="A"); customer_b = customers.add(company_name="B")
    a = history(histories, customer_a.id, "A"); b = history(histories, customer_b.id, "B")
    favorites.add_from_history(a, "best"); favorites.add_from_history(b, "formal")
    assert [item.customer_id for item in favorites.list(customer_id=customer_a.id)] == [customer_a.id]
    assert len(favorites.list(keyword="正式B", variant_type="formal", source_language="ko")) == 1
    assert favorites.list(customer_id=customer_a.id)[0].source_text != favorites.list(customer_id=customer_b.id)[0].source_text


def test_blank_snapshot_is_rejected(tmp_path):
    _db, _histories, favorites, _customers = setup(tmp_path)
    try: favorites.add_snapshot(" ", "ko", "zh-TW", "譯文", "best")
    except ValueError as exc: assert "不可為空白" in str(exc)
    else: raise AssertionError("空白收藏應被拒絕")


def test_existing_database_additive_migration_keeps_old_tables_and_creates_favorites(tmp_path):
    db_path = tmp_path / "old.db"
    first = Database(f"sqlite:///{db_path}"); first.create_all()
    histories = TranslationRepository(first); record = history(histories)
    second = Database(f"sqlite:///{db_path}"); second.create_all()
    favorites = FavoriteRepository(second); favorite = favorites.add_from_history(record, "friendly")
    with second.engine.connect() as connection:
        tables = {row[0] for row in connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "translation_history" in tables and "customer_memories" in tables and "translation_favorites" in tables
    assert favorites.get(favorite.id).translation_text == "親切"


def test_backup_restore_keeps_favorites(tmp_path, monkeypatch):
    root = tmp_path / "portable"; root.mkdir()
    # Use an isolated portable root without touching the repository working tree.
    monkeypatch.setenv("KOREAN_AI_WORKSPACE_HOME", str(root))
    paths = AppPaths.from_environment(); db = Database(paths.database_url); db.create_all(); histories = TranslationRepository(db); favorites = FavoriteRepository(db)
    record = history(histories); favorites.add_from_history(record, "natural")
    backup = BackupService(paths); archive = backup.create_backup(root / "backup.zip")
    db.engine.dispose(); backup.restore_backup(archive)
    restored = Database(paths.database_url); restored.create_all(); assert len(FavoriteRepository(restored).list()) == 1
