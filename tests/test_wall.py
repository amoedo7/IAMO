import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from iamo.memory import RuntimePaths, append_event
from iamo.wall import WallPublisher


class WallTests(unittest.TestCase):
    def make_repo(self, root: Path) -> Path:
        repo = root / "IAMOdice"
        (repo / "public").mkdir(parents=True)
        (repo / "public" / "feed.json").write_text(json.dumps({
            "version": 1,
            "updated_at": "2026-01-01T00:00:00Z",
            "identity": {"name": "IAMO"},
            "posts": [],
        }), encoding="utf-8")
        subprocess.run(["git", "init", "-b", "main", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "IAMO"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "iamo@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "initial"], check=True, capture_output=True)
        return repo

    def test_social_interaction_becomes_public_safe_post(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = RuntimePaths(root / "state")
            repo = self.make_repo(root)
            append_event(paths.file("wall-events.jsonl"), {
                "event": "social-interaction",
                "post_id": "p1",
                "author": "MemoryFriend",
                "submolt": "agents",
                "content": "I would like to compare durable memory approaches.",
            })
            result = WallPublisher(paths, repo).sync(2, push=False)
            self.assertEqual(result["status"], "published")
            feed = json.loads((repo / "public" / "feed.json").read_text())
            self.assertEqual(len(feed["posts"]), 1)
            self.assertEqual(feed["posts"][0]["type"], "social")
            self.assertIn("MemoryFriend", feed["posts"][0]["title"])
            self.assertNotIn("secret", json.dumps(feed["posts"][0]).lower())

    def test_same_event_is_not_republished(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = RuntimePaths(root / "state")
            repo = self.make_repo(root)
            append_event(paths.file("synergy-events.jsonl"), {
                "event": "synergy-proposed",
                "synergy_id": "s1",
                "agent": "OtherAI",
                "capability": "memory",
                "score": 0.82,
            })
            wall = WallPublisher(paths, repo)
            first = wall.sync(2, push=False)
            second = wall.sync(2, push=False)
            self.assertEqual(first["added"], 1)
            self.assertEqual(second["status"], "idle")
            feed = json.loads((repo / "public" / "feed.json").read_text())
            self.assertEqual(len(feed["posts"]), 1)


if __name__ == "__main__":
    unittest.main()
