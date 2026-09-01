"""Typed, serializable atomic operation payloads for Universal Video Editing IR."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

from pydantic import BaseModel, Field, ConfigDict

from video_editor.ir.enums import ActorType, OperationType, TrackType
from video_editor.ir.models import AudioConfig, Clip, Track, Transform


def generate_uuid() -> str:
    """Generate a random UUID string."""
    return str(uuid.uuid4())


class Operation(BaseModel):
    """Base atomic operation payload."""

    model_config = ConfigDict(extra="ignore")

    operation_id: str = Field(default_factory=generate_uuid)
    operation_type: OperationType
    actor: ActorType = Field(default=ActorType.USER)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AddTrackOperation(Operation):
    """Operation: Add a new track to the project timeline."""

    operation_type: OperationType = Field(default=OperationType.ADD_TRACK)
    track_name: str
    track_type: TrackType
    index: Optional[int] = Field(
        default=None, description="Optional target index (defaults to end of stack)"
    )


class DeleteTrackOperation(Operation):
    """Operation: Delete a track by ID."""

    operation_type: OperationType = Field(default=OperationType.DELETE_TRACK)
    track_id: str


class AddClipOperation(Operation):
    """Operation: Insert a clip into a track."""

    operation_type: OperationType = Field(default=OperationType.ADD_CLIP)
    track_id: str
    clip: Clip


class DeleteClipOperation(Operation):
    """Operation: Remove a clip from a track."""

    operation_type: OperationType = Field(default=OperationType.DELETE_CLIP)
    track_id: str
    clip_id: str


class TrimClipOperation(Operation):
    """Operation: Trim a clip's source range and timeline duration."""

    operation_type: OperationType = Field(default=OperationType.TRIM_CLIP)
    track_id: str
    clip_id: str
    new_source_start_us: int = Field(..., ge=0)
    new_source_duration_us: int = Field(..., gt=0)


class SplitClipOperation(Operation):
    """Operation: Split a clip into two adjacent clips at split_timeline_time_us."""

    operation_type: OperationType = Field(default=OperationType.SPLIT_CLIP)
    track_id: str
    clip_id: str
    split_timeline_time_us: int = Field(..., ge=0)


class MoveClipOperation(Operation):
    """Operation: Reposition a clip on timeline or transfer to another track."""

    operation_type: OperationType = Field(default=OperationType.MOVE_CLIP)
    source_track_id: str
    clip_id: str
    target_track_id: str
    target_timeline_start_us: int = Field(..., ge=0)


class SetClipVolumeOperation(Operation):
    """Operation: Update audio volume and muted status for a clip."""

    operation_type: OperationType = Field(default=OperationType.SET_CLIP_VOLUME)
    track_id: str
    clip_id: str
    volume: float = Field(..., ge=0.0, le=2.0)
    muted: bool = Field(default=False)


class SetClipTransformOperation(Operation):
    """Operation: Update spatial 2D transform parameters for a clip."""

    operation_type: OperationType = Field(default=OperationType.SET_CLIP_TRANSFORM)
    track_id: str
    clip_id: str
    transform: Transform
