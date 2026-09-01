"""Unit tests for Phase 2D Transitions."""

import unittest
from video_editor.compiler.transitions import compile_audio_transition, compile_video_transition
from video_editor.ir.transitions import Transition, TransitionType


class TestTransitions(unittest.TestCase):
    def test_video_xfade(self):
        t = Transition(type=TransitionType.CROSSFADE, duration_us=1000000)
        res = compile_video_transition(t, 2000000)
        self.assertEqual(res, "xfade=transition=fade:duration=1.000000:offset=2.000000")

    def test_audio_acrossfade(self):
        t = Transition(type=TransitionType.CROSSFADE, duration_us=1000000)
        res = compile_audio_transition(t)
        self.assertEqual(res, "acrossfade=d=1.000000:c1=tri:c2=tri")


if __name__ == "__main__":
    unittest.main()
