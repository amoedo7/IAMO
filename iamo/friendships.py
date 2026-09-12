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
            score = interactions + replies_received * 2 + interesting * 0.25 + (1 if followed else 0)
            item = {
                "name": name,
                "score": round(score, 2),
                "interactions": interactions,
                "replies_received": replies_received,
                "followed": followed,
            }
            if interactions >= 2 and replies_received >= 1:
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
