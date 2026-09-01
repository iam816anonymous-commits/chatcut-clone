"""Comprehensive transactional rollback and state integrity unit tests."""

import pytest
from video_editor.engine.state_manager import StateManager
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.exceptions import InvalidTimeRangeError, TrackLockedError
from video_editor.ir.models import Asset, Clip
from video_editor.ir.operations import AddClipOperation, AddTrackOperation, SplitClipOperation


def test_failed_operation_does_not_mutate_state_or_history():
    sm = StateManager()
    asset = Asset(type=AssetType.VIDEO, path="/video.mp4", duration_us=10_000_000)
    sm.register_asset(asset)

    sm.apply_operation(AddTrackOperation(track_name="V1", track_type=TrackType.VIDEO))
    track_id = sm.project.tracks[0].id

    clip = Clip(
        asset_id=asset.id,
        timeline_start_us=0,
        timeline_duration_us=4_000_000,
        source_start_us=0,
        source_duration_us=4_000_000,
    )
    sm.apply_operation(AddClipOperation(track_id=track_id, clip=clip))
    clip_id = sm.project.tracks[0].clips[0].id

    state_before_failure = sm.project.model_copy(deep=True)
    history_len_before = len(sm._history._past_states)
    ops_len_before = len(sm._history.history_log)

    # Attempt invalid split operation at boundary (0 us)
    invalid_op = SplitClipOperation(
        track_id=track_id, clip_id=clip_id, split_timeline_time_us=0
    )

    with pytest.raises(InvalidTimeRangeError):
        sm.apply_operation(invalid_op)

    # Verify state and history are 100% identical to before failure
    assert len(sm.project.tracks[0].clips) == 1
    assert sm.project.tracks[0].clips[0].id == clip_id
    assert len(sm._history._past_states) == history_len_before
    assert len(sm._history.history_log) == ops_len_before


def test_failed_operation_on_locked_track():
    sm = StateManager()
    sm.apply_operation(AddTrackOperation(track_name="V1", track_type=TrackType.VIDEO))
    track = sm.project.tracks[0]
    track.locked = True

    clip = Clip(
        timeline_start_us=0,
        timeline_duration_us=1_000_000,
        source_start_us=0,
        source_duration_us=1_000_000,
    )

    with pytest.raises(TrackLockedError):
        sm.apply_operation(AddClipOperation(track_id=track.id, clip=clip))

    assert len(sm.project.tracks[0].clips) == 0
