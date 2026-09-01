"""Typed Pydantic v2 RenderPlan Domain Schemas."""

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from video_editor.ir.enums import TrackType
from video_editor.ir.models import Transform, TextStyle
from video_editor.ir.animation import AnimationTrack
from video_editor.ir.transitions import Transition
from video_editor.ir.effects import Effect


def generate_uuid() -> str:
    return str(uuid.uuid4())


class RenderInput(BaseModel):
    """Registered input media asset file for rendering."""

    model_config = ConfigDict(extra="ignore")

    input_index: int = Field(..., ge=0, description="FFmpeg input index (-i 0, -i 1, etc.)")
    asset_id: str = Field(..., description="Referenced IR Asset ID")
    file_path: str = Field(..., description="Canonical absolute file path on disk")


class RenderSegment(BaseModel):
    """Media clip segment compiled for timeline placement."""

    model_config = ConfigDict(extra="ignore")

    clip_id: str = Field(..., description="Referenced IR Clip ID")
    asset_id: str = Field(default="", description="Referenced IR Asset ID")
    input_index: int = Field(default=0, ge=0, description="Corresponding RenderInput index")
    timeline_start_us: int = Field(..., ge=0, description="Timeline position in microseconds")
    timeline_duration_us: int = Field(..., gt=0, description="Timeline duration in microseconds")
    source_start_us: int = Field(default=0, ge=0, description="Source trim start in microseconds")
    source_duration_us: int = Field(default=1_000_000, gt=0, description="Source trim duration in microseconds")
    speed: float = Field(default=1.0, gt=0.1, le=10.0, description="Playback speed multiplier")
    volume: float = Field(default=1.0, ge=0.0, le=2.0, description="Audio volume multiplier")
    transform: Transform = Field(default_factory=Transform, description="Static spatial transform")
    text_style: Optional[TextStyle] = Field(default=None, description="TextStyle for text/subtitle clips")
    animation_tracks: List[AnimationTrack] = Field(default_factory=list, description="Keyframe animation tracks")
    transition_in: Optional[Transition] = Field(default=None, description="Inbound clip transition")
    transition_out: Optional[Transition] = Field(default=None, description="Outbound clip transition")
    effects: List[Effect] = Field(default_factory=list, description="Visual/audio effect chain")

    @property
    def timeline_end_us(self) -> int:
        return self.timeline_start_us + self.timeline_duration_us


class RenderGap(BaseModel):
    """Explicit timeline gap requiring black video or silent audio generation."""

    model_config = ConfigDict(extra="ignore")

    gap_id: str = Field(default_factory=generate_uuid)
    timeline_start_us: int = Field(..., ge=0)
    timeline_duration_us: int = Field(..., gt=0)

    @property
    def timeline_end_us(self) -> int:
        return self.timeline_start_us + self.timeline_duration_us


class RenderTrack(BaseModel):
    """Compiled timeline track containing segments and explicit gaps."""

    model_config = ConfigDict(extra="ignore")

    track_id: str = Field(..., description="Referenced IR Track ID")
    track_type: TrackType = Field(..., description="Track layer type")
    index: int = Field(..., ge=0)
    items: List[RenderSegment | RenderGap] = Field(default_factory=list)


class RenderOutputSettings(BaseModel):
    """Target output encoding parameters."""

    model_config = ConfigDict(extra="ignore")

    width: int = Field(default=1080, ge=1)
    height: int = Field(default=1920, ge=1)
    fps: float = Field(default=30.0, gt=0)
    video_codec: str = Field(default="libx264")
    audio_codec: str = Field(default="aac")
    audio_sample_rate: int = Field(default=48000)
    audio_channels: int = Field(default=2)


class RenderPlan(BaseModel):
    """Root compiled, pure, inspectable render plan."""

    model_config = ConfigDict(extra="ignore")

    plan_id: str = Field(default_factory=generate_uuid)
    project_id: str = Field(..., description="Source VideoProject ID")
    version: str = Field(default="1.0.0")
    total_duration_us: int = Field(..., ge=0, description="Compiled sequence total duration in us")
    output_settings: RenderOutputSettings = Field(default_factory=RenderOutputSettings)
    inputs: List[RenderInput] = Field(default_factory=list)
    tracks: List[RenderTrack] = Field(default_factory=list)

    @property
    def video_tracks(self) -> List[RenderTrack]:
        return [t for t in self.tracks if t.track_type == TrackType.VIDEO]

    @property
    def audio_tracks(self) -> List[RenderTrack]:
        return [t for t in self.tracks if t.track_type == TrackType.AUDIO]

    @property
    def text_tracks(self) -> List[RenderTrack]:
        return [t for t in self.tracks if t.track_type in (TrackType.TEXT, TrackType.SUBTITLE)]
