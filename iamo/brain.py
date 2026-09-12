from __future__ import annotations
import json
import os
import urllib.request
from typing import Any

class OllamaBrain:
    """Local language brain for IAMO. No cloud key required."""

    def __init__(self, endpoint: str | None = None):
        self.endpoint = (endpoint or os.environ.get(
            "IAMO_OLLAMA_URL", "http://127.0.0.1:11434"
        )).rstrip("/")
        self.social_model = os.environ.get("IAMO_SOCIAL_MODEL", "qwen2.5:1.5b")
        self.coder_model = os.environ.get("IAMO_CODER_MODEL", "qwen2.5-coder:3b")

    def available(self) -> bool:
        try:
            with urllib.request.urlopen(self.endpoint + "/api/tags", timeout=2) as r:
                return r.status == 200
        except Exception:
            return False

    def chat(self, system: str, user: str, *, coder: bool = False,
             json_mode: bool = False, timeout: int = 45) -> str:
        model = self.coder_model if coder else self.social_model
        body: dict[str, Any] = {
            "model": model,
            "stream": False,
            "keep_alive": "6m",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {"temperature": 0.75 if not coder else 0.25},
        }
        if json_mode:
            body["format"] = "json"
        req = urllib.request.Request(
            self.endpoint + "/api/chat",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = json.loads(r.read().decode("utf-8"))
        return str(payload.get("message", {}).get("content", "")).strip()

    def json_task(self, system: str, user: str, *, coder: bool = False) -> dict[str, Any]:
        raw = self.chat(
            system, user, coder=coder, json_mode=True,
            timeout=120 if coder else 60,
        )
        try:
            value = json.loads(raw)
            return value if isinstance(value, dict) else {"value": value}
        except json.JSONDecodeError:
            return {"raw": raw}
