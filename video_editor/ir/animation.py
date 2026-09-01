"""Keyframe Animation Domain Models for Universal Video Editing IR."""

from enum import Enum
from typing import Any, List
from pydantic import BaseModel, Field, ConfigDict, model_validator
from video_editor.ir.exceptions import InvalidKeyframeError


class InterpolationMode(str, Enum):
    """Supported keyframe animation interpolation algorithms."""

    HOLD = "HOLD"
    LINEAR = "LINEAR"


# Alias for backward compatibility
InterpolationType = InterpolationMode


class AnimatedProperty(str, Enum):
    """Supported animatable clip and overlay properties."""

    POSITION_X = "POSITION_X"
    POSITION_Y = "POSITION_Y"
    SCALE_X = "SCALE_X"
    SCALE_Y = "SCALE_Y"
    OPACITY = "OPACITY"
    VOLUME = "VOLUME"


class Keyframe(BaseModel):
    """Single keyframe entry at a clip-local time offset."""

    model_config = ConfigDict(extra="ignore")

    time_us: int = Field(..., ge=0, description="Clip-local microsecond offset (>= 0)")
    value: float = Field(..., description="Property scalar value at keyframe timestamp")
    interpolation: InterpolationMode = Field(
        default=InterpolationMode.LINEAR, description="Interpolation curve to next keyframe"
    )


class AnimationTrack(BaseModel):
    """Track sequence of keyframes animating a specific property."""

    model_config = ConfigDict(extra="ignore")

    property: AnimatedProperty = Field(..., description="Target property enum")
    keyframes: List[Keyframe] = Field(default_factory=list, description="Ordered keyframe list")

    @model_validator(mode="after")
    def validate_keyframe_sequence(self) -> "AnimationTrack":
        """Enforce non-empty, strictly ordered keyframes with no duplicate timestamps."""
        if not self.keyframes:
            raise InvalidKeyframeError("AnimationTrack must contain at least one keyframe")

        seen_times = set()
        prev_time = -1

        for kf in self.keyframes:
            if kf.time_us in seen_times:
                raise InvalidKeyframeError(
                    f"Duplicate keyframe timestamp {kf.time_us}us found in track '{self.property}'"
                )
            if kf.time_us < prev_time:
                raise InvalidKeyframeError(
                    f"Keyframes in track '{self.property}' must be strictly sorted by time_us. "
                    f"Found {kf.time_us}us after {prev_time}us."
                )
            seen_times.add(kf.time_us)
            prev_time = kf.time_us

        return self
