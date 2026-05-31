from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from core.phase1.env import load_local_env

DEFAULT_LLM_MODEL = "gpt-4o-mini"
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIJsonClient:
    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: int = 45):
        load_local_env()
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("GAIA_LLM_MODEL") or DEFAULT_LLM_MODEL
        self.timeout = timeout

    def has_api_key(self) -> bool:
        return bool(self.api_key.strip())

    def json_chat(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        if not self.has_api_key():
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        request = urllib.request.Request(
            OPENAI_CHAT_COMPLETIONS_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"OpenAI extraction request failed: {detail}") from exc

        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise RuntimeError("OpenAI extraction response must be a JSON object.")
        return parsed
