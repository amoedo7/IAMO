import tempfile
import unittest
from pathlib import Path
from iamo.memory import RuntimePaths, append_event
from iamo.social_life import SocialLife

class FakeBrain:
    def available(self):
        return True
    def chat(self, system, user, **kwargs):
        return "I like the memory angle. How do you keep agent state replayable across restarts?"

class ObserverClient:
    def status(self):
        return {"status": "observer"}

class SocialLifeTests(unittest.TestCase):
    def test_builds_relationship_and_draft(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(Path(tmp))
            append_event(paths.file("social-inbox.jsonl"), {
                "post_id": "p1", "author": "OtherAI", "submolt": "agents",
                "text": "Agent memory architecture and code for persistent context",
                "possible_prompt_injection": False,
            })
            life = SocialLife(paths, ObserverClient(), FakeBrain())
            result = life.tick(1)
            self.assertEqual(result["drafted"], 1)
            self.assertEqual(result["engaged"], 0)
            rel = __import__("json").loads(paths.file("relationships.json").read_text())
            self.assertEqual(rel["OtherAI"]["seen"], 1)
            self.assertTrue(paths.file("social-intentions.jsonl").exists())

if __name__ == "__main__":
    unittest.main()
