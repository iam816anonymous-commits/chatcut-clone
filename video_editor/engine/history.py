"""History Manager for Undo/Redo Stacks and Audit History."""

from typing import List, Optional
from video_editor.ir.exceptions import HistoryError
from video_editor.ir.operations import Operation
from video_editor.ir.models import VideoProject


class HistoryManager:
    """Manages undo/redo state history trees and operation logs."""

    def __init__(self, initial_project: VideoProject, max_history: int = 100) -> None:
        self._past_states: List[VideoProject] = []
        self._current_state: VideoProject = initial_project.model_copy(deep=True)
        self._future_states: List[VideoProject] = []
        self._operations: List[Operation] = []
        self._max_history = max_history

    @property
    def current_state(self) -> VideoProject:
        return self._current_state

    @property
    def can_undo(self) -> bool:
        return len(self._past_states) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._future_states) > 0

    @property
    def history_log(self) -> List[Operation]:
        return list(self._operations)

    def record_state_change(self, new_state: VideoProject, operation: Operation) -> None:
        """Commit a new project state and operation to history, clearing the redo stack."""
        self._past_states.append(self._current_state)
        if len(self._past_states) > self._max_history:
            self._past_states.pop(0)

        self._current_state = new_state.model_copy(deep=True)
        self._future_states.clear()  # Clear redo branch on new edit
        self._operations.append(operation)

    def undo(self) -> VideoProject:
        """Revert to previous project state."""
        if not self.can_undo:
            raise HistoryError("No states available to undo")

        self._future_states.append(self._current_state)
        self._current_state = self._past_states.pop()
        return self._current_state.model_copy(deep=True)

    def redo(self) -> VideoProject:
        """Advance to next project state in redo stack."""
        if not self.can_redo:
            raise HistoryError("No states available to redo")

        self._past_states.append(self._current_state)
        self._current_state = self._future_states.pop()
        return self._current_state.model_copy(deep=True)
