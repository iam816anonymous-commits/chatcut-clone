"""Core Pydantic v2 Models for Universal Video Editing IR v1.0.0."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field, ConfigDict, model_validator

from video_editor.ir.enums import (
    AspectRatio,
    AssetType,
    EffectType as EnumEffectType,
    TextAlignment,
    TrackType,
    TransitionType as EnumTransitionType,
)
from video_editor.ir.animation import AnimationTrack
from video_editor.ir.effects import Effect as DomainEffect, EffectType
from video_editor.ir.transitions import Transition as DomainTransition, TransitionType, TransitionCategory


def generate_uuid() -> str:
    """Generate a random UUID string."""
    return str(uuid.uuid4())


class ProjectSettings(BaseModel):
    """Canvas and sequence settings."""

    model_config = ConfigDict(extra="ignore")

    width: int = Field(default=1080, ge=1, description="Canvas pixel width")
    height: int = Field(default=1920, ge=1, description="Canvas pixel height")
    fps: float = Field(default=30.0, gt=0, description="Target frame rate")
    aspect_ratio: AspectRatio = Field(
        default=AspectRatio.RATIO_9_16, description="Canvas aspect ratio"
    )
    timebase: str = Field(default="microseconds", description="Canonical timebase unit")
    background_color: str = Field(
        default="#000000",
        pattern=r"^#[0-9a-fA-F]{6}$",
        description="Hex background color",
    )


class Asset(BaseModel):
    """Source media asset registered in project inventory."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=generate_uuid, description="Asset UUID")
    type: AssetType = Field(..., description="Asset type discriminator")
    path: str = Field(..., description="Disk or resource path")
    duration_us: int = Field(..., ge=0, description="Source duration in microseconds")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Inspected asset metadata"
    )


class Transform(BaseModel):
    """2D Spatial affine transform configuration."""

    model_config = ConfigDict(extra="ignore")

    position_x: float = Field(default=0.0, description="Pixel X offset from center")
    position_y: float = Field(default=0.0, description="Pixel Y offset from center")
    scale_x: float = Field(default=1.0, description="X scale multiplier")
    scale_y: float = Field(default=1.0, description="Y scale multiplier")
    rotation: float = Field(default=0.0, ge=-360.0, le=360.0, description="Rotation degrees")


class AudioConfig(BaseModel):
    """Audio volume, muting, and fade settings."""

    model_config = ConfigDict(extra="ignore")

    volume: float = Field(default=1.0, ge=0.0, le=2.0, description="Volume multiplier")
    muted: bool = Field(default=False, description="Mute audio channel")
    fade_in_us: int = Field(default=0, ge=0, description="Fade in duration in us")
    fade_out_us: int = Field(default=0, ge=0, description="Fade out duration in us")


class TextStyle(BaseModel):
    """Styling properties for text and subtitle overlays."""

    model_config = ConfigDict(extra="ignore")

    content: str = Field(..., description="Displayed text content")
    font_family: str = Field(default="Inter", description="Font family name")
    font_size: int = Field(default=48, ge=1, description="Font point size")
    font_color: str = Field(
        default="#FFFFFF",
        pattern=r"^#[0-9a-fA-F]{6}$",
        description="Hex text color",
    )
    alignment: TextAlignment = Field(
        default=TextAlignment.CENTER, description="Text alignment"
    )


Effect = DomainEffect
Transition = DomainTransition


class Clip(BaseModel):
    """Placed media clip or text instance on a timeline track."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=generate_uuid, description="Clip UUID")
    asset_id: Optional[str] = Field(
        default=None, description="Referenced source Asset UUID"
    )
    timeline_start_us: int = Field(
        ..., ge=0, description="Timeline position in microseconds"
    )
    timeline_duration_us: int = Field(
        ..., gt=0, description="Timeline duration in microseconds"
    )
    source_start_us: int = Field(
        default=0, ge=0, description="Trimmed offset in source asset in us"
    )
    source_duration_us: int = Field(
        ..., gt=0, description="Trimmed duration in source asset in us"
    )
    speed: float = Field(
        default=1.0, gt=0.1, le=10.0, description="Playback speed multiplier"
    )
    transform: Transform = Field(default_factory=Transform)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    text: Optional[TextStyle] = Field(
        default=None, description="TextStyle if text/subtitle clip"
    )
    effects: List[Effect] = Field(default_factory=list)
    transition_in: Optional[Transition] = Field(default=None)
    transition_out: Optional[Transition] = Field(default=None)
    in_transition: Optional[Transition] = Field(default=None)
    out_transition: Optional[Transition] = Field(default=None)
    animation_tracks: List[AnimationTrack] = Field(default_factory=list)

    @property
    def timeline_end_us(self) -> int:
        """Derived property: timeline end position in microseconds."""
        return self.timeline_start_us + self.timeline_duration_us

    @property
    def source_end_us(self) -> int:
        """Derived property: source asset trim end in microseconds."""
        return self.source_start_us + self.source_duration_us


class Track(BaseModel):
    """Timeline layer containing ordered clips."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=generate_uuid, description="Track UUID")
    name: str = Field(..., description="Track display label")
    type: TrackType = Field(..., description="Track layer type")
    index: int = Field(..., ge=0, description="Z-order / stack priority index")
    muted: bool = Field(default=False, description="Mute track")
    locked: bool = Field(default=False, description="Lock track against modifications")
    clips: List[Clip] = Field(default_factory=list, description="Clips on track")


class VideoProject(BaseModel):
    """Root canonical Universal Video Editing IR project state."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=generate_uuid, description="Project UUID")
    name: str = Field(default="Untitled Project", description="Project title")
    version: str = Field(default="1.0.0", description="IR Schema version")
    settings: ProjectSettings = Field(default_factory=ProjectSettings)
    assets: Dict[str, Asset] = Field(
        default_factory=dict, description="Registered media asset dictionary"
    )
    tracks: List[Track] = Field(
        default_factory=list, description="Timeline track layers"
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def duration_us(self) -> int:
        """Derived project duration: max timeline_end_us across all tracks and clips."""
        max_duration = 0
        for track in self.tracks:
            for clip in track.clips:
                if clip.timeline_end_us > max_duration:
                    max_duration = clip.timeline_end_us
        return max_duration
