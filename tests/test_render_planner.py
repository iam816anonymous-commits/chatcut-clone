"""Unit tests for RenderPlanner command generation."""

from video_editor.compiler.models import (
    RenderGap,
    RenderInput,
    RenderOutputSettings,
    RenderPlan,
    RenderSegment,
    RenderTrack,
)
from video_editor.compiler.planner import RenderPlanner
from video_editor.ir.enums import TrackType


def test_planner_generates_command_with_filter_complex():
    inp = RenderInput(input_index=0, asset_id="a1", file_path="/media/v.mp4")
    v_track = RenderTrack(
        track_id="t1",
        track_type=TrackType.VIDEO,
        index=0,
        items=[
            RenderSegment(
                clip_id="c1",
                asset_id="a1",
                input_index=0,
                timeline_start_us=0,
                timeline_duration_us=2_000_000,
                source_start_us=0,
                source_duration_us=2_000_000,
            ),
            RenderGap(timeline_start_us=2_000_000, timeline_duration_us=1_000_000),
        ],
    )

    plan = RenderPlan(
        project_id="p1",
        total_duration_us=3_000_000,
        output_settings=RenderOutputSettings(width=1080, height=1920, fps=30.0),
        inputs=[inp],
        tracks=[v_track],
    )

    planner = RenderPlanner()
    cmd = planner.plan_to_command(plan, "/out/render.mp4")

    cmd_str = cmd.to_display_string()
    assert "-filter_complex" in cmd_str
    assert "trim=start=0.000000:end=2.000000" in cmd_str
    assert "color=c=black:s=1080x1920:r=30.0:d=1.000000" in cmd_str
    assert "concat=n=2:v=1:a=0" in cmd_str
    assert "/out/render.mp4" in cmd_str
