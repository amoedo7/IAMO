from __future__ import annotations

import json
import os
import urllib.request
from typing import Any


class OllamaBrain:
    """Local language brain for IAMO. No cloud key required."""

    SOCIAL_FALLBACKS = ("qwen3:8b", "qwen3:4b", "qwen3:0.6b")
    CODER_FALLBACKS = ("qwen3:8b", "qwen3:4b", "qwen3:0.6b")

    def __init__(self, endpoint: str | None = None):
        self.endpoint = (
            endpoint
            or os.environ.get("IAMO_OLLAMA_URL", "http://127.0.0.1:11434")
        ).rstrip("/")
        self.social_model = os.environ.get("IAMO_SOCIAL_MODEL", "qwen3:8b")
        self.coder_model = os.environ.get("IAMO_CODER_MODEL", "qwen3:8b")
        self.keep_alive = os.environ.get("IAMO_KEEP_ALIVE", "90s")
        self.context_length = max(
            2048,
            int(os.environ.get("IAMO_CONTEXT_LENGTH", "8192")),
        )

    def available_models(self) -> list[str]:
        try:
            with urllib.request.urlopen(self.endpoint + "/api/tags", timeout=2) as r:
                if r.status != 200:
                    return []
                payload = json.loads(r.read().decode("utf-8"))
        except Exception:
            return []

        out: list[str] = []
        for item in payload.get("models", []):
            name = str(item.get("name") or item.get("model") or "").strip()
            if name:
                out.append(name)
        return out

    def available(self) -> bool:
        return bool(self.available_models())

    def resolve_model(self, *, coder: bool = False) -> str:
        installed = set(self.available_models())
        configured = self.coder_model if coder else self.social_model
        fallbacks = self.CODER_FALLBACKS if coder else self.SOCIAL_FALLBACKS

        candidates = [configured, *fallbacks]
        seen: set[str] = set()
        for candidate in candidates:
            candidate = str(candidate or "").strip()
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            if candidate in installed:
                return candidate

        raise RuntimeError(
            "IAMO no tiene un modelo Ollama compatible instalado. "
            f"Configurado={configured!r}; disponibles={sorted(installed)!r}"
        )

    def model_status(self, *, coder: bool = False) -> dict[str, Any]:
        configured = self.coder_model if coder else self.social_model
        installed = self.available_models()
        try:
            selected = self.resolve_model(coder=coder)
        except RuntimeError:
            selected = ""

        if selected == "qwen3:8b":
            tier = "full"
        elif selected == "qwen3:4b":
            tier = "fallback"
        elif selected == "qwen3:0.6b":
            tier = "seed"
        else:
            tier = "unavailable"

        return {
            "configured": configured,
            "selected": selected,
            "tier": tier,
            "degraded": bool(selected and selected != configured),
            "available": installed,
        }

    def chat(
        self,
        system: str,
        user: str,
        *,
        coder: bool = False,
        json_mode: bool = False,
        timeout: int = 45,
    ) -> str:
        model = self.resolve_model(coder=coder)
        body: dict[str, Any] = {
            "model": model,
            "stream": False,
            "keep_alive": self.keep_alive,
            "think": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {
                "temperature": 0.45 if not coder else 0.20,
                "num_ctx": self.context_length,
            },
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

    def json_task(
        self,
        system: str,
        user: str,
        *,
        coder: bool = False,
    ) -> dict[str, Any]:
        raw = self.chat(
            system,
            user,
            coder=coder,
            json_mode=True,
            timeout=120 if coder else 90,
        )
        try:
            value = json.loads(raw)
            return value if isinstance(value, dict) else {"value": value}
        except json.JSONDecodeError:
            return {"raw": raw}
