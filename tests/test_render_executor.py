"""Unit tests for FFmpegRenderExecutor."""

import unittest
from video_editor.runtime.executor import FFmpegRenderExecutor


class TestRenderExecutor(unittest.TestCase):
    def test_executor_instantiation(self):
        executor = FFmpegRenderExecutor(timeout_sec=10.0)
        self.assertEqual(executor.timeout_sec, 10.0)


if __name__ == "__main__":
    unittest.main()
