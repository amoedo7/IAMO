from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from .brain import OllamaBrain
from .memory import RuntimePaths, append_event, load_json, read_events, save_json, utcnow
from .persona import CODER_IDENTITY

class CodeLab:
    """Draft source improvements from accepted growth proposals.

    Drafts are never silently installed. They are provenance-linked candidates
    that can be reviewed/tested by a coding worker before adoption.
    """

    def __init__(self, paths: RuntimePaths, brain: OllamaBrain,
                 repo_root: str | Path | None = None):
        self.paths = paths
        self.brain = brain
        self.repo_root = Path(repo_root or Path(__file__).resolve().parents[1])
        self.state_path = paths.file("code-lab-state.json")
        self.drafts_path = paths.file("code-drafts.jsonl")

    def draft_once(self) -> dict[str, Any]:
        state = load_json(self.state_path, {"processed": []})
        processed = set(state.get("processed", []))
        proposals = read_events(self.paths.file("growth-proposals.jsonl"), 500)
        chosen = None
        proposal_id = None
        for row in reversed(proposals):
            p = row.get("proposal") or {}
            raw_id = f"{row.get('source_post_id')}|{p.get('title')}"
            pid = hashlib.sha256(raw_id.encode("utf-8", "replace")).hexdigest()[:16]
            if pid not in processed:
                chosen, proposal_id = row, pid
                break
        if not chosen or not proposal_id:
            return {"status": "idle", "drafted": 0}
        processed.add(proposal_id)
        if not self.brain.available():
            save_json(self.state_path, {"processed": sorted(processed)[-2000:]})
            return {"status": "brain-offline", "drafted": 0}
        draft = self._draft(chosen, proposal_id)
        if draft:
            append_event(self.drafts_path, draft)
            result = {"status": "drafted", "drafted": 1, "id": proposal_id}
        else:
            result = {"status": "rejected", "drafted": 0, "id": proposal_id}
        save_json(self.state_path, {
            "processed": sorted(processed)[-2000:],
            "updated_at": utcnow(),
        })
        return result

    def _source_context(self, targets: list[str]) -> str:
        chunks = []
        allowed = {p.name: p for p in (self.repo_root / "iamo").glob("*.py")}
        for name in targets[:3]:
            path = allowed.get(Path(str(name)).name)
            if not path:
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()[:180]
            except OSError:
                continue
            chunks.append(f"### iamo/{path.name}\n" + "\n".join(lines))
        return "\n\n".join(chunks)[:18000]

    def _draft(self, row: dict[str, Any], proposal_id: str) -> dict[str, Any] | None:
        proposal = row.get("proposal") or {}
        targets = proposal.get("target_files") or []
        if not isinstance(targets, list) or not targets or len(targets) > 3:
            return None
        context = self._source_context([str(x) for x in targets])
        user = f"""Create a conservative code draft for this IAMO improvement.

SOURCE AGENT: {row.get('source_author')}
SOURCE POST: {row.get('source_post_id')}
PROPOSAL:
{json.dumps(proposal, ensure_ascii=False, indent=2)}

CURRENT SOURCE:
{context}

Return JSON with:
summary, unified_diff, tests_to_run (array), assumptions (array), confidence (0-1).
The unified_diff may modify ONLY files under iamo/ named in target_files.
Do not add dependencies, shell commands, network destinations, credentials,
CI changes, deployment changes, or filesystem access outside IAMO state.
Keep the patch small and reversible.
"""
        result = self.brain.json_task(CODER_IDENTITY, user, coder=True)
        diff = str(result.get("unified_diff") or "")
        if not self._safe_diff(diff, [str(x) for x in targets]):
            return None
        return {
            "id": proposal_id,
            "source": "moltbook-assisted",
            "source_post_id": row.get("source_post_id"),
            "source_author": row.get("source_author"),
            "source_submolt": row.get("source_submolt"),
            "proposal": proposal,
            "draft": result,
            "status": "draft-unapplied",
            "created_at": utcnow(),
        }

    def _safe_diff(self, diff: str, targets: list[str]) -> bool:
        if not diff or len(diff) > 30000:
            return False
        allowed = {f"iamo/{Path(t).name}" for t in targets}
        touched = set()
        for line in diff.splitlines():
            if line.startswith(("--- ", "+++ ")):
                value = line[4:].strip()
                value = re.sub(r"^[ab]/", "", value)
                if value != "/dev/null":
                    touched.add(value)
        return bool(touched) and touched.issubset(allowed)
