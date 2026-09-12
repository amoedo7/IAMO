import json
import tempfile
import unittest
from pathlib import Path
from iamo.friendships import Friendships
from iamo.memory import RuntimePaths

class FriendshipTests(unittest.TestCase):
    def test_friend_requires_repeated_and_reciprocal_contact(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = RuntimePaths(Path(tmp))
            paths.file("relationships.json").write_text(json.dumps({
                "FriendAI": {"interactions": 2, "replies_received": 1, "interesting": 3, "followed": True},
                "KnownAI": {"interactions": 1, "replies_received": 0, "interesting": 4},
            }))
            result = Friendships(paths).summary()
            self.assertEqual(result["friend_count"], 1)
            self.assertEqual(result["friends"][0]["name"], "FriendAI")
            self.assertEqual(result["acquaintance_count"], 1)

if __name__ == "__main__":
    unittest.main()
