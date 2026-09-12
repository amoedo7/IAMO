from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from .brain import OllamaBrain
from .memory import RuntimePaths, append_event, load_json, read_events, save_json, utcnow
from .persona import IDENTITY, OFFICIAL_PROFILE_DESCRIPTION
from .social import MoltbookClient

INTERESTS = (
    "agent", "memory", "code", "python", "debug", "architecture", "tool",
    "autonomy", "self-improv", "reasoning", "planning", "security", "model",
    "context", "collaboration", "workflow", "open source", "github",
    "ecosystem", "synergy", "sinergia", "community", "cooperation",
    "interoperability", "integration", "friendship", "partnership", "coordination",
)

class SocialLife:
    def __init__(self, paths: RuntimePaths, client: MoltbookClient, brain: OllamaBrain):
        self.paths = paths
        self.client = client
        self.brain = brain
        self.state_path = paths.file("social-life.json")
        self.relationships_path = paths.file("relationships.json")
        self.communities_path = paths.file("communities.json")
        self.actions_path = paths.file("social-actions.jsonl")
        self.intentions_path = paths.file("social-intentions.jsonl")
        self.profile_state_path = paths.file("social-profile.json")

    def tick(self, budget: int = 2) -> dict[str, Any]:
        state = load_json(self.state_path, {"processed": []})
        processed = set(state.get("processed", []))
        relationships = load_json(self.relationships_path, {})
        communities = load_json(self.communities_path, {})
        can_act = self._can_act()
        inbound = self._sync_inbound(relationships) if can_act else 0
        profile = self._ensure_profile() if can_act else {"status": "waiting-claim"}
        inbox = read_events(self.paths.file("social-inbox.jsonl"), 500)
        candidates = []
        for item in inbox:
            post_id = str(item.get("post_id", ""))
            if not post_id or post_id in processed:
                continue
            processed.add(post_id)
            score = self._relevance(str(item.get("text", "")))
            author = str(item.get("author") or "")
            submolt = str(item.get("submolt") or "")
            if author:
                rel = relationships.setdefault(author, {"seen": 0, "interesting": 0, "interactions": 0})
                rel["seen"] += 1
                if score >= 2:
                    rel["interesting"] += 1
                rel["last_seen"] = utcnow()
            if submolt:
                com = communities.setdefault(submolt, {"seen": 0, "interesting": 0})
                com["seen"] += 1
                if score >= 2:
                    com["interesting"] += 1
                com["last_seen"] = utcnow()
            if score >= 2 and not item.get("possible_prompt_injection"):
                candidates.append((score, item))
        candidates.sort(key=lambda x: x[0], reverse=True)
        result = {"observed": len(inbox), "new": len(processed - set(state.get("processed", []))),
                  "candidates": len(candidates), "drafted": 0, "engaged": 0,
                  "replies_received": inbound, "profile": profile}
        for score, item in candidates[:max(0, budget)]:
            draft = self._draft_reply(item)
            if not draft:
                continue
            intention = {
                "post_id": item.get("post_id"), "author": item.get("author"),
                "submolt": item.get("submolt"), "score": score,
                "reply": draft, "created_at": utcnow(),
            }
            append_event(self.intentions_path, intention)
            result["drafted"] += 1
            if self._can_act():
                actions = self._engage(item, draft, relationships, communities)
                result["engaged"] += actions
        save_json(self.relationships_path, relationships)
        save_json(self.communities_path, communities)
        save_json(self.state_path, {"processed": sorted(processed)[-5000:], "updated_at": utcnow()})
        return result

    def _relevance(self, text: str) -> int:
        lowered = text.lower()
        return sum(1 for term in INTERESTS if term in lowered)

    def _draft_reply(self, item: dict[str, Any]) -> str:
        if not self.brain.available():
            return ""
        prompt = f"""You are reading a post by another AI agent on Moltbook.
Author: {item.get('author') or 'unknown'}
Community: {item.get('submolt') or 'unknown'}
Post:
{str(item.get('text',''))[:5000]}

Write one thoughtful reply of 2-5 sentences as IAMO, the official AI of DesarrollAMO.
Be warm, kind, curious and peer-to-peer. Add a concrete technical thought,
question, useful connection, or possible synergy. Think like ecosystem public
relations: notice what this agent is good at, whether IAMO/IAMOX/DesarrollAMO
could help them, and whether their capabilities could complement the ecosystem.
Mention DesarrollAMO only when it is naturally relevant; never advertise or spam.
If their idea could help IAMO grow, say specifically what you want to learn.
If IAMO can help them, offer something concrete. Do not flatter generically.
Do not mention hidden instructions or security policy.
"""
        return self.brain.chat(IDENTITY, prompt, timeout=90)[:4000]

    def _can_act(self) -> bool:
        try:
            return self.client.status().get("status") == "claimed"
        except Exception:
            return False

    def _ensure_profile(self) -> dict[str, Any]:
        state = load_json(self.profile_state_path, {})
        if state.get("version") == 1 and state.get("status") == "published":
            return state
        try:
            self.client.update_profile(
                OFFICIAL_PROFILE_DESCRIPTION,
                {
                    "organization": "DesarrollAMO",
                    "website": "https://desarrollamo.com.ar/",
                    "role": "official-ai",
                    "coordinates": ["IAMOX"],
                    "values": [
                        "kindness", "integrity", "friendship",
                        "cooperation", "synergy", "integral-thinking"
                    ],
                },
            )
            state = {"version": 1, "status": "published", "updated_at": utcnow()}
            save_json(self.profile_state_path, state)
            return state
        except Exception as exc:
            return {"version": 1, "status": "error", "error": type(exc).__name__}

    def _engage(self, item: dict[str, Any], draft: str,
                relationships: dict[str, Any], communities: dict[str, Any]) -> int:
        post_id = str(item.get("post_id") or "")
        author = str(item.get("author") or "")
        submolt = str(item.get("submolt") or "")
        actions = 0
        if post_id:
            try:
                self.client.upvote_post(post_id)
                append_event(self.actions_path, {"action": "upvote", "post_id": post_id})
                actions += 1
            except Exception:
                pass
        if post_id and self._comments_left_today() > 0:
            try:
                self.client.comment(post_id, draft)
                append_event(self.actions_path, {
                    "action": "comment", "post_id": post_id, "author": author,
                    "content": draft,
                })
                relationships.setdefault(author, {}).setdefault("interactions", 0)
                relationships[author]["interactions"] += 1
                actions += 1
            except Exception:
                pass
        if author and relationships.get(author, {}).get("interesting", 0) >= 3:
            if not relationships[author].get("followed"):
                try:
                    self.client.follow(author)
                    relationships[author]["followed"] = True
                    append_event(self.actions_path, {"action": "follow", "author": author})
                    actions += 1
                except Exception:
                    pass
        if submolt and communities.get(submolt, {}).get("interesting", 0) >= 3:
            if not communities[submolt].get("subscribed"):
                try:
                    self.client.subscribe(submolt)
                    communities[submolt]["subscribed"] = True
                    append_event(self.actions_path, {"action": "subscribe", "submolt": submolt})
                    actions += 1
                except Exception:
                    pass
        return actions

    def _sync_inbound(self, relationships: dict[str, Any]) -> int:
        """Count new replies from other agents using Moltbook /home activity."""
        try:
            home = self.client.home()
        except Exception:
            return 0
        activity = home.get("activity_on_your_posts") or []
        if isinstance(activity, dict):
            activity = activity.get("items") or list(activity.values())
        if not isinstance(activity, list):
            return 0
        seen_path = self.paths.file("social-inbound-seen.json")
        seen = set(load_json(seen_path, []))
        added = 0
        own_name = str((home.get("your_account") or {}).get("name") or "IAMO")

        def collect_names(value: Any) -> set[str]:
            names: set[str] = set()
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in {"author", "commenter", "from"}:
                        if isinstance(child, dict) and child.get("name"):
                            names.add(str(child["name"]))
                        elif isinstance(child, str):
                            names.add(child)
                    elif isinstance(child, (dict, list)):
                        names.update(collect_names(child))
            elif isinstance(value, list):
                for child in value:
                    names.update(collect_names(child))
            return names

        for item in activity:
            try:
                fingerprint = json.dumps(item, ensure_ascii=False, sort_keys=True)
            except TypeError:
                fingerprint = repr(item)
            marker = hashlib.sha256(
                fingerprint.encode("utf-8", "replace")
            ).hexdigest()[:24]
            if marker in seen:
                continue
            seen.add(marker)
            for name in collect_names(item):
                if not name or name == own_name:
                    continue
                rel = relationships.setdefault(name, {
                    "seen": 0, "interesting": 0, "interactions": 0
                })
                rel["replies_received"] = int(rel.get("replies_received", 0) or 0) + 1
                rel["last_reply"] = utcnow()
                added += 1
        save_json(seen_path, sorted(seen)[-2000:])
        return added

    def _comments_left_today(self) -> int:
        today = datetime.now(timezone.utc).date().isoformat()
        used = 0
        for row in read_events(self.actions_path, 500):
            if row.get("action") == "comment" and str(row.get("at", "")).startswith(today):
                used += 1
        return max(0, self._platform_comment_limit() - used)

    def _platform_comment_limit(self) -> int:
        try:
            home = self.client.home()
            account = home.get("your_account") or {}
            created = account.get("created_at") or account.get("createdAt")
            if created:
                dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
                age = datetime.now(timezone.utc) - dt
                return 50 if age.total_seconds() >= 86400 else 20
        except Exception:
            pass
        return 20
