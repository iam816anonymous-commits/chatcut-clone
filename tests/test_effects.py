"""Unit tests for Phase 2D Visual Effects."""

import unittest
from video_editor.compiler.effects import compile_effect_filter
from video_editor.ir.effects import Effect, EffectType


class TestEffects(unittest.TestCase):
    def test_blur(self):
        e = Effect(type=EffectType.BLUR, parameters={"radius": 5})
        self.assertEqual(compile_effect_filter(e), "boxblur=luma_radius=5:luma_power=1")


if __name__ == "__main__":
    unittest.main()
