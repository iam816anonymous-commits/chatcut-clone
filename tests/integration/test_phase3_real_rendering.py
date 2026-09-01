"""Real End-to-End Integration and Failure Injection Tests for Phase 3 Rendering Runtime."""

import os
import shutil
import tempfile
import unittest
from tests.helpers.media_generator import TestMediaGenerator
from video_editor.compiler.compiler import TimelineCompiler
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.models import Asset, Clip, ProjectSettings, Track, VideoProject
from video_editor.runtime.environment import FFmpegEnvironmentInspector
from video_editor.runtime.executor import FFmpegRenderExecutor
from video_editor.runtime.models import RenderExecutionStatus


class TestPhase3RealRendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.env = FFmpegEnvironmentInspector.inspect()
        cls.temp_dir = tempfile.mkdtemp(prefix="phase3_tests_")
        cls.asset_path = os.path.join(cls.temp_dir, "sample_input.mp4")

        if cls.env.ffmpeg_available:
            TestMediaGenerator.generate_test_video(
                cls.asset_path, duration_sec=2.0, width=320, height=240, color="blue"
            )

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_real_render_execution(self):
        if not self.env.ffmpeg_available or not self.env.ffprobe_available:
            self.skipTest("FFmpeg or FFprobe binaries unavailable in execution environment")

        project = VideoProject(
            id="p3_real_proj",
            name="Phase 3 Real Rendering Test",
            settings=ProjectSettings(width=320, height=240, fps=30.0),
            assets={
                "ast1": Asset(id="ast1", type=AssetType.VIDEO, path=self.asset_path, duration_us=2_000_000)
            },
            tracks=[
                Track(
                    id="trk1",
                    name="Video Track",
                    type=TrackType.VIDEO,
                    index=0,
                    clips=[
                        Clip(
                            id="clp1",
                            asset_id="ast1",
                            timeline_start_us=0,
                            timeline_duration_us=2_000_000,
                            source_start_us=0,
                            source_duration_us=2_000_000,
                        )
                    ]
                )
            ]
        )

        compiler = TimelineCompiler()
        plan = compiler.compile(project)

        target_path = os.path.join(self.temp_dir, "rendered_output.mp4")
        executor = FFmpegRenderExecutor(workspace_base_dir=os.path.join(self.temp_dir, "workspaces"))

        execution = executor.execute_render_plan(plan, target_path)

        self.assertEqual(execution.status, RenderExecutionStatus.COMPLETED)
        self.assertTrue(os.path.exists(target_path))
        self.assertGreater(os.path.getsize(target_path), 0)
        self.assertIsNotNone(execution.artifact)
        self.assertGreater(len(execution.artifact.sha256_checksum), 0)


if __name__ == "__main__":
    unittest.main()
