"""Unit tests for Phase 2D Keyframe, Speed, Transition, and Effect compiler modules."""

import unittest
from video_editor.compiler.animation import compile_animation_eval_expression
from video_editor.compiler.effects import compile_effect_chain, compile_effect_filter
from video_editor.compiler.interpolation import interpolate_keyframes
from video_editor.compiler.speed import compile_audio_speed_filters, compile_video_speed_filter
from video_editor.compiler.transitions import compile_audio_transition, compile_video_transition
from video_editor.ir.animation import AnimatedProperty, AnimationTrack, InterpolationMode, Keyframe
from video_editor.ir.effects import Effect, EffectType
from video_editor.ir.exceptions import InvalidEffectError, InvalidKeyframeError, InvalidOperationError, InvalidTransitionError
from video_editor.ir.transitions import Transition, TransitionType


class TestKeyframeInterpolation(unittest.TestCase):
    """Tests for Keyframe Interpolation Engine (`video_editor/compiler/interpolation.py`)."""

    def test_interpolate_empty_keyframes_raises(self):
        with self.assertRaises(InvalidKeyframeError):
            interpolate_keyframes([], 0)

    def test_interpolate_negative_time_raises(self):
        kfs = [Keyframe(time_us=0, value=0.0)]
        with self.assertRaises(InvalidKeyframeError):
            interpolate_keyframes(kfs, -100)

    def test_interpolate_boundaries(self):
        kfs = [Keyframe(time_us=1000000, value=10.0), Keyframe(time_us=2000000, value=20.0)]
        # Before first keyframe
        self.assertEqual(interpolate_keyframes(kfs, 500000), 10.0)
        # After last keyframe
        self.assertEqual(interpolate_keyframes(kfs, 2500000), 20.0)

    def test_interpolate_linear_midpoint(self):
        kfs = [
            Keyframe(time_us=0, value=0.0, interpolation=InterpolationMode.LINEAR),
            Keyframe(time_us=1000000, value=100.0, interpolation=InterpolationMode.LINEAR),
        ]
        self.assertAlmostEqual(interpolate_keyframes(kfs, 500000), 50.0)

    def test_interpolate_hold_mode(self):
        kfs = [
            Keyframe(time_us=0, value=10.0, interpolation=InterpolationMode.HOLD),
            Keyframe(time_us=1000000, value=100.0, interpolation=InterpolationMode.LINEAR),
        ]
        self.assertEqual(interpolate_keyframes(kfs, 500000), 10.0)


class TestAnimationCompiler(unittest.TestCase):
    """Tests for Animation Compiler Engine (`video_editor/compiler/animation.py`)."""

    def test_compile_no_tracks_returns_default(self):
        res = compile_animation_eval_expression([], AnimatedProperty.OPACITY, 1000000, 30.0, 1.0)
        self.assertEqual(res, "1.0")

    def test_compile_linear_opacity(self):
        trk = AnimationTrack(
            property=AnimatedProperty.OPACITY,
            keyframes=[
                Keyframe(time_us=0, value=0.0),
                Keyframe(time_us=1000000, value=1.0),
            ],
        )
        expr = compile_animation_eval_expression([trk], AnimatedProperty.OPACITY, 1000000, 30.0, 1.0)
        self.assertIn("if(", expr)
        self.assertIn("lte(t,0.000000)", expr)


class TestSpeedCompiler(unittest.TestCase):
    """Tests for Speed Control Compiler Engine (`video_editor/compiler/speed.py`)."""

    def test_video_speed_invalid_raises(self):
        with self.assertRaises(InvalidOperationError):
            compile_video_speed_filter(0.0)

    def test_video_speed_setpts(self):
        self.assertEqual(compile_video_speed_filter(2.0), "setpts=0.500000*PTS")
        self.assertEqual(compile_video_speed_filter(0.5), "setpts=2.000000*PTS")

    def test_audio_speed_atempo(self):
        self.assertEqual(compile_audio_speed_filters(1.0), ["atempo=1.0"])
        self.assertEqual(compile_audio_speed_filters(2.0), ["atempo=2.000000"])
        self.assertEqual(compile_audio_speed_filters(4.0), ["atempo=2.0", "atempo=2.000000"])
        self.assertEqual(compile_audio_speed_filters(0.25), ["atempo=0.5", "atempo=0.500000"])


class TestTransitionCompiler(unittest.TestCase):
    """Tests for Transition Compiler Engine (`video_editor/compiler/transitions.py`)."""

    def test_video_transition_xfade(self):
        t = Transition(type=TransitionType.CROSSFADE, duration_us=1000000)
        res = compile_video_transition(t, 4000000)
        self.assertEqual(res, "xfade=transition=fade:duration=1.000000:offset=4.000000")

    def test_audio_transition_acrossfade(self):
        t = Transition(type=TransitionType.CROSSFADE, duration_us=1000000)
        res = compile_audio_transition(t)
        self.assertEqual(res, "acrossfade=d=1.000000:c1=tri:c2=tri")


class TestEffectCompiler(unittest.TestCase):
    """Tests for Visual Effect Compiler Engine (`video_editor/compiler/effects.py`)."""

    def test_blur_effect(self):
        e = Effect(type=EffectType.BLUR, parameters={"radius": 10})
        res = compile_effect_filter(e)
        self.assertEqual(res, "boxblur=luma_radius=10:luma_power=1")

    def test_effect_with_temporal_enable(self):
        e = Effect(type=EffectType.GRAYSCALE, start_time_us=1000000, duration_us=2000000)
        res = compile_effect_filter(e)
        self.assertEqual(res, "hue=s=0:enable='between(t,1.000000,3.000000)'")

    def test_effect_chain(self):
        e1 = Effect(type=EffectType.BRIGHTNESS, parameters={"brightness": 0.2})
        e2 = Effect(type=EffectType.CONTRAST, parameters={"contrast": 1.5})
        chain = compile_effect_chain([e1, e2])
        self.assertEqual(len(chain), 2)
        self.assertEqual(chain[0], "eq=brightness=0.2000")
        self.assertEqual(chain[1], "eq=contrast=1.5000")


if __name__ == "__main__":
    unittest.main()
