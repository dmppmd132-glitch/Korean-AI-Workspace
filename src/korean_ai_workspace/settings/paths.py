from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    root: Path
    data: Path
    database: Path
    attachments: Path
    history: Path
    customer_memory: Path
    config: Path
    backups: Path
    logs: Path
    temp: Path

    @classmethod
    def from_environment(cls) -> "AppPaths":
        # Portable mode: data lives beside the executable or project root.
        base = Path(os.environ.get("KOREAN_AI_WORKSPACE_HOME", Path.cwd()))
        data = base / "data"
        paths = cls(
            root=base,
            data=data,
            database=data / "database",
            attachments=data / "attachments",
            history=data / "history",
            customer_memory=data / "customer_memory",
            config=base / "config",
            backups=base / "backups",
            logs=base / "logs",
            temp=base / "temp",
        )
        for path in (paths.data, paths.database, paths.attachments, paths.history,
                     paths.customer_memory, paths.config, paths.backups, paths.logs, paths.temp):
            path.mkdir(parents=True, exist_ok=True)
        return paths

    @property
    def database_url(self) -> str:
        return f"sqlite:///{(self.database / 'workspace.db').as_posix()}"

    @property
    def attachment_directory(self) -> Path:
        return self.attachments
