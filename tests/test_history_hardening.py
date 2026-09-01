"""Comprehensive unit tests for HistoryManager boundary and branching semantics."""

import pytest
from video_editor.engine.state_manager import StateManager
from video_editor.ir.enums import TrackType
from video_editor.ir.exceptions import HistoryError
from video_editor.ir.operations import AddTrackOperation


def test_undo_at_initial_state_raises_history_error():
    sm = StateManager()
    assert not sm.can_undo
    with pytest.raises(HistoryError):
        sm.undo()


def test_redo_with_empty_future_stack_raises_history_error():
    sm = StateManager()
    assert not sm.can_redo
    with pytest.raises(HistoryError):
        sm.redo()


def test_redo_branch_invalidation():
    sm = StateManager()

    # Step 1: Add Track 1
    sm.apply_operation(AddTrackOperation(track_name="V1", track_type=TrackType.VIDEO))
    # Step 2: Add Track 2
    sm.apply_operation(AddTrackOperation(track_name="V2", track_type=TrackType.VIDEO))

    assert len(sm.project.tracks) == 2

    # Step 3: Undo once back to V1
    sm.undo()
    assert len(sm.project.tracks) == 1
    assert sm.can_redo

    # Step 4: Apply new Operation Track 3
    sm.apply_operation(AddTrackOperation(track_name="V3", track_type=TrackType.VIDEO))

    # Redo stack MUST be cleared
    assert not sm.can_redo
    assert len(sm.project.tracks) == 2
    assert sm.project.tracks[1].name == "V3"
    with pytest.raises(HistoryError):
        sm.redo()
