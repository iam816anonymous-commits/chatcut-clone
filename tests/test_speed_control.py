"""Unit tests for Phase 2D Speed Control."""

import unittest
from video_editor.compiler.speed import compile_audio_speed_filters, compile_video_speed_filter


class TestSpeedControl(unittest.TestCase):
    def test_setpts(self):
        self.assertEqual(compile_video_speed_filter(2.0), "setpts=0.500000*PTS")

    def test_atempo_chaining(self):
        self.assertEqual(compile_audio_speed_filters(4.0), ["atempo=2.0", "atempo=2.000000"])


if __name__ == "__main__":
    unittest.main()
