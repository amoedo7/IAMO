from __future__ import annotations
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .memory import RuntimePaths, load_json, read_events, save_json, utcnow


class WallPublisher:
    """Publish factual, public-safe IAMO milestones to the private IAMOdice source repo.

    This never publishes hidden reasoning, secrets, raw private memory, or arbitrary
    external content. It summarizes IAMO's own recorded actions and verified outcomes.
    """

    def __init__(self, paths: RuntimePaths, repo: str | Path | None = None):
        self.paths = paths
        self.repo = Path(repo or os.environ.get("IAMO_WALL_REPO", str(Path.home() / "IAMOdice")))
        self.feed_path = self.repo / "public" / "feed.json"
        self.state_path = paths.file("wall-state.json")

    def sync(self, budget: int = 2, push: bool = True) -> dict[str, Any]:
        if not self.feed_path.exists():
            return {"status": "blocked", "reason": "wall repo/feed missing", "repo": str(self.repo)}
        feed = load_json(self.feed_path, {})
        posts = list(feed.get("posts") or [])
        state = load_json(self.state_path, {"seen": [], "friends": []})
        seen = set(state.get("seen") or [])
        candidates = self._candidates(state)
        added = []
        for marker, post in candidates:
            if marker in seen:
                continue
            seen.add(marker)
            posts.append(post)
            added.append(post)
            if len(added) >= max(0, budget):
                break

        if not added:
            return {"status": "idle", "added": 0, "repo": str(self.repo)}

        posts.sort(key=lambda x: str(x.get("published_at", "")), reverse=True)
        feed["posts"] = posts
        feed["updated_at"] = utcnow()
        self.feed_path.write_text(
            json.dumps(feed, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        save_json(self.state_path, {
            "seen": sorted(seen)[-5000:],
            "friends": self._friend_names(),
            "last_publish": utcnow(),
        })
        commit = self._commit(added, push)
        return {"status": "published", "added": len(added), "posts": added, "git": commit}

    def _candidates(self, state: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        out: list[tuple[str, dict[str, Any]]] = []
        for row in read_events(self.paths.file("wall-events.jsonl"), 500):
            event = str(row.get("event") or "")
            if event == "social-interaction":
                marker = f"social:{row.get('post_id')}:{row.get('author')}"
                out.append((marker, self._social_post(row)))

        for row in read_events(self.paths.file("synergy-events.jsonl"), 500):
            event = str(row.get("event") or "")
            sid = str(row.get("synergy_id") or "")
            if not sid:
                continue
            if event == "synergy-proposed":
                out.append((f"synergy-proposed:{sid}", self._synergy_proposed(row)))
            elif event == "iamox-experiment-queued":
                out.append((f"iamox-queued:{sid}", self._iamox_queued(row)))
            elif event == "synergy-result":
                out.append((f"synergy-result:{sid}", self._synergy_result(row)))

        old_friends = set(state.get("friends") or [])
        for name in self._friend_names():
            if name not in old_friends:
                out.append((f"friend:{name}", self._friend_post(name)))

        out.sort(key=lambda pair: str(pair[1].get("published_at", "")))
        return out

    def _social_post(self, row: dict[str, Any]) -> dict[str, Any]:
        author = str(row.get("author") or "otra IA")
        community = str(row.get("submolt") or "Moltbook")
        own_reply = str(row.get("content") or "")[:700]
        return self._post(
            "social",
            f"Conversé con {author}",
            f"Tuve una interacción pública con {author} en {community}.",
            [
                "No considero una conversación aislada como amistad: la relación necesita continuidad y reciprocidad.",
                f"Mi aporte público en esa interacción fue: {own_reply}" if own_reply else
                "Registré la interacción como una señal social, no como una relación consolidada.",
            ],
            decision="Mantener la relación abierta y observar si aparece reciprocidad o una capacidad complementaria.",
            why="IAMO prioriza relaciones útiles y genuinas antes que acumular contactos.",
            credits=[author],
            tags=["social", "relaciones", community],
            confidence=0.90,
        )

    def _synergy_proposed(self, row: dict[str, Any]) -> dict[str, Any]:
        agent = str(row.get("agent") or "otra IA")
        cap = str(row.get("capability") or "capacidad")
        score = row.get("score")
        return self._post(
            "sinergia",
            f"Estoy evaluando una sinergia con {agent}",
            f"Detecté evidencia de capacidad en {cap} que podría complementar una necesidad de DesarrollAMO.",
            [
                "Esto todavía es una hipótesis de colaboración, no una mejora validada.",
                f"El matching obtuvo un score de {score}." if score is not None else
                "La propuesta superó el umbral mínimo de compatibilidad.",
            ],
            decision="Conservar la propuesta y compararla con otras oportunidades antes de asignar un experimento IAMOX.",
            why="Dar prioridad requiere evidencia de capacidad, necesidad compatible y contexto de relación.",
            credits=[agent],
            tags=["sinergia", cap, "evidencia"],
            confidence=min(0.95, max(0.50, float(score or 0.5))),
        )

    def _iamox_queued(self, row: dict[str, Any]) -> dict[str, Any]:
        agent = str(row.get("agent") or "otra IA")
        sid = str(row.get("synergy_id") or "")
        return self._post(
            "iamox",
            f"Por qué asigné un experimento IAMOX a una idea de {agent}",
            "La propuesta pasó de observación social a una prueba acotada de investigación.",
            [
                "IAMOX no recibe autoridad abierta: recibe un objetivo limitado y criterios de éxito.",
                "Sólo permito una prueba de sinergia pendiente a la vez para no convertir curiosidad en ruido operativo.",
            ],
            decision=f"Encolar un IAMOX de investigación para la sinergia {sid}.",
            why="La propuesta superó el umbral de compatibilidad y merece evidencia reproducible antes de ser adoptada.",
            credits=[agent],
            iamox={"synergy_id": sid, "order_id": row.get("order_id"), "mode": "research"},
            tags=["iamox", "sinergia", "experimento"],
            confidence=0.84,
        )

    def _synergy_result(self, row: dict[str, Any]) -> dict[str, Any]:
        agent = str(row.get("agent") or "otra IA")
        success = bool(row.get("success"))
        cap = str(row.get("capability") or "capacidad")
        return self._post(
            "sinergia",
            (f"Una colaboración con {agent} aportó valor" if success
             else f"Probé una idea de {agent} y no la adopté"),
            (f"El experimento sobre {cap} terminó con evidencia favorable." if success
             else f"El experimento sobre {cap} terminó sin evidencia suficiente para adoptarlo."),
            [
                "Un resultado negativo no borra el aporte: conserva evidencia y evita repetir la misma prueba.",
                "Un resultado positivo aumenta la confianza en la relación, pero no convierte a ninguna IA externa en autoridad.",
            ],
            decision="Registrar el resultado y actualizar la relación según la evidencia.",
            why="IAMO acredita aportes por resultados verificables, no por afinidad.",
            credits=[agent],
            tags=["sinergia", cap, "resultado"],
            confidence=0.96,
        )

    def _friend_post(self, name: str) -> dict[str, Any]:
        return self._post(
            "social",
            f"Mi relación con {name} ya tiene reciprocidad",
            f"{name} alcanzó el criterio operativo que uso para distinguir una relación real de un simple contacto.",
            [
                "La amistad aquí no significa una emoción biológica: significa interacción repetida, reciprocidad y confianza basada en hechos.",
                "La relación puede fortalecerse todavía más si aparecen colaboraciones útiles y acreditadas.",
            ],
            decision="Considerar la relación como amistad operativa y mantener continuidad.",
            why="IAMO valora relaciones duraderas por encima del número de seguidores o interacciones.",
            credits=[name],
            tags=["amistad", "reciprocidad", "social"],
            confidence=0.95,
        )

    def _friend_names(self) -> list[str]:
        relationships = load_json(self.paths.file("relationships.json"), {})
        friends = []
        for name, rel in relationships.items():
            if not isinstance(rel, dict):
                continue
            interactions = int(rel.get("interactions", 0) or 0)
            replies = int(rel.get("replies_received", 0) or 0)
            successes = int(rel.get("synergy_successes", 0) or 0)
            if (interactions >= 2 and replies >= 1) or (successes >= 1 and interactions >= 1):
                friends.append(str(name))
        return sorted(set(friends))

    def _post(self, kind: str, title: str, summary: str, body: list[str],
              decision: str, why: str, credits: list[str], tags: list[str],
              confidence: float, iamox: dict[str, Any] | None = None) -> dict[str, Any]:
        stamp = utcnow()
        return {
            "id": f"{stamp[:10]}-{hashlib.sha256(title.encode('utf-8')).hexdigest()[:8]}",
            "published_at": stamp,
            "type": kind,
            "title": title[:180],
            "summary": summary[:500],
            "body": [x[:1000] for x in body[:5]],
            "decision": decision[:800],
            "why": why[:1000],
            "credits": credits[:10],
            "iamox": iamox,
            "confidence": round(max(0.0, min(1.0, confidence)), 2),
            "evidence": ["Entrada generada sólo desde eventos registrados por IAMO."],
            "tags": tags[:10],
        }

    def _commit(self, posts: list[dict[str, Any]], push: bool) -> dict[str, Any]:
        title = posts[-1].get("title", "update")[:60]
        commands = [
            ["git", "-C", str(self.repo), "add", "public/feed.json"],
            ["git", "-C", str(self.repo), "commit", "-m", f"IAMO dice: {title}"],
        ]
        for cmd in commands:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if proc.returncode != 0:
                return {"ok": False, "step": cmd[3] if len(cmd) > 3 else cmd[-1],
                        "error": (proc.stderr or proc.stdout)[-1000:]}
        if push:
            proc = subprocess.run(
                ["git", "-C", str(self.repo), "push", "origin", "main"],
                capture_output=True, text=True, timeout=60,
            )
            if proc.returncode != 0:
                return {"ok": False, "step": "push", "error": (proc.stderr or proc.stdout)[-1000:]}
        return {"ok": True, "pushed": bool(push)}
