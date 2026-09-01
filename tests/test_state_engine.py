"""Unit tests for StateManager, HistoryManager, operations execution, and Undo/Redo."""

import pytest
from video_editor.engine.state_manager import StateManager
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.exceptions import (
    ClipNotFoundError,
    HistoryError,
    InvalidTimeRangeError,
    TrackLockedError,
    TrackNotFoundError,
)
from video_editor.ir.models import Asset, Clip, Transform
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


@pytest.fixture
def base_state_manager():
    sm = StateManager()
    # Register an asset
    asset = Asset(type=AssetType.VIDEO, path="/media/sample.mp4", duration_us=10_000_000)
    sm.register_asset(asset)

    # Add a track
    op_track = AddTrackOperation(track_name="Main Video", track_type=TrackType.VIDEO)
    sm.apply_operation(op_track)
    return sm, asset


def test_add_and_delete_track(base_state_manager):
    sm, _ = base_state_manager
    assert len(sm.project.tracks) == 1
    track_id = sm.project.tracks[0].id

    # Delete track
    op_del = DeleteTrackOperation(track_id=track_id)
    sm.apply_operation(op_del)
    assert len(sm.project.tracks) == 0

    # Test Undo
    sm.undo()
    assert len(sm.project.tracks) == 1

    # Test Redo
    sm.redo()
    assert len(sm.project.tracks) == 0


def test_add_trim_and_split_clip(base_state_manager):
    sm, asset = base_state_manager
    track_id = sm.project.tracks[0].id

    clip = Clip(
        asset_id=asset.id,
        timeline_start_us=0,
        timeline_duration_us=4_000_000,
        source_start_us=0,
        source_duration_us=4_000_000,
    )
    op_add = AddClipOperation(track_id=track_id, clip=clip)
    sm.apply_operation(op_add)
    assert len(sm.project.tracks[0].clips) == 1

    # Split clip at 2,000,000 us
    op_split = SplitClipOperation(
        track_id=track_id, clip_id=clip.id, split_timeline_time_us=2_000_000
    )
    sm.apply_operation(op_split)
    clips = sm.project.tracks[0].clips
    assert len(clips) == 2
    assert clips[0].timeline_start_us == 0
    assert clips[0].timeline_duration_us == 2_000_000
    assert clips[1].timeline_start_us == 2_000_000
    assert clips[1].timeline_duration_us == 2_000_000

    # Undo split
    sm.undo()
    assert len(sm.project.tracks[0].clips) == 1


def test_invalid_split_time(base_state_manager):
    sm, asset = base_state_manager
    track_id = sm.project.tracks[0].id

    clip = Clip(
        asset_id=asset.id,
        timeline_start_us=0,
        timeline_duration_us=4_000_000,
        source_start_us=0,
        source_duration_us=4_000_000,
    )
    sm.apply_operation(AddClipOperation(track_id=track_id, clip=clip))

    # Attempt split at boundary 0
    with pytest.raises(InvalidTimeRangeError):
        sm.apply_operation(
            SplitClipOperation(
                track_id=track_id, clip_id=clip.id, split_timeline_time_us=0
            )
        )

    # Ensure state remains uncorrupted
    assert len(sm.project.tracks[0].clips) == 1


def test_locked_track_rejection(base_state_manager):
    sm, asset = base_state_manager
    track = sm.project.tracks[0]
    track.locked = True

    clip = Clip(
        asset_id=asset.id,
        timeline_start_us=0,
        timeline_duration_us=2_000_000,
        source_start_us=0,
        source_duration_us=2_000_000,
    )
    with pytest.raises(TrackLockedError):
        sm.apply_operation(AddClipOperation(track_id=track.id, clip=clip))


def test_redo_branch_clearing(base_state_manager):
    sm, asset = base_state_manager
    track_id = sm.project.tracks[0].id

    clip1 = Clip(
        asset_id=asset.id,
        timeline_start_us=0,
        timeline_duration_us=1_000_000,
        source_start_us=0,
        source_duration_us=1_000_000,
    )
    sm.apply_operation(AddClipOperation(track_id=track_id, clip=clip1))
    assert sm.can_undo
    assert not sm.can_redo

    sm.undo()
    assert sm.can_redo

    # Perform new operation -> should clear redo stack
    clip2 = Clip(
        asset_id=asset.id,
        timeline_start_us=1_000_000,
        timeline_duration_us=1_000_000,
        source_start_us=0,
        source_duration_us=1_000_000,
    )
    sm.apply_operation(AddClipOperation(track_id=track_id, clip=clip2))
    assert not sm.can_redo
