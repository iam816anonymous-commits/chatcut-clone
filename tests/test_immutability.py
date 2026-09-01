"""Unit tests specifically targeting state immutability and deep-copy isolation."""

import pytest
from video_editor.engine.state_manager import StateManager
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.models import Asset, Clip, Transform, AudioConfig, TextStyle
from video_editor.ir.operations import (
    AddClipOperation,
    AddTrackOperation,
    SetClipTransformOperation,
    SetClipVolumeOperation,
)


def test_deep_copy_isolation_on_nested_objects():
    sm = StateManager()
    asset = Asset(type=AssetType.VIDEO, path="/video.mp4", duration_us=10_000_000)
    sm.register_asset(asset)

    # 1. Add track
    sm.apply_operation(AddTrackOperation(track_name="V1", track_type=TrackType.VIDEO))
    track_id = sm.project.tracks[0].id

    # 2. Add clip with initial transform and audio
    clip = Clip(
        asset_id=asset.id,
        timeline_start_us=0,
        timeline_duration_us=3_000_000,
        source_start_us=0,
        source_duration_us=3_000_000,
        transform=Transform(position_x=10.0, scale_x=1.0),
        audio=AudioConfig(volume=1.0),
    )
    sm.apply_operation(AddClipOperation(track_id=track_id, clip=clip))
    clip_id = sm.project.tracks[0].clips[0].id

    # Capture initial state snapshot reference
    initial_project = sm.project
    initial_clip = initial_project.tracks[0].clips[0]

    # 3. Apply transform operation
    new_transform = Transform(position_x=500.0, scale_x=2.0, rotation=45.0)
    sm.apply_operation(
        SetClipTransformOperation(
            track_id=track_id, clip_id=clip_id, transform=new_transform
        )
    )

    updated_clip = sm.project.tracks[0].clips[0]
    assert updated_clip.transform.position_x == 500.0

    # Verify initial snapshot remains strictly unpolluted
    assert initial_clip.transform.position_x == 10.0
    assert initial_clip.transform.scale_x == 1.0

    # 4. Direct mutation attempt on new state object
    sm.project.tracks[0].clips[0].audio.volume = 0.1
    # Verify undo restores true original state
    sm.undo()  # Undoes transform operation
    assert sm.project.tracks[0].clips[0].transform.position_x == 10.0
    assert sm.project.tracks[0].clips[0].audio.volume == 1.0
