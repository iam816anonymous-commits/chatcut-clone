"""End-to-End Integration Test for Phase 2D Video Editing Pipeline."""

import os
import shutil
import unittest
from video_editor.compiler.compiler import TimelineCompiler
from video_editor.compiler.planner import RenderPlanner
from video_editor.ir.animation import AnimatedProperty, AnimationTrack, Keyframe
from video_editor.ir.effects import Effect, EffectType
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.models import Asset, Clip, ProjectSettings, Track, VideoProject
from video_editor.ir.transitions import Transition, TransitionType


class TestEndToEndPhase2D(unittest.TestCase):
    def test_compile_phase2d_project(self):
        project = VideoProject(
            id="proj_phase2d",
            name="Phase 2D Integration Test",
            settings=ProjectSettings(width=1080, height=1920, fps=30.0),
            assets={
                "ast1": Asset(id="ast1", type=AssetType.VIDEO, path="/tmp/fake_video.mp4", duration_us=10_000_000)
            },
            tracks=[
                Track(
                    id="trk1",
                    name="Video Main",
                    type=TrackType.VIDEO,
                    index=0,
                    clips=[
                        Clip(
                            id="clip1",
                            asset_id="ast1",
                            timeline_start_us=0,
                            timeline_duration_us=5_000_000,
                            source_start_us=0,
                            source_duration_us=5_000_000,
                            speed=2.0,
                            transition_in=Transition(type=TransitionType.CROSSFADE, duration_us=1_000_000),
                            effects=[Effect(type=EffectType.BLUR, parameters={"radius": 5})],
                            animation_tracks=[
                                AnimationTrack(
                                    property=AnimatedProperty.OPACITY,
                                    keyframes=[Keyframe(time_us=0, value=0.0), Keyframe(time_us=1_000_000, value=1.0)]
                                )
                            ]
                        )
                    ]
                )
            ]
        )

        compiler = TimelineCompiler()
        plan = compiler.compile(project)

        self.assertEqual(plan.total_duration_us, 5_000_000)
        self.assertEqual(len(plan.tracks), 1)

        planner = RenderPlanner()
        cmd = planner.plan_to_command(plan, "/tmp/output.mp4")
        self.assertIsNotNone(cmd)
        self.assertIn("-filter_complex", cmd.arguments)


if __name__ == "__main__":
    unittest.main()
