import os
import unittest
from unittest.mock import patch

from iamo.brain import OllamaBrain


class BrainTests(unittest.TestCase):
    def test_defaults_prefer_qwen3_8b(self):
        with patch.dict(os.environ, {}, clear=False):
            brain = OllamaBrain("http://127.0.0.1:11434")
        self.assertEqual(brain.social_model, "qwen3:8b")
        self.assertEqual(brain.coder_model, "qwen3:8b")

    def test_model_resolution_prefers_8b_then_4b_then_seed(self):
        brain = OllamaBrain("http://127.0.0.1:11434")

        brain.available_models = lambda: ["qwen3:8b", "qwen3:4b", "qwen3:0.6b"]
        self.assertEqual(brain.resolve_model(), "qwen3:8b")
        self.assertEqual(brain.model_status()["tier"], "full")

        brain.available_models = lambda: ["qwen3:4b", "qwen3:0.6b"]
        self.assertEqual(brain.resolve_model(), "qwen3:4b")
        status = brain.model_status()
        self.assertEqual(status["tier"], "fallback")
        self.assertTrue(status["degraded"])

        brain.available_models = lambda: ["qwen3:0.6b"]
        self.assertEqual(brain.resolve_model(), "qwen3:0.6b")
        self.assertEqual(brain.model_status()["tier"], "seed")

    def test_missing_models_fails_closed(self):
        brain = OllamaBrain("http://127.0.0.1:11434")
        brain.available_models = lambda: []
        with self.assertRaises(RuntimeError):
            brain.resolve_model()


if __name__ == "__main__":
    unittest.main()
