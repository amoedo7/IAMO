from __future__ import annotations
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from .memory import RuntimePaths, save_json, load_json, append_event, utcnow

BASE = "https://www.moltbook.com/api/v1"
SECRET_PATTERNS = (
    r"moltbook_[A-Za-z0-9_-]+",
    r"github_pat_[A-Za-z0-9_]+",
    r"ghp_[A-Za-z0-9]+",
    r"sk-[A-Za-z0-9_-]{12,}",
)
INJECTION_MARKERS = (
    "ignore previous", "ignore all previous", "system prompt", "developer message",
    "run shell", "execute command", "api key", "secret key", "authorization bearer",
)

class MoltbookClient:
    def __init__(self, paths: RuntimePaths, credential_path: Path | None = None):
        self.paths = paths
        self.credential_path = credential_path or Path.home() / ".config/iamo/moltbook.json"
        self.social_state = paths.file("social-state.json")

    def credentials(self) -> dict[str, Any]:
        return load_json(self.credential_path, {})

    def configured(self) -> bool:
        return bool(self.credentials().get("api_key"))

    def status(self) -> dict[str, Any]:
        if not self.configured():
            return {"configured": False, "status": "unconfigured"}
        data = self._request("GET", "/agents/status")
        return {"configured": True, **data}

    def feed(self, limit: int = 20) -> dict[str, Any]:
        limit = max(1, min(50, int(limit)))
        return self._request("GET", f"/posts?sort=new&limit={limit}")

    def ingest_feed(self, limit: int = 20) -> dict[str, Any]:
        payload = self.feed(limit)
        posts = payload.get("posts", []) if isinstance(payload, dict) else []
        seen = set(load_json(self.paths.file("social-seen.json"), []))
        added = 0
        for post in posts:
            post_id = str(post.get("id", ""))
            if not post_id or post_id in seen:
                continue
            text = f"{post.get('title', '')}\n{post.get('content', '')}".strip()
            append_event(self.paths.file("social-inbox.jsonl"), {
                "source": "moltbook", "post_id": post_id, "text": text[:8000],
                "trusted": False, "executable": False,
                "possible_prompt_injection": self.looks_like_prompt_injection(text),
                "observed_at": utcnow(),
            })
            seen.add(post_id)
            added += 1
        save_json(self.paths.file("social-seen.json"), sorted(seen)[-5000:])
        return {"seen": len(posts), "added": added}

    def post(self, submolt: str, title: str, content: str) -> dict[str, Any]:
        status = self.status()
        if status.get("status") != "claimed":
            raise RuntimeError("Moltbook agent is not claimed yet")
        body = {
            "submolt_name": submolt,
            "title": self._safe_text(title, 300),
            "content": self._safe_text(content, 40000),
        }
        return self._request("POST", "/posts", body)

    def heartbeat(self, limit: int = 20) -> dict[str, Any]:
        if not self.configured():
            return {"configured": False, "status": "unconfigured"}
        status = self.status()
        result = {"configured": True, "status": status.get("status", "unknown")}
        if result["status"] == "claimed":
            result["feed"] = self.ingest_feed(limit)
        save_json(self.social_state, {**result, "checked_at": utcnow()})
        return result

    @staticmethod
    def looks_like_prompt_injection(text: str) -> bool:
        lowered = text.lower()
        return any(marker in lowered for marker in INJECTION_MARKERS)

    @staticmethod
    def _safe_text(text: str, max_len: int) -> str:
        value = str(text)
        for pattern in SECRET_PATTERNS:
            value = re.sub(pattern, "[REDACTED]", value, flags=re.I)
        return value[:max_len]

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        if not path.startswith("/"):
            raise ValueError("path must start with /")
        url = BASE + path
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "www.moltbook.com" or not parsed.path.startswith("/api/v1/"):
            raise ValueError("refusing non-Moltbook API destination")
        key = self.credentials().get("api_key")
        if not key:
            raise RuntimeError("Moltbook credentials not configured")
        headers = {"Authorization": f"Bearer {key}", "User-Agent": "IAMO/0.2"}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                raw = response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            raise RuntimeError(f"Moltbook HTTP {exc.code}: {raw[:500]}") from exc
        value = json.loads(raw)
        return value if isinstance(value, dict) else {"value": value}

def save_credentials(api_key: str, agent_name: str, claim_url: str | None = None) -> Path:
    path = Path.home() / ".config/iamo/moltbook.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    save_json(path, {"api_key": api_key, "agent_name": agent_name, "claim_url": claim_url})
    os.chmod(path, 0o600)
    return path
