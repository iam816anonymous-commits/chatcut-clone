"""Unit tests for validation hardening, track overlap policies, and error handling."""

import pytest
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.exceptions import (
    AssetNotFoundError,
    ClipOverlapError,
    ProjectIntegrityError,
)
from video_editor.ir.models import Asset, Clip, TextStyle, Track, VideoProject
from video_editor.ir.validation import validate_project_integrity


def test_audio_track_allows_overlaps():
    project = VideoProject()
    asset = Asset(type=AssetType.AUDIO, path="/audio.mp3", duration_us=10_000_000)
    project.assets[asset.id] = asset

    track = Track(name="Background Music & Voice", type=TrackType.AUDIO, index=0)
    c1 = Clip(
        asset_id=asset.id,
        timeline_start_us=0,
        timeline_duration_us=5_000_000,
        source_start_us=0,
        source_duration_us=5_000_000,
    )
    c2 = Clip(
        asset_id=asset.id,
        timeline_start_us=2_000_000,  # Overlaps c1 on audio track
        timeline_duration_us=5_000_000,
        source_start_us=0,
        source_duration_us=5_000_000,
    )
    track.clips.extend([c1, c2])
    project.tracks.append(track)

    # Audio overlaps must pass validation cleanly
    validate_project_integrity(project)


def test_video_track_forbids_overlaps():
    project = VideoProject()
    asset = Asset(type=AssetType.VIDEO, path="/video.mp4", duration_us=10_000_000)
    project.assets[asset.id] = asset

    track = Track(name="Main Video", type=TrackType.VIDEO, index=0)
    c1 = Clip(
        asset_id=asset.id,
        timeline_start_us=0,
        timeline_duration_us=5_000_000,
        source_start_us=0,
        source_duration_us=5_000_000,
    )
    c2 = Clip(
        asset_id=asset.id,
        timeline_start_us=2_000_000,  # Overlaps c1 on video track
        timeline_duration_us=5_000_000,
        source_start_us=0,
        source_duration_us=5_000_000,
    )
    track.clips.extend([c1, c2])
    project.tracks.append(track)

    with pytest.raises(ClipOverlapError):
        validate_project_integrity(project)


def test_duplicate_clip_ids_rejected():
    project = VideoProject()
    track = Track(name="Video", type=TrackType.VIDEO, index=0)
    c1 = Clip(
        id="duplicate-clip-id",
        timeline_start_us=0,
        timeline_duration_us=1_000_000,
        source_start_us=0,
        source_duration_us=1_000_000,
    )
    c2 = Clip(
        id="duplicate-clip-id",
        timeline_start_us=2_000_000,
        timeline_duration_us=1_000_000,
        source_start_us=0,
        source_duration_us=1_000_000,
    )
    track.clips.extend([c1, c2])
    project.tracks.append(track)

    with pytest.raises(ProjectIntegrityError):
        validate_project_integrity(project)


def test_unsupported_ir_version_rejected():
    project = VideoProject(version="2.0.0")
    with pytest.raises(ProjectIntegrityError):
        validate_project_integrity(project)
