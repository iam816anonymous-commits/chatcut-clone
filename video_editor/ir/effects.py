"""Reusable and Temporal Visual Effect Domain Models for Universal Video Editing IR."""

from enum import Enum
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict, model_validator
from video_editor.ir.exceptions import InvalidEffectError


def generate_uuid() -> str:
    return str(uuid.uuid4())


class EffectType(str, Enum):
    """Supported visual and audio effect types."""

    BLUR = "BLUR"
    BRIGHTNESS = "BRIGHTNESS"
    CONTRAST = "CONTRAST"
    GRAYSCALE = "GRAYSCALE"
    VIGNETTE = "VIGNETTE"


class Effect(BaseModel):
    """Reusable visual effect specification with optional temporal interval bounds."""

    model_config = ConfigDict(extra="ignore")

    effect_id: str = Field(default_factory=generate_uuid)
    type: EffectType = Field(..., description="Target effect discriminator")
    start_time_us: Optional[int] = Field(default=None, ge=0, description="Clip-local start offset in us")
    duration_us: Optional[int] = Field(default=None, gt=0, description="Effect duration in us")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Effect parameters")

    @model_validator(mode="after")
    def validate_temporal_bounds(self) -> "Effect":
        if self.start_time_us is not None and self.duration_us is not None:
            if self.start_time_us < 0:
                raise InvalidEffectError(f"Effect start_time_us must be >= 0, got {self.start_time_us}")
            if self.duration_us <= 0:
                raise InvalidEffectError(f"Effect duration_us must be > 0, got {self.duration_us}")
        return self
