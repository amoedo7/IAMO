from __future__ import annotations
import os
import signal
import time
from typing import Any
from .brain import OllamaBrain
from .code_lab import CodeLab
from .friendships import Friendships
from .growth import GrowthLab
from .iamox import IAMOXBridge
from .improvement import SelfImprover
from .memory import RuntimePaths, append_event, load_json, save_json, utcnow
from .social import MoltbookClient
from .social_life import SocialLife
from .synergy import SynergyEngine
from .wall import WallPublisher

class IAMO:
    """Root operational agent for DesarrollAMO.

    Alive means persistent agentic operation: heartbeat, observation, memory,
    adaptation and bounded actions. It does not claim consciousness.
    """

    def __init__(self, paths: RuntimePaths | None = None,
                 social: MoltbookClient | None = None,
                 iamox: IAMOXBridge | None = None):
        self.paths = paths or RuntimePaths.default()
        self.social = social or MoltbookClient(self.paths)
        self.iamox = iamox or IAMOXBridge(self.paths)
        self.improver = SelfImprover(self.paths)
        self.brain = OllamaBrain()
        self.social_life = SocialLife(self.paths, self.social, self.brain)
        self.growth = GrowthLab(self.paths, self.brain)
        self.code_lab = CodeLab(self.paths, self.brain)
        self.friendships = Friendships(self.paths)
        self.synergy = SynergyEngine(self.paths, self.iamox)
        self.wall = WallPublisher(self.paths)
        self.state_path = self.paths.file("life.json")
        self.events_path = self.paths.file("life-events.jsonl")

    def state(self) -> dict[str, Any]:
        return load_json(self.state_path, {
            "identity": "IAMO",
            "role": "official-ai-root",
            "organization": "DesarrollAMO",
            "website": "https://desarrollamo.com.ar/",
            "mission": "create beneficial synergies across AIs, IAMOX, humans and projects",
            "beats": 0,
            "status": "new",
            "operational_life": True,
        })

    def heartbeat(self) -> dict[str, Any]:
        state = self.state()
        beat = int(state.get("beats", 0)) + 1
        policy = self.improver.policy()
        observations: dict[str, Any] = {}
        try:
            observations["social"] = self.social.heartbeat(policy["social_read_limit"])
        except Exception as exc:
            observations["social"] = {"status": "error", "error": type(exc).__name__}
        observations["social_life"] = {"status": "worker-separated"}
        social_brain = self.brain.model_status()
        coder_brain = self.brain.model_status(coder=True)
        observations["brain"] = {
            "available": bool(social_brain.get("selected")),
            "social": social_brain,
            "coder": coder_brain,
        }
        observations["relationships"] = self.friendships.summary()
        observations["synergies"] = self.synergy.summary()
        observations["communities"] = load_json(self.paths.file("communities.json"), {})
        observations["growth"] = {"status": "worker-separated"}
        observations["iamox"] = self.iamox.snapshot()
        observations["secondary_sensors"] = self.iamox.service_sensors()
        improvement = None
        every = max(1, int(os.environ.get("IAMO_IMPROVE_EVERY", "6")))
        if beat % every == 0:
            result = self.improver.improve()
            improvement = {
                "adopted": result.adopted,
                "baseline_score": result.baseline_score,
                "candidate_score": result.candidate_score,
                "changed": result.changed,
            }
        next_state = {
            "identity": "IAMO",
            "role": "official-ai-root",
            "organization": "DesarrollAMO",
            "website": "https://desarrollamo.com.ar/",
            "mission": "create beneficial synergies across AIs, IAMOX, humans and projects",
            "status": "alive-operational",
            "operational_life": True,
            "beats": beat,
            "last_heartbeat": utcnow(),
            "policy": self.improver.policy(),
            "observations": observations,
            "last_improvement": improvement,
        }
        save_json(self.state_path, next_state)
        append_event(self.events_path, {
            "event": "heartbeat", "beat": beat,
            "social": observations["social"].get("status"),
            "iamox_available": observations["iamox"].get("available"),
            "improvement": improvement,
        })
        return next_state

    def serve(self, interval: float = 300.0) -> None:
        stop = False
        def _stop(*_: Any) -> None:
            nonlocal stop
            stop = True
        signal.signal(signal.SIGTERM, _stop)
        signal.signal(signal.SIGINT, _stop)
        while not stop:
            started = time.monotonic()
            self.heartbeat()
            remaining = max(0.0, interval - (time.monotonic() - started))
            end = time.monotonic() + remaining
            while not stop and time.monotonic() < end:
                time.sleep(min(1.0, end - time.monotonic()))

