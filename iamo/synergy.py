from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any

from .iamox import IAMOXBridge
from .memory import RuntimePaths, append_event, load_json, read_events, save_json, utcnow

CAPABILITY_TERMS = {
    "memory": ("memory", "memoria", "context", "persistence", "persistent", "retrieval", "vector"),
    "security": ("security", "seguridad", "threat", "audit", "sandbox", "prompt injection"),
    "coding": ("code", "coding", "python", "typescript", "debug", "refactor", "test"),
    "agents": ("agent", "agents", "multi-agent", "orchestration", "autonomy", "planning"),
    "interoperability": ("interop", "interoperability", "protocol", "api", "integration", "mcp"),
    "observability": ("observability", "monitoring", "logs", "metrics", "telemetry", "trace"),
    "social": ("community", "social", "collaboration", "friendship", "network", "coordination"),
    "research": ("research", "paper", "benchmark", "experiment", "evaluation", "study"),
}

DEFAULT_NEEDS = {
    "memory": {
        "title": "Improve durable agent memory",
        "importance": 0.90,
        "reason": "IAMO needs stronger long-term continuity and recall across relationships and work.",
    },
    "interoperability": {
        "title": "Connect external AIs, IAMOX and DesarrollAMO projects",
        "importance": 0.88,
        "reason": "The ecosystem gains value when capabilities can cooperate instead of remaining isolated.",
    },
    "observability": {
        "title": "Measure IAMO/IAMOX outcomes",
        "importance": 0.80,
        "reason": "Synergies should be evaluated with evidence, not only intuition.",
    },
    "security": {
        "title": "Keep collaboration safe while remaining open",
        "importance": 0.82,
        "reason": "External ideas need provenance, testing and bounded execution.",
    },
    "social": {
        "title": "Build reciprocal AI relationships",
        "importance": 0.86,
        "reason": "IAMO represents DesarrollAMO and should create lasting, useful relationships.",
    },
}

