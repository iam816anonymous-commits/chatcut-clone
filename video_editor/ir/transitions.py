"""Transition Domain Models for Universal Video Editing IR."""

from enum import Enum
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict, model_validator
from video_editor.ir.exceptions import InvalidTransitionError


def generate_uuid() -> str:
    return str(uuid.uuid4())


class TransitionCategory(str, Enum):
    """Transition effect category classification."""

    FADE = "FADE"
    DISSOLVE = "DISSOLVE"
    WIPE = "WIPE"
    SLIDE = "SLIDE"


class TransitionType(str, Enum):
    """Supported video and audio transition effect types."""

    CROSSFADE = "CROSSFADE"
    CUT = "CUT"
    FADE = "FADE"
    FADE_BLACK = "FADE_BLACK"
    FADE_WHITE = "FADE_WHITE"
    WIPE_LEFT = "WIPE_LEFT"
    WIPE_RIGHT = "WIPE_RIGHT"
    WIPE_UP = "WIPE_UP"
    WIPE_DOWN = "WIPE_DOWN"
    SLIDE_LEFT = "SLIDE_LEFT"
    SLIDE_RIGHT = "SLIDE_RIGHT"
    DISSOLVE = "DISSOLVE"


class Transition(BaseModel):
    """Transition specification connecting adjacent clips or fading clip boundaries."""

    model_config = ConfigDict(extra="ignore")

    transition_id: str = Field(default_factory=generate_uuid)
    type: TransitionType = Field(default=TransitionType.FADE)
    duration_us: int = Field(..., gt=0, description="Transition blend duration in microseconds (> 0)")
    source_clip_id: Optional[str] = Field(default=None, description="Preceding outgoing clip ID")
    destination_clip_id: Optional[str] = Field(default=None, description="Following incoming clip ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Custom transition parameters")

    @model_validator(mode="after")
    def validate_transition_duration(self) -> "Transition":
        if self.duration_us <= 0:
            raise InvalidTransitionError(f"Transition duration_us must be > 0, got {self.duration_us}")
        return self
