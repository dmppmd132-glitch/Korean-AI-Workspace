from __future__ import annotations

import json
import urllib.error
import urllib.request
from abc import ABC, abstractmethod

from .config import AIProviderConfig


class AIProviderError(RuntimeError):
    pass


class AIProvider(ABC):
    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.config.validate()

    @abstractmethod
    def translate(self, prompt: str) -> str:
        raise NotImplementedError

    def test_connection(self) -> str:
        return self.translate("請只回覆：連線測試成功")


class OpenAICompatibleProvider(AIProvider):
    def translate(self, prompt: str) -> str:
        endpoint = self.config.endpoint.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "你是專業的韓文與台灣繁體中文商務翻譯助手。"},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise AIProviderError(f"AI API HTTP {exc.code}: {detail}") from exc
        except TimeoutError as exc:
            raise AIProviderError(f"AI API 回應逾時（{self.config.timeout_seconds} 秒）。請確認模型可用、網路穩定，或改用較快的 Flash 模型。") from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise AIProviderError(f"AI API 回應逾時（{self.config.timeout_seconds} 秒）。請確認模型可用、網路穩定，或改用較快的 Flash 模型。") from exc
            raise AIProviderError(f"AI API 網路連線失敗：{exc}") from exc
        except json.JSONDecodeError as exc:
            raise AIProviderError("AI API 回傳不是有效 JSON") from exc
        try:
            return result["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError("AI API 回傳格式不符合 Chat Completions 規格") from exc


def build_provider(config: AIProviderConfig) -> AIProvider:
    # Gemini can expose an OpenAI-compatible endpoint; users may set it explicitly.
    if config.provider in {"openai", "gemini", "openai_compatible"}:
        return OpenAICompatibleProvider(config)
    raise ValueError(f"不支援的 AI 服務商：{config.provider}")
