"""Unit tests for TimelineCompiler engine and gap detection."""

import pytest
from video_editor.compiler.compiler import TimelineCompiler
from video_editor.compiler.models import RenderGap, RenderSegment
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.models import Asset, Clip, Track, VideoProject


def test_timeline_compiler_single_clip(tmp_path):
    fake_video = tmp_path / "video.mp4"
    fake_video.write_text("dummy")

    project = VideoProject()
    asset = Asset(type=AssetType.VIDEO, path=str(fake_video), duration_us=10_000_000)
    project.assets[asset.id] = asset

    track = Track(name="V1", type=TrackType.VIDEO, index=0)
    clip = Clip(
        asset_id=asset.id,
        timeline_start_us=0,
        timeline_duration_us=5_000_000,
        source_start_us=0,
        source_duration_us=5_000_000,
    )
    track.clips.append(clip)
    project.tracks.append(track)

    compiler = TimelineCompiler()
    plan = compiler.compile(project)

    assert plan.total_duration_us == 5_000_000
    assert len(plan.inputs) == 1
    assert plan.inputs[0].file_path == str(fake_video.resolve())
    assert len(plan.tracks) == 1
    assert len(plan.tracks[0].items) == 1
    assert isinstance(plan.tracks[0].items[0], RenderSegment)


def test_timeline_compiler_gap_detection(tmp_path):
    fake_video = tmp_path / "video.mp4"
    fake_video.write_text("dummy")

    project = VideoProject()
    asset = Asset(type=AssetType.VIDEO, path=str(fake_video), duration_us=10_000_000)
    project.assets[asset.id] = asset

    track = Track(name="V1", type=TrackType.VIDEO, index=0)
    c1 = Clip(
        asset_id=asset.id,
        timeline_start_us=0,
        timeline_duration_us=2_000_000,
        source_start_us=0,
        source_duration_us=2_000_000,
    )
    # Gap from 2.0s to 5.0s (3s gap)
    c2 = Clip(
        asset_id=asset.id,
        timeline_start_us=5_000_000,
        timeline_duration_us=3_000_000,
        source_start_us=2_000_000,
        source_duration_us=3_000_000,
    )
    track.clips.extend([c1, c2])
    project.tracks.append(track)

    compiler = TimelineCompiler()
    plan = compiler.compile(project)

    assert plan.total_duration_us == 8_000_000
    items = plan.tracks[0].items
    assert len(items) == 3
    assert isinstance(items[0], RenderSegment)
    assert isinstance(items[1], RenderGap)
    assert items[1].timeline_start_us == 2_000_000
    assert items[1].timeline_duration_us == 3_000_000
    assert isinstance(items[2], RenderSegment)
