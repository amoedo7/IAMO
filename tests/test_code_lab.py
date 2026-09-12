import unittest
from iamo.code_lab import CodeLab

class CodeLabTests(unittest.TestCase):
    def test_diff_must_stay_inside_declared_modules(self):
        lab = object.__new__(CodeLab)
        good = "--- a/iamo/memory.py\n+++ b/iamo/memory.py\n@@ -1 +1 @@\n-a=1\n+a=2\n"
        bad = "--- a/deploy/iamo.service\n+++ b/deploy/iamo.service\n@@ -1 +1 @@\n-a\n+b\n"
        self.assertTrue(lab._safe_diff(good, ["memory.py"]))
        self.assertFalse(lab._safe_diff(bad, ["memory.py"]))

if __name__ == "__main__":
    unittest.main()
