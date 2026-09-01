"""Unit tests for TimelineCompiler and RenderPlanner output determinism."""

from video_editor.compiler.compiler import TimelineCompiler
from video_editor.compiler.planner import RenderPlanner
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.models import Asset, Clip, Track, VideoProject


def test_compiler_and_planner_determinism(tmp_path):
    f1 = tmp_path / "v1.mp4"
    f2 = tmp_path / "v2.mp4"
    f1.write_text("data1")
    f2.write_text("data2")

    project = VideoProject(name="Deterministic Test Project")
    a1 = Asset(type=AssetType.VIDEO, path=str(f1), duration_us=10_000_000)
    a2 = Asset(type=AssetType.VIDEO, path=str(f2), duration_us=10_000_000)
    project.assets[a1.id] = a1
    project.assets[a2.id] = a2

    track = Track(name="V1", type=TrackType.VIDEO, index=0)
    c1 = Clip(
        asset_id=a1.id,
        timeline_start_us=0,
        timeline_duration_us=3_000_000,
        source_start_us=0,
        source_duration_us=3_000_000,
    )
    c2 = Clip(
        asset_id=a2.id,
        timeline_start_us=3_000_000,
        timeline_duration_us=4_000_000,
        source_start_us=0,
        source_duration_us=4_000_000,
    )
    track.clips.extend([c1, c2])
    project.tracks.append(track)

    compiler = TimelineCompiler()
    planner = RenderPlanner()

    # Compile and plan 10 times in a row
    plans = [compiler.compile(project) for _ in range(10)]
    cmds = [planner.plan_to_command(p, "/output.mp4").to_display_string() for p in plans]

    # Verify 100% string and structure identity
    first_cmd = cmds[0]
    for cmd in cmds[1:]:
        assert cmd == first_cmd
