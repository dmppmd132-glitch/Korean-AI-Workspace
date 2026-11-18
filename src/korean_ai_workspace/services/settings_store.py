from __future__ import annotations

import json
from pathlib import Path

from korean_ai_workspace.services.ai.config import AIProviderConfig
from korean_ai_workspace.services.secret_store import SecretStore, SecretStoreError


class SettingsStore:
    def __init__(self, config_directory: Path):
        self.config_directory = Path(config_directory)
        self.config_directory.mkdir(parents=True, exist_ok=True)
        self.path = self.config_directory / "settings.json"
        self.secrets = SecretStore(self.config_directory)

    def save_provider(self, config: AIProviderConfig) -> None:
        payload = {
            "version": 1,
            "provider": config.provider,
            "model": config.model,
            "endpoint": config.endpoint,
            "encrypted_api_key": self.secrets.encrypt(config.api_key),
        }
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def load_provider(self) -> AIProviderConfig | None:
        if not self.path.exists():
            return None
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return AIProviderConfig(
                provider=str(payload.get("provider", "openai")),
                api_key=self.secrets.decrypt(str(payload.get("encrypted_api_key", ""))),
                model=str(payload.get("model", "gpt-4o-mini")),
                endpoint=str(payload.get("endpoint", "https://api.openai.com/v1")),
            )
        except (OSError, json.JSONDecodeError, KeyError, TypeError, SecretStoreError) as exc:
            raise SecretStoreError("AI 設定讀取或 API Key 解密失敗") from exc
