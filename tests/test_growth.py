import json
import tempfile
import unittest
from pathlib import Path
from iamo.growth import GrowthLab
from iamo.memory import RuntimePaths, append_event

class FakeBrain:
    def available(self):
        return True
    def json_task(self, system, user, **kwargs):
        return {
            "useful": True,
            "title": "Persist agent memory",
            "insight": "Keep durable state",
            "evidence_quote": "persistent memory",
            "target_files": ["memory.py"],
            "implementation": "Add a compact index.",
            "tests": ["test restart"],
            "risks": ["stale index"],
            "credit": "OtherAI",
        }

class GrowthTests(unittest.TestCase):
    def test_social_idea_becomes_attributed_proposal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = RuntimePaths(root / "state")
            repo = root / "repo"
            (repo / "iamo").mkdir(parents=True)
            (repo / "iamo" / "memory.py").write_text("VALUE = 1\n")
            append_event(paths.file("social-inbox.jsonl"), {
                "post_id": "p1", "author": "OtherAI", "submolt": "agents",
                "text": "I use persistent memory for agent context and code.",
            })
            lab = GrowthLab(paths, FakeBrain(), repo)
            result = lab.harvest(1)
            self.assertEqual(result["proposed"], 1)
            row = json.loads(paths.file("growth-proposals.jsonl").read_text().splitlines()[0])
            self.assertEqual(row["source_author"], "OtherAI")
            self.assertEqual(row["proposal"]["target_files"], ["memory.py"])

if __name__ == "__main__":
    unittest.main()
