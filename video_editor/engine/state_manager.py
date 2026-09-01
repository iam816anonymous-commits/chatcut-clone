"""Transactional Copy-On-Write State Engine for Universal Video Editing IR."""

from datetime import datetime, timezone
from typing import Optional, List

from video_editor.engine.history import HistoryManager
from video_editor.ir.enums import OperationType, TrackType
from video_editor.ir.exceptions import (
    AssetNotFoundError,
    ClipNotFoundError,
    InvalidOperationError,
    InvalidTimeRangeError,
    TrackLockedError,
    TrackNotFoundError,
)
from video_editor.ir.models import Asset, Clip, Track, VideoProject
from video_editor.ir.operations import (
    AddClipOperation,
    AddTrackOperation,
    DeleteClipOperation,
    DeleteTrackOperation,
    MoveClipOperation,
    Operation,
    SetClipTransformOperation,
    SetClipVolumeOperation,
    SplitClipOperation,
    TrimClipOperation,
)
from video_editor.ir.validation import validate_project_integrity


class StateManager:
    """Transactional Copy-on-Write State Manager for Video Projects."""

    def __init__(self, project: Optional[VideoProject] = None) -> None:
        initial = project or VideoProject()
        validate_project_integrity(initial)
        self._history = HistoryManager(initial)

    @property
    def project(self) -> VideoProject:
        """Get current validated project state."""
        return self._history.current_state

    @property
    def can_undo(self) -> bool:
        return self._history.can_undo

    @property
    def can_redo(self) -> bool:
        return self._history.can_redo

    def undo(self) -> VideoProject:
        """Perform undo state transition."""
        return self._history.undo()

    def redo(self) -> VideoProject:
        """Perform redo state transition."""
        return self._history.redo()

    def register_asset(self, asset: Asset) -> None:
        """Register a source media asset in project inventory."""
        self._history._current_state.assets[asset.id] = asset

    def apply_operation(self, operation: Operation) -> VideoProject:
        """Apply an atomic operation in a transactional copy-on-write sandbox."""
        # 1. Transactional Copy
        candidate_project = self._history.current_state.model_copy(deep=True)

        # 2. Apply State Transition
        op_type = operation.operation_type

        if op_type == OperationType.ADD_TRACK:
            self._exec_add_track(candidate_project, operation)  # type: ignore
        elif op_type == OperationType.DELETE_TRACK:
            self._exec_delete_track(candidate_project, operation)  # type: ignore
        elif op_type == OperationType.ADD_CLIP:
            self._exec_add_clip(candidate_project, operation)  # type: ignore
        elif op_type == OperationType.DELETE_CLIP:
            self._exec_delete_clip(candidate_project, operation)  # type: ignore
        elif op_type == OperationType.TRIM_CLIP:
            self._exec_trim_clip(candidate_project, operation)  # type: ignore
        elif op_type == OperationType.SPLIT_CLIP:
            self._exec_split_clip(candidate_project, operation)  # type: ignore
        elif op_type == OperationType.MOVE_CLIP:
            self._exec_move_clip(candidate_project, operation)  # type: ignore
        elif op_type == OperationType.SET_CLIP_VOLUME:
            self._exec_set_clip_volume(candidate_project, operation)  # type: ignore
        elif op_type == OperationType.SET_CLIP_TRANSFORM:
            self._exec_set_clip_transform(candidate_project, operation)  # type: ignore
        else:
            raise InvalidOperationError(f"Unsupported operation type: {op_type}")

        # 3. Update Timestamp
        candidate_project.updated_at = datetime.now(timezone.utc).isoformat()

        # 4. Integrity Validation Gate
        validate_project_integrity(candidate_project)

        # 5. Commit Transaction to History
        self._history.record_state_change(candidate_project, operation)
        return self.project

    # --- Operation Handlers ---

    def _get_track(self, project: VideoProject, track_id: str) -> Track:
        for track in project.tracks:
            if track.id == track_id:
                return track
        raise TrackNotFoundError(f"Track '{track_id}' not found", {"track_id": track_id})

    def _get_clip_and_track(
        self, project: VideoProject, track_id: str, clip_id: str
    ) -> tuple[Track, Clip]:
        track = self._get_track(project, track_id)
        for clip in track.clips:
            if clip.id == clip_id:
                return track, clip
        raise ClipNotFoundError(
            f"Clip '{clip_id}' not found on track '{track_id}'",
            {"track_id": track_id, "clip_id": clip_id},
        )

    def _exec_add_track(self, project: VideoProject, op: AddTrackOperation) -> None:
        target_index = op.index if op.index is not None else len(project.tracks)
        new_track = Track(
            name=op.track_name,
            type=op.track_type,
            index=target_index,
        )
        project.tracks.append(new_track)
        # Re-index tracks
        project.tracks.sort(key=lambda t: t.index)
        for idx, t in enumerate(project.tracks):
            t.index = idx

    def _exec_delete_track(self, project: VideoProject, op: DeleteTrackOperation) -> None:
        track = self._get_track(project, op.track_id)
        if track.locked:
            raise TrackLockedError(
                f"Cannot delete locked track '{track.id}'", {"track_id": track.id}
            )
        project.tracks = [t for t in project.tracks if t.id != op.track_id]
        # Re-index
        for idx, t in enumerate(project.tracks):
            t.index = idx

    def _exec_add_clip(self, project: VideoProject, op: AddClipOperation) -> None:
        track = self._get_track(project, op.track_id)
        if track.locked:
            raise TrackLockedError(
                f"Cannot add clip to locked track '{track.id}'", {"track_id": track.id}
            )
        track.clips.append(op.clip.model_copy(deep=True))
        track.clips.sort(key=lambda c: c.timeline_start_us)

    def _exec_delete_clip(self, project: VideoProject, op: DeleteClipOperation) -> None:
        track, clip = self._get_clip_and_track(project, op.track_id, op.clip_id)
        if track.locked:
            raise TrackLockedError(
                f"Cannot delete clip from locked track '{track.id}'",
                {"track_id": track.id},
            )
        track.clips = [c for c in track.clips if c.id != op.clip_id]

    def _exec_trim_clip(self, project: VideoProject, op: TrimClipOperation) -> None:
        track, clip = self._get_clip_and_track(project, op.track_id, op.clip_id)
        if track.locked:
            raise TrackLockedError(
                f"Cannot trim clip on locked track '{track.id}'", {"track_id": track.id}
            )
        clip.source_start_us = op.new_source_start_us
        clip.source_duration_us = op.new_source_duration_us
        # Adjust timeline duration matching source duration adjusted for speed
        clip.timeline_duration_us = round(op.new_source_duration_us / clip.speed)

    def _exec_split_clip(self, project: VideoProject, op: SplitClipOperation) -> None:
        track, clip = self._get_clip_and_track(project, op.track_id, op.clip_id)
        if track.locked:
            raise TrackLockedError(
                f"Cannot split clip on locked track '{track.id}'", {"track_id": track.id}
            )

        split_t = op.split_timeline_time_us
        if split_t <= clip.timeline_start_us or split_t >= clip.timeline_end_us:
            raise InvalidTimeRangeError(
                f"Split time {split_t}us must be strictly inside clip bounds ({clip.timeline_start_us}-{clip.timeline_end_us}us)",
                {
                    "split_t": split_t,
                    "start": clip.timeline_start_us,
                    "end": clip.timeline_end_us,
                },
            )

        # Calculate time split offsets
        left_timeline_duration = split_t - clip.timeline_start_us
        right_timeline_duration = clip.timeline_duration_us - left_timeline_duration

        left_source_duration = round(left_timeline_duration * clip.speed)
        right_source_duration = clip.source_duration_us - left_source_duration

        # Clip A (Left half)
        clip_a = clip.model_copy(deep=True)
        clip_a.timeline_duration_us = left_timeline_duration
        clip_a.source_duration_us = left_source_duration

        # Clip B (Right half)
        clip_b = clip.model_copy(deep=True)
        clip_b.id = generate_uuid()
        clip_b.timeline_start_us = split_t
        clip_b.timeline_duration_us = right_timeline_duration
        clip_b.source_start_us = clip.source_start_us + left_source_duration
        clip_b.source_duration_us = right_source_duration

        # Replace original clip
        idx = track.clips.index(clip)
        track.clips[idx] = clip_a
        track.clips.insert(idx + 1, clip_b)

    def _exec_move_clip(self, project: VideoProject, op: MoveClipOperation) -> None:
        src_track, clip = self._get_clip_and_track(
            project, op.source_track_id, op.clip_id
        )
        if src_track.locked:
            raise TrackLockedError(
                f"Cannot move clip from locked source track '{src_track.id}'",
                {"track_id": src_track.id},
            )

        dst_track = self._get_track(project, op.target_track_id)
        if dst_track.locked:
            raise TrackLockedError(
                f"Cannot move clip to locked target track '{dst_track.id}'",
                {"track_id": dst_track.id},
            )

        # Remove clip from source track
        src_track.clips = [c for c in src_track.clips if c.id != op.clip_id]

        # Update position and append to destination track
        clip.timeline_start_us = op.target_timeline_start_us
        dst_track.clips.append(clip)
        dst_track.clips.sort(key=lambda c: c.timeline_start_us)

    def _exec_set_clip_volume(
        self, project: VideoProject, op: SetClipVolumeOperation
    ) -> None:
        track, clip = self._get_clip_and_track(project, op.track_id, op.clip_id)
        if track.locked:
            raise TrackLockedError(
                f"Cannot modify clip on locked track '{track.id}'",
                {"track_id": track.id},
            )
        clip.audio.volume = op.volume
        clip.audio.muted = op.muted

    def _exec_set_clip_transform(
        self, project: VideoProject, op: SetClipTransformOperation
    ) -> None:
        track, clip = self._get_clip_and_track(project, op.track_id, op.clip_id)
        if track.locked:
            raise TrackLockedError(
                f"Cannot modify clip on locked track '{track.id}'",
                {"track_id": track.id},
            )
        clip.transform = op.transform.model_copy(deep=True)


def generate_uuid() -> str:
    import uuid

    return str(uuid.uuid4())
