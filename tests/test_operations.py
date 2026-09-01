"""Unit tests for atomic operations."""

import pytest
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.models import Asset, Clip, Track, VideoProject
from video_editor.ir.operations import (
    AddClipOperation,
    AddTrackOperation,
    DeleteClipOperation,
    DeleteTrackOperation,
    MoveClipOperation,
    SetClipTransformOperation,
    SetClipVolumeOperation,
    SplitClipOperation,
    TrimClipOperation,
)


def test_operation_models_instantiation():
    op_track = AddTrackOperation(track_name="V1", track_type=TrackType.VIDEO)
    assert op_track.track_name == "V1"
    assert op_track.track_type == TrackType.VIDEO

    clip = Clip(
        timeline_start_us=0,
        timeline_duration_us=1_000_000,
        source_start_us=0,
        source_duration_us=1_000_000,
    )
    op_clip = AddClipOperation(track_id="t1", clip=clip)
    assert op_clip.track_id == "t1"
    assert op_clip.clip.id == clip.id
