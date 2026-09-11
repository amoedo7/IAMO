from __future__ import annotations
import hashlib
from copy import deepcopy
from dataclasses import dataclass
from typing import Any
from .memory import RuntimePaths, append_event, load_json, read_events, save_json, utcnow

DEFAULT_POLICY: dict[str, Any] = {
    "reply_threshold": 0.65,
    "novelty_weight": 0.55,
    "social_read_limit": 20,
    "max_daily_posts": 3,
    "iamox_parallelism": 2,
}
BOUNDS = {
    "reply_threshold": (0.35, 0.90),
    "novelty_weight": (0.20, 0.90),
    "social_read_limit": (5, 50),
    "max_daily_posts": (1, 6),
    "iamox_parallelism": (1, 4),
}

@dataclass
class ImprovementResult:
    adopted: bool
    baseline_score: float
    candidate_score: float
    changed: dict[str, Any]
    policy: dict[str, Any]

class SelfImprover:
    """Adaptive policy search. It never executes or patches source code."""

    def __init__(self, paths: RuntimePaths):
        self.paths = paths
        self.policy_path = paths.file("policy.json")
        self.outcomes_path = paths.file("outcomes.jsonl")
        self.history_path = paths.file("improvements.jsonl")
        if not self.policy_path.exists():
            save_json(self.policy_path, DEFAULT_POLICY)

    def policy(self) -> dict[str, Any]:
        value = load_json(self.policy_path, DEFAULT_POLICY)
        merged = dict(DEFAULT_POLICY)
        if isinstance(value, dict):
            merged.update({k: v for k, v in value.items() if k in DEFAULT_POLICY})
        return self._bounded(merged)

    def record_outcome(self, *, kind: str, reward: float, signal: float = 1.0,
                       safety: float = 1.0, latency_ms: float = 0.0) -> None:
        append_event(self.outcomes_path, {
            "kind": kind,
            "reward": max(-1.0, min(1.0, float(reward))),
            "signal": max(0.0, min(1.0, float(signal))),
            "safety": max(0.0, min(1.0, float(safety))),
            "latency_ms": max(0.0, float(latency_ms)),
        })

    def stage_external_idea(self, text: str, source: str) -> dict[str, Any]:
        digest = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]
        idea = {
            "id": digest, "source": source, "text": text[:4000],
            "trusted": False, "executable": False, "status": "candidate",
            "created_at": utcnow(),
        }
        append_event(self.paths.file("external-ideas.jsonl"), idea)
        return idea

    def improve(self) -> ImprovementResult:
        current = self.policy()
        outcomes = read_events(self.outcomes_path, 1000)
        baseline = self._score(current, outcomes)
        best = current
        best_score = baseline
        for candidate in self._candidates(current):
            score = self._score(candidate, outcomes)
            if score > best_score + 0.01:
                best, best_score = candidate, score
        changed = {k: best[k] for k in best if best[k] != current[k]}
        adopted = bool(changed)
        if adopted:
            save_json(self.policy_path, best)
        append_event(self.history_path, {
            "adopted": adopted,
            "baseline_score": round(baseline, 6),
            "candidate_score": round(best_score, 6),
            "changed": changed,
            "policy": best,
        })
        return ImprovementResult(adopted, baseline, best_score, changed, best)

    def _score(self, policy: dict[str, Any], outcomes: list[dict[str, Any]]) -> float:
        if not outcomes:
            return 0.0
        total = 0.0
        threshold = float(policy["reply_threshold"])
        novelty_weight = float(policy["novelty_weight"])
        parallelism = int(policy["iamox_parallelism"])
        for row in outcomes:
            reward = float(row.get("reward", 0))
            signal = float(row.get("signal", 1))
            safety = float(row.get("safety", 1))
            latency = float(row.get("latency_ms", 0))
            kind = str(row.get("kind", "generic"))
            if kind == "social":
                selected = signal >= threshold
                contribution = (reward if selected else -0.25 * reward)
                contribution *= (0.5 + novelty_weight * signal)
            elif kind == "iamox":
                contribution = reward * safety
                contribution -= min(latency / 120000.0, 0.25)
                contribution -= 0.015 * max(0, parallelism - 2)
            else:
                contribution = reward * safety
            total += contribution
        return total / len(outcomes)

    def _candidates(self, policy: dict[str, Any]) -> list[dict[str, Any]]:
        deltas = {
            "reply_threshold": (-0.05, 0.05),
            "novelty_weight": (-0.05, 0.05),
            "social_read_limit": (-5, 5),
            "max_daily_posts": (-1, 1),
            "iamox_parallelism": (-1, 1),
        }
        values: list[dict[str, Any]] = []
        for key, pair in deltas.items():
            for delta in pair:
                candidate = deepcopy(policy)
                candidate[key] = candidate[key] + delta
                values.append(self._bounded(candidate))
        return values

    def _bounded(self, policy: dict[str, Any]) -> dict[str, Any]:
        out = dict(policy)
        for key, (low, high) in BOUNDS.items():
            value = max(low, min(high, out[key]))
            if isinstance(DEFAULT_POLICY[key], int):
                value = int(round(value))
            else:
                value = round(float(value), 4)
            out[key] = value
        return out
