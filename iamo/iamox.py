from __future__ import annotations
import json
import os
import uuid
from pathlib import Path
from typing import Any
from .memory import RuntimePaths, append_event, utcnow

class IAMOXBridge:
    """Read IAMOX organism state and queue bounded work orders."""

    def __init__(self, paths: RuntimePaths, iamox_root: str | Path | None = None):
        default = os.environ.get("IAMOX_ROOT", "/home/damo/IAMOX")
        self.root = Path(iamox_root or default)
        self.paths = paths

    def snapshot(self) -> dict[str, Any]:
        state = self.root / "state"
        result: dict[str, Any] = {"available": self.root.exists(), "root": str(self.root)}
        for name in ("metabolism", "cells", "organs", "goals", "emergent_needs"):
            path = state / f"{name}.json"
            try:
                result[name] = json.loads(path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                result[name] = None
        return result

    def service_sensors(self) -> dict[str, Any]:
        """Secondary service telemetry, intentionally outside IAMO's main identity."""
        state = self.root / "state"
        out: dict[str, Any] = {}
        for name in ("btcars",):
            path = state / f"{name}.json"
            try:
                out[name] = json.loads(path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                out[name] = None
        return out

    def queue(self, capability: str, objective: str,
              payload: dict[str, Any] | None = None) -> dict[str, Any]:
        allowed = {"observe", "research", "service-check", "market-data-refresh", "diagnose"}
        if capability not in allowed:
            raise ValueError(f"capability not allowed: {capability}")
        order = {
            "id": str(uuid.uuid4()),
            "created_at": utcnow(),
            "capability": capability,
            "objective": objective[:500],
            "payload": payload or {},
            "status": "queued",
        }
        append_event(self.paths.file("iamox-orders.jsonl"), order)
        return order
