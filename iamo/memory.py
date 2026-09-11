from __future__ import annotations
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

@dataclass(frozen=True)
class RuntimePaths:
    root: Path

    @classmethod
    def default(cls) -> "RuntimePaths":
        value = os.environ.get("IAMO_STATE_DIR")
        root = Path(value).expanduser() if value else Path.home() / ".local/state/iamo"
        root.mkdir(parents=True, exist_ok=True)
        return cls(root)

    def file(self, name: str) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root / name

def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default

def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = dict(event)
    row.setdefault("at", utcnow())
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

def read_events(path: Path, limit: int = 500) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except FileNotFoundError:
        return []
    out: list[dict[str, Any]] = []
    for line in lines:
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                out.append(value)
        except json.JSONDecodeError:
            continue
    return out
