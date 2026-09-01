"""Unit tests for TimelineTime, Pydantic IR domain models, and Validation."""

import pytest
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.exceptions import (
    AssetNotFoundError,
    ClipOverlapError,
    InvalidTimeRangeError,
)
from video_editor.ir.models import Asset, Clip, Track, VideoProject
from video_editor.ir.time import TimelineTime
from video_editor.ir.validation import validate_project_integrity


def test_timeline_time_conversions():
    t1 = TimelineTime.from_seconds(2.5)
    assert t1.microseconds == 2_500_000
    assert t1.seconds == 2.5

    t2 = TimelineTime.from_frames(30, 30.0)
    assert t2.microseconds == 1_000_000

    assert t1 + t2 == TimelineTime(3_500_000)
    assert t1 - t2 == TimelineTime(1_500_000)
    assert t1 > t2


def test_clip_derived_properties():
    clip = Clip(
        timeline_start_us=1_000_000,
        timeline_duration_us=2_000_000,
        source_start_us=500_000,
        source_duration_us=2_000_000,
    )
    assert clip.timeline_end_us == 3_000_000
    assert clip.source_end_us == 2_500_000


def test_project_duration_computation():
    project = VideoProject()
    asset = Asset(type=AssetType.VIDEO, path="test.mp4", duration_us=10_000_000)
    project.assets[asset.id] = asset

    track = Track(name="Main Video", type=TrackType.VIDEO, index=0)
    clip1 = Clip(
        asset_id=asset.id,
        timeline_start_us=0,
        timeline_duration_us=3_000_000,
        source_start_us=0,
        source_duration_us=3_000_000,
    )
    clip2 = Clip(
        asset_id=asset.id,
        timeline_start_us=3_000_000,
        timeline_duration_us=4_000_000,
        source_start_us=3_000_000,
        source_duration_us=4_000_000,
    )
    track.clips.extend([clip1, clip2])
    project.tracks.append(track)

    assert project.duration_us == 7_000_000
    validate_project_integrity(project)


def test_validation_missing_asset():
    project = VideoProject()
    track = Track(name="Video", type=TrackType.VIDEO, index=0)
    clip = Clip(
        asset_id="non-existent-asset-id",
        timeline_start_us=0,
        timeline_duration_us=1_000_000,
        source_start_us=0,
        source_duration_us=1_000_000,
    )
    track.clips.append(clip)
    project.tracks.append(track)

    with pytest.raises(AssetNotFoundError):
        validate_project_integrity(project)


def test_validation_overlap_rejection():
    project = VideoProject()
    asset = Asset(type=AssetType.VIDEO, path="v.mp4", duration_us=10_000_000)
    project.assets[asset.id] = asset

    track = Track(name="Video", type=TrackType.VIDEO, index=0)
    c1 = Clip(
        asset_id=asset.id,
        timeline_start_us=0,
        timeline_duration_us=2_000_000,
        source_start_us=0,
        source_duration_us=2_000_000,
    )
    c2 = Clip(
        asset_id=asset.id,
        timeline_start_us=1_500_000,  # Overlaps c1
        timeline_duration_us=2_000_000,
        source_start_us=0,
        source_duration_us=2_000_000,
    )
    track.clips.extend([c1, c2])
    project.tracks.append(track)

    with pytest.raises(ClipOverlapError):
        validate_project_integrity(project)