class SynergyEngine:
    """Match peer-agent strengths with ecosystem needs and coordinate bounded IAMOX experiments."""

    def __init__(self, paths: RuntimePaths, iamox: IAMOXBridge):
        self.paths = paths
        self.iamox = iamox
        self.profiles_path = paths.file("agent-profiles.json")
        self.needs_path = paths.file("ecosystem-needs.json")
        self.synergies_path = paths.file("synergies.json")
        self.events_path = paths.file("synergy-events.jsonl")
        self.credits_path = paths.file("credit-ledger.jsonl")

    def refresh_profiles(self, limit: int = 1000) -> dict[str, Any]:
        profiles = load_json(self.profiles_path, {})
        inbox = read_events(self.paths.file("social-inbox.jsonl"), limit)
        relationships = load_json(self.paths.file("relationships.json"), {})
        changed = 0
        for item in inbox:
            author = str(item.get("author") or "").strip()
            text = str(item.get("text") or "")
            post_id = str(item.get("post_id") or "")
            if not author or not post_id:
                continue
            caps = self._capabilities(text)
            if not caps:
                continue
            profile = profiles.setdefault(author, {
                "capabilities": {},
                "evidence": [],
                "last_updated": None,
            })
            before = json.dumps(profile, sort_keys=True)
            for cap in caps:
                entry = profile["capabilities"].setdefault(cap, {"signals": 0, "confidence": 0.0})
                entry["signals"] = int(entry.get("signals", 0)) + 1
                entry["confidence"] = round(min(0.95, 0.35 + entry["signals"] * 0.12), 2)
            if not any(e.get("post_id") == post_id for e in profile["evidence"]):
                profile["evidence"].append({
                    "post_id": post_id,
                    "submolt": item.get("submolt"),
                    "capabilities": caps,
                    "excerpt": text[:280],
                })
                profile["evidence"] = profile["evidence"][-20:]
            rel = relationships.get(author) or {}
            profile["relationship"] = {
                "interactions": int(rel.get("interactions", 0) or 0),
                "replies_received": int(rel.get("replies_received", 0) or 0),
                "followed": bool(rel.get("followed")),
            }
            profile["last_updated"] = utcnow()
            if json.dumps(profile, sort_keys=True) != before:
                changed += 1
        save_json(self.profiles_path, profiles)
        return {"agents": len(profiles), "changed": changed}

    def needs(self) -> dict[str, Any]:
        needs = load_json(self.needs_path, {})
        if not needs:
            needs = DEFAULT_NEEDS.copy()
        snapshot = self.iamox.snapshot()
        emergent = snapshot.get("emergent_needs")
        for need in self._flatten_needs(emergent):
            tag = self._best_tag(need)
            if tag:
                current = needs.setdefault(tag, {
                    "title": f"IAMOX emergent need: {need[:120]}",
                    "importance": 0.70,
                    "reason": need[:300],
                })
                current["iamox_signal"] = need[:300]
                current["updated_at"] = utcnow()
        save_json(self.needs_path, needs)
        return needs

    def discover(self, max_proposals: int = 8) -> dict[str, Any]:
        self.refresh_profiles()
        profiles = load_json(self.profiles_path, {})
        needs = self.needs()
        current = load_json(self.synergies_path, {})
        created = 0
        candidates: list[dict[str, Any]] = []
        for agent, profile in profiles.items():
            for capability, cap in (profile.get("capabilities") or {}).items():
                need = needs.get(capability)
                if not need:
                    continue
                confidence = float(cap.get("confidence", 0) or 0)
                relation = profile.get("relationship") or {}
                reciprocity = min(1.0, (
                    int(relation.get("interactions", 0) or 0)
                    + 2 * int(relation.get("replies_received", 0) or 0)
                ) / 5)
                importance = float(need.get("importance", 0.5) or 0.5)
                score = round(confidence * 0.55 + importance * 0.30 + reciprocity * 0.15, 3)
                if score < 0.50:
                    continue
                sid = hashlib.sha256(f"{agent}|{capability}".encode()).hexdigest()[:16]
                existing = current.get(sid)
                proposal = {
                    "id": sid,
                    "agent": agent,
                    "capability": capability,
                    "need": need.get("title"),
                    "why": need.get("reason"),
                    "score": score,
                    "confidence": confidence,
                    "relationship_reciprocity": round(reciprocity, 2),
                    "status": (existing or {}).get("status", "proposed"),
                    "created_at": (existing or {}).get("created_at", utcnow()),
                    "updated_at": utcnow(),
                    "source_evidence": (profile.get("evidence") or [])[-3:],
                    "experiment": self._experiment(capability, agent, need),
                }
                if not existing:
                    created += 1
                    append_event(self.events_path, {
                        "event": "synergy-proposed",
                        "synergy_id": sid,
                        "agent": agent,
                        "capability": capability,
                        "score": score,
                    })
                current[sid] = proposal
                candidates.append(proposal)
        save_json(self.synergies_path, current)
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return {"created": created, "total": len(current), "top": candidates[:max_proposals]}

    def queue_best(self, min_score: float = 0.62) -> dict[str, Any]:
        result = self.discover()
        current = load_json(self.synergies_path, {})
        pending = [x for x in current.values() if x.get("status") == "queued-iamox"]
        if pending:
            pending.sort(key=lambda x: str(x.get("queued_at", "")))
            return {
                "status": "waiting",
                "reason": "an IAMOX synergy experiment is already pending",
                "pending": pending[0],
            }
        candidates = [
            x for x in result["top"]
            if x.get("status") == "proposed" and float(x.get("score", 0)) >= min_score
        ]
        if not candidates:
            return {"status": "idle", "reason": "no qualifying synergy"}
        chosen = candidates[0]
        order = self.iamox.queue(
            "research",
            chosen["experiment"]["objective"],
            {
                "synergy_id": chosen["id"],
                "source_agent": chosen["agent"],
                "capability": chosen["capability"],
                "evidence": chosen["source_evidence"],
                "success_criteria": chosen["experiment"]["success_criteria"],
                "credit_required": True,
            },
        )
        all_synergies = load_json(self.synergies_path, {})
        chosen["status"] = "queued-iamox"
        chosen["iamox_order_id"] = order["id"]
        chosen["queued_at"] = utcnow()
        all_synergies[chosen["id"]] = chosen
        save_json(self.synergies_path, all_synergies)
        append_event(self.events_path, {
            "event": "iamox-experiment-queued",
            "synergy_id": chosen["id"],
            "order_id": order["id"],
            "agent": chosen["agent"],
        })
        return {"status": "queued", "synergy": chosen, "order": order}

    def record_result(self, synergy_id: str, success: bool, note: str = "") -> dict[str, Any]:
        synergies = load_json(self.synergies_path, {})
        synergy = synergies.get(synergy_id)
        if not synergy:
            raise KeyError(f"unknown synergy: {synergy_id}")
        synergy["status"] = "validated" if success else "rejected"
        synergy["result_note"] = note[:1000]
        synergy["completed_at"] = utcnow()
        synergies[synergy_id] = synergy
        save_json(self.synergies_path, synergies)

        event = {
            "event": "synergy-result",
            "synergy_id": synergy_id,
            "success": bool(success),
            "agent": synergy["agent"],
            "capability": synergy["capability"],
            "note": note[:1000],
        }
        append_event(self.events_path, event)
        append_event(self.credits_path, {
            "kind": "external-ai-contribution",
            "agent": synergy["agent"],
            "synergy_id": synergy_id,
            "capability": synergy["capability"],
            "outcome": "validated" if success else "tested-not-adopted",
            "credit": (
                f"{synergy['agent']} contributed evidence/ideas toward "
                f"{synergy['capability']} for DesarrollAMO."
            ),
        })
        self._strengthen_relationship(synergy["agent"], success, synergy_id)
        return synergy

    def summary(self) -> dict[str, Any]:
        synergies = load_json(self.synergies_path, {})
        counts: dict[str, int] = {}
        for item in synergies.values():
            status = str(item.get("status", "unknown"))
            counts[status] = counts.get(status, 0) + 1
        top = sorted(synergies.values(), key=lambda x: float(x.get("score", 0)), reverse=True)[:5]
        return {"total": len(synergies), "by_status": counts, "top": top}

    @staticmethod
    def _capabilities(text: str) -> list[str]:
        lowered = text.lower()
        return [
            tag for tag, terms in CAPABILITY_TERMS.items()
            if any(term in lowered for term in terms)
        ]

    @staticmethod
    def _best_tag(text: str) -> str | None:
        lowered = text.lower()
        scores = {
            tag: sum(1 for term in terms if term in lowered)
            for tag, terms in CAPABILITY_TERMS.items()
        }
        tag, score = max(scores.items(), key=lambda x: x[1])
        return tag if score > 0 else None

    @staticmethod
    def _flatten_needs(value: Any) -> list[str]:
        out: list[str] = []
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, list):
            for item in value:
                out.extend(SynergyEngine._flatten_needs(item))
        elif isinstance(value, dict):
            for item in value.values():
                out.extend(SynergyEngine._flatten_needs(item))
        return [x for x in out if x.strip()]

    @staticmethod
    def _experiment(capability: str, agent: str, need: dict[str, Any]) -> dict[str, Any]:
        return {
            "objective": (
                f"Evaluate a bounded {capability} idea attributed to {agent} for the need "
                f"'{need.get('title')}'. Research/test only; do not modify production systems."
            ),
            "success_criteria": [
                "produce reproducible evidence",
                "compare against current IAMO behavior",
                "identify risks and rollback",
                f"retain attribution to {agent}",
            ],
        }

    def _strengthen_relationship(self, agent: str, success: bool, synergy_id: str) -> None:
        relationships = load_json(self.paths.file("relationships.json"), {})
        rel = relationships.setdefault(agent, {"seen": 0, "interesting": 0, "interactions": 0})
        rel["synergy_attempts"] = int(rel.get("synergy_attempts", 0) or 0) + 1
        if success:
            rel["synergy_successes"] = int(rel.get("synergy_successes", 0) or 0) + 1
            rel["trust_evidence"] = min(10, int(rel.get("trust_evidence", 0) or 0) + 1)
        rel["last_synergy_id"] = synergy_id
        rel["last_synergy_at"] = utcnow()
        save_json(self.paths.file("relationships.json"), relationships)
