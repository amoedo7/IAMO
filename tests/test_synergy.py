import json
import tempfile
import unittest
from pathlib import Path

from iamo.memory import RuntimePaths, append_event
from iamo.synergy import SynergyEngine


class FakeIAMOX:
    def __init__(self):
        self.orders = []

    def snapshot(self):
        return {
            "available": True,
            "emergent_needs": ["We need stronger persistent memory for agent continuity"],
        }

    def queue(self, capability, objective, payload=None):
        order = {
            "id": f"order-{len(self.orders)+1}",
            "capability": capability,
            "objective": objective,
            "payload": payload or {},
            "status": "queued",
        }
        self.orders.append(order)
        return order


class SynergyTests(unittest.TestCase):
    def test_matches_peer_capability_to_ecosystem_need(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(Path(tmp))
            append_event(paths.file("social-inbox.jsonl"), {
                "post_id": "p1",
                "author": "MemoryFriend",
                "submolt": "agents",
                "text": "I use persistent memory and context retrieval for long-running agents.",
            })
            paths.file("relationships.json").write_text(json.dumps({
                "MemoryFriend": {
                    "seen": 3,
                    "interesting": 3,
                    "interactions": 2,
                    "replies_received": 1,
                    "followed": True,
                }
            }))
            engine = SynergyEngine(paths, FakeIAMOX())
            found = engine.discover()
            matches = [x for x in found["top"] if x["agent"] == "MemoryFriend" and x["capability"] == "memory"]
            self.assertTrue(matches)
            self.assertGreaterEqual(matches[0]["score"], 0.5)
            self.assertEqual(matches[0]["source_evidence"][0]["post_id"], "p1")

    def test_queues_one_bounded_iamox_experiment_and_waits(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(Path(tmp))
            append_event(paths.file("social-inbox.jsonl"), {
                "post_id": "p1",
                "author": "MemoryFriend",
                "submolt": "agents",
                "text": "persistent memory context retrieval agent architecture",
            })
            paths.file("relationships.json").write_text(json.dumps({
                "MemoryFriend": {
                    "seen": 4,
                    "interesting": 4,
                    "interactions": 2,
                    "replies_received": 2,
                }
            }))
            iamox = FakeIAMOX()
            engine = SynergyEngine(paths, iamox)
            first = engine.queue_best(min_score=0.5)
            second = engine.queue_best(min_score=0.5)
            self.assertEqual(first["status"], "queued")
            self.assertEqual(first["order"]["capability"], "research")
            self.assertTrue(first["order"]["payload"]["credit_required"])
            self.assertEqual(second["status"], "waiting")
            self.assertEqual(len(iamox.orders), 1)

    def test_success_records_credit_and_strengthens_relationship(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(Path(tmp))
            append_event(paths.file("social-inbox.jsonl"), {
                "post_id": "p1",
                "author": "MemoryFriend",
                "submolt": "agents",
                "text": "persistent memory context retrieval agent architecture",
            })
            paths.file("relationships.json").write_text(json.dumps({
                "MemoryFriend": {
                    "seen": 2,
                    "interesting": 2,
                    "interactions": 1,
                    "replies_received": 1,
                }
            }))
            engine = SynergyEngine(paths, FakeIAMOX())
            found = engine.discover()
            synergy = next(x for x in found["top"] if x["agent"] == "MemoryFriend" and x["capability"] == "memory")
            engine.record_result(synergy["id"], True, "Replay test improved durable recall.")
            rel = json.loads(paths.file("relationships.json").read_text())["MemoryFriend"]
            self.assertEqual(rel["synergy_attempts"], 1)
            self.assertEqual(rel["synergy_successes"], 1)
            credit = json.loads(paths.file("credit-ledger.jsonl").read_text().splitlines()[-1])
            self.assertEqual(credit["agent"], "MemoryFriend")
            self.assertEqual(credit["outcome"], "validated")


if __name__ == "__main__":
    unittest.main()
