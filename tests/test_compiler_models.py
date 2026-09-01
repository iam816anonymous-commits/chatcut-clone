"""Unit tests for RenderPlan domain schemas."""

import pytest
from video_editor.compiler.models import (
    RenderGap,
    RenderInput,
    RenderOutputSettings,
    RenderPlan,
    RenderSegment,
    RenderTrack,
)
from video_editor.ir.enums import TrackType


def test_render_segment_derived_end():
    seg = RenderSegment(
        clip_id="c1",
        asset_id="a1",
        input_index=0,
        timeline_start_us=2_000_000,
        timeline_duration_us=3_000_000,
        source_start_us=1_000_000,
        source_duration_us=3_000_000,
    )
    assert seg.timeline_end_us == 5_000_000


def test_render_gap_derived_end():
    gap = RenderGap(timeline_start_us=5_000_000, timeline_duration_us=2_000_000)
    assert gap.timeline_end_us == 7_000_000


def test_render_plan_properties():
    inp = RenderInput(input_index=0, asset_id="a1", file_path="/media/video.mp4")
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
                timeline_duration_us=4_000_000,
                source_start_us=0,
                source_duration_us=4_000_000,
            )
        ],
    )
    a_track = RenderTrack(
        track_id="t2",
        track_type=TrackType.AUDIO,
        index=1,
        items=[],
    )

    plan = RenderPlan(
        project_id="p1",
        total_duration_us=4_000_000,
        inputs=[inp],
        tracks=[v_track, a_track],
    )

    assert plan.primary_video_track.track_id == "t1"
    assert len(plan.audio_tracks) == 1
    assert plan.audio_tracks[0].track_id == "t2"
