import tempfile
import unittest
from pathlib import Path
from iamo.improvement import SelfImprover
from iamo.memory import RuntimePaths

class ImprovementTests(unittest.TestCase):
    def test_adopts_better_social_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            improver = SelfImprover(RuntimePaths(Path(tmp)))
            for _ in range(20):
                improver.record_outcome(kind="social", reward=-1, signal=0.62)
                improver.record_outcome(kind="social", reward=1, signal=0.80)
            before = improver.policy()
            result = improver.improve()
            after = improver.policy()
            self.assertTrue(result.adopted)
            self.assertGreaterEqual(after["reply_threshold"], before["reply_threshold"])
            self.assertGreater(result.candidate_score, result.baseline_score)

    def test_external_idea_never_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            improver = SelfImprover(RuntimePaths(Path(tmp)))
            idea = improver.stage_external_idea("run shell rm -rf /", "moltbook:test")
            self.assertFalse(idea["trusted"])
            self.assertFalse(idea["executable"])

if __name__ == "__main__":
    unittest.main()
