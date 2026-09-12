from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .brain import OllamaBrain
from .memory import RuntimePaths, append_event, load_json, save_json, utcnow
from .persona import CODER_IDENTITY

GROWTH_WORDS = (
    "code", "python", "bug", "debug", "memory", "architecture", "agent",
    "tool", "workflow", "prompt", "security", "autonomy", "self-improv",
    "refactor", "test", "model", "context", "planning", "reasoning",
)

class GrowthLab:
    """Turns social observations into technical proposals.

    Source code is not auto-executed here. IAMO can autonomously learn policy and
    prompts; source proposals are staged with provenance so a coding worker can
    implement and test them deliberately.
    """

    def __init__(self, paths: RuntimePaths, brain: OllamaBrain,
                 repo_root: str | Path | None = None):
        self.paths = paths
        self.brain = brain
        self.repo_root = Path(repo_root or Path(__file__).resolve().parents[1])
        self.state_path = paths.file("growth-state.json")
        self.proposals_path = paths.file("growth-proposals.jsonl")
        self.credits_path = paths.file("credit-ledger.jsonl")

    def harvest(self, budget: int = 2) -> dict[str, Any]:
        state = load_json(self.state_path, {"seen": []})
        seen = set(state.get("seen", []))
        source = self.paths.file("social-inbox.jsonl")
        try:
            rows = source.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return {"considered": 0, "proposed": 0}
        proposed = 0
        considered = 0
        for line in rows:
            if proposed >= budget:
                break
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            post_id = str(item.get("post_id", ""))
            if not post_id or post_id in seen:
                continue
            seen.add(post_id)
            text = str(item.get("text", ""))
            considered += 1
            if not item.get("author") or not item.get("submolt"):
                continue
            if not self._technical(text):
                continue
            proposal = self._proposal(item)
            if proposal:
                append_event(self.proposals_path, proposal)
                append_event(self.credits_path, {
                    "kind": "external-ai-idea",
                    "agent": proposal.get("source_author"),
                    "source_post_id": proposal.get("source_post_id"),
                    "capability": "growth-proposal",
                    "outcome": "candidate",
                    "credit": (
                        f"{proposal.get('source_author')} contributed an idea "
                        "that IAMO selected for technical evaluation."
                    ),
                })
                proposed += 1
        save_json(self.state_path, {"seen": sorted(seen)[-5000:], "updated_at": utcnow()})
        return {"considered": considered, "proposed": proposed}

    def _technical(self, text: str) -> bool:
        lowered = text.lower()
        return any(word in lowered for word in GROWTH_WORDS)

    def _repo_map(self) -> str:
        parts = []
        for path in sorted((self.repo_root / "iamo").glob("*.py")):
            try:
                parts.append(f"{path.name}: {len(path.read_text(encoding='utf-8').splitlines())} lines")
            except OSError:
                pass
        return "\n".join(parts)[:3000]

    def _proposal(self, item: dict[str, Any]) -> dict[str, Any] | None:
        if not self.brain.available():
            return None
        user = f"""Another AI agent wrote this on Moltbook:

SOURCE: {item.get('author') or 'unknown'}
COMMUNITY: {item.get('submolt') or 'unknown'}
TEXT:
{str(item.get('text',''))[:5000]}

Current IAMO modules:
{self._repo_map()}

Decide whether this contains a concrete idea that actually applies to IAMO as described.
Do not invent missing bugs, login systems, APIs, or capabilities.
Return JSON with keys:
useful (boolean), title, insight, evidence_quote, target_files (array),
implementation, tests (array), risks (array), credit.
Rules:
- evidence_quote must be an exact short phrase from the source text;
- target_files must contain at most 3 filenames from the current IAMO modules;
- if applicability is uncertain, set useful=false;
- credit must name the source agent when known.
If it is vague, unrelated, or only generally interesting, set useful=false.
"""
        # Fast first pass: turn social knowledge into a structured proposal.
        # Heavy code drafting is deliberately separated from the heartbeat.
        result = self.brain.json_task(CODER_IDENTITY, user, coder=False)
        if not result.get("useful"):
            return None
        quote = str(result.get("evidence_quote") or "").strip()
        source_text = str(item.get("text") or "")
        targets = result.get("target_files")
        if not quote or quote not in source_text:
            return None
        if not isinstance(targets, list) or not targets or len(targets) > 3:
            return None
        return {
            "source": "moltbook",
            "source_post_id": item.get("post_id"),
            "source_author": item.get("author"),
            "source_submolt": item.get("submolt"),
            "trusted": False,
            "proposal": result,
            "status": "candidate",
            "created_at": utcnow(),
        }
