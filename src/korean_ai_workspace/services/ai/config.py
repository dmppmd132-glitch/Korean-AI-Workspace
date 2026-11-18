from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AIProviderConfig:
    provider: str
    api_key: str
    model: str
    endpoint: str = "https://api.openai.com/v1"
    timeout_seconds: int = 60

    def validate(self) -> None:
        if not self.provider.strip():
            raise ValueError("尚未指定 AI 服務商")
        if not self.api_key.strip():
            raise ValueError("尚未設定 API Key")
        if not self.model.strip():
            raise ValueError("尚未設定模型名稱")
        if self.provider == "openai_compatible" and not self.endpoint.strip():
            raise ValueError("OpenAI 相容 API 必須設定 Endpoint")
