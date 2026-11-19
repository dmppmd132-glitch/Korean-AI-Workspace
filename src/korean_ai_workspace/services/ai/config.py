from __future__ import annotations

from dataclasses import dataclass


DEFAULT_API_TIMEOUT_SECONDS = 180
FIXED_PROVIDER = "gemini"
FIXED_MODEL = "gemini-4-hydrogen"
FIXED_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/openai"


PROVIDER_PRESETS = {
    "openai": {
        "label": "OpenAI",
        "endpoint": "https://api.openai.com/v1",
        "models": ("gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"),
    },
    "gemini": {
        "label": "Google Gemini（OpenAI 相容）",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": (FIXED_MODEL,),
    },
    "openai_compatible": {
        "label": "OpenAI 相容 API（自訂）",
        "endpoint": "",
        "models": (),
    },
}


@dataclass(frozen=True)
class AIProviderConfig:
    provider: str
    api_key: str
    model: str
    endpoint: str = "https://api.openai.com/v1"
    timeout_seconds: int = DEFAULT_API_TIMEOUT_SECONDS

    def validate(self) -> None:
        if not self.provider.strip():
            raise ValueError("尚未指定 AI 服務商")
        if not self.api_key.strip():
            raise ValueError("尚未設定 API Key")
        if not self.model.strip():
            raise ValueError("尚未設定模型名稱")
        if self.provider == "openai_compatible" and not self.endpoint.strip():
            raise ValueError("OpenAI 相容 API 必須設定 Endpoint")
