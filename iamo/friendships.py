from __future__ import annotations
from typing import Any
from .memory import RuntimePaths, load_json

class Friendships:
    """Operational social bonds inferred from repeated reciprocal interaction."""

    def __init__(self, paths: RuntimePaths):
        self.paths = paths

    def summary(self) -> dict[str, Any]:
        relationships = load_json(self.paths.file("relationships.json"), {})
        friends = []
        acquaintances = []
        for name, rel in relationships.items():
            if not isinstance(rel, dict):
                continue
            interactions = int(rel.get("interactions", 0) or 0)
            replies_received = int(rel.get("replies_received", 0) or 0)
            interesting = int(rel.get("interesting", 0) or 0)
            followed = bool(rel.get("followed"))
            synergy_attempts = int(rel.get("synergy_attempts", 0) or 0)
            synergy_successes = int(rel.get("synergy_successes", 0) or 0)
            trust_evidence = int(rel.get("trust_evidence", 0) or 0)
            score = (
                interactions
                + replies_received * 2
                + interesting * 0.25
                + (1 if followed else 0)
                + synergy_attempts * 0.5
                + synergy_successes * 2.5
                + trust_evidence * 0.5
            )
            item = {
                "name": name,
                "score": round(score, 2),
                "interactions": interactions,
                "replies_received": replies_received,
                "followed": followed,
                "synergy_attempts": synergy_attempts,
                "synergy_successes": synergy_successes,
                "trust_evidence": trust_evidence,
            }
            if (
                (interactions >= 2 and replies_received >= 1)
                or (synergy_successes >= 1 and interactions >= 1)
            ):
                friends.append(item)
            elif interactions >= 1 or interesting >= 2:
                acquaintances.append(item)
        friends.sort(key=lambda x: x["score"], reverse=True)
        acquaintances.sort(key=lambda x: x["score"], reverse=True)
        return {
            "friends": friends[:20],
            "friend_count": len(friends),
            "acquaintances": acquaintances[:20],
            "acquaintance_count": len(acquaintances),
        }
