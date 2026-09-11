import tempfile
import unittest
from pathlib import Path
from iamo.core import IAMO
from iamo.iamox import IAMOXBridge
from iamo.memory import RuntimePaths

class FakeSocial:
    def heartbeat(self, limit=20):
        return {"configured": True, "status": "claimed", "feed": {"seen": 0, "added": 0}}

class CoreTests(unittest.TestCase):
    def test_heartbeat_persists_life(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = RuntimePaths(root / "state")
            iamox_root = root / "IAMOX"
            (iamox_root / "state").mkdir(parents=True)
            app = IAMO(paths, social=FakeSocial(), iamox=IAMOXBridge(paths, iamox_root))
            state = app.heartbeat()
            self.assertEqual(state["status"], "alive-operational")
            self.assertEqual(state["beats"], 1)
            self.assertTrue(state["operational_life"])
            self.assertTrue(state["observations"]["iamox"]["available"])
            self.assertTrue((paths.root / "life.json").exists())

if __name__ == "__main__":
    unittest.main()
