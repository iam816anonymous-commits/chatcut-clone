"""Domain Enums for Universal Video Editing IR."""

from enum import Enum


class AssetType(str, Enum):
    """Supported source media asset categories."""

    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    IMAGE = "IMAGE"
    FONT = "FONT"


class TrackType(str, Enum):
    """Supported timeline track layer categories."""

    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    TEXT = "TEXT"
    SUBTITLE = "SUBTITLE"
    EFFECT = "EFFECT"


class AspectRatio(str, Enum):
    """Standard canvas aspect ratios."""

    RATIO_16_9 = "16:9"
    RATIO_9_16 = "9:16"
    RATIO_1_1 = "1:1"
    RATIO_4_5 = "4:5"
    CUSTOM = "Custom"


class OperationType(str, Enum):
    """Supported atomic state editing operations."""

    ADD_TRACK = "ADD_TRACK"
    DELETE_TRACK = "DELETE_TRACK"
    ADD_CLIP = "ADD_CLIP"
    DELETE_CLIP = "DELETE_CLIP"
    TRIM_CLIP = "TRIM_CLIP"
    SPLIT_CLIP = "SPLIT_CLIP"
    MOVE_CLIP = "MOVE_CLIP"
    SET_CLIP_VOLUME = "SET_CLIP_VOLUME"
    SET_CLIP_TRANSFORM = "SET_CLIP_TRANSFORM"


class ActorType(str, Enum):
    """Originator actor performing an operation."""

    USER = "USER"
    AI = "AI"
    SYSTEM = "SYSTEM"


class TextAlignment(str, Enum):
    """Text alignment options."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class TransitionType(str, Enum):
    """Supported transition effect types."""

    CUT = "CUT"
    FADE = "FADE"
    DISSOLVE = "DISSOLVE"


class EffectType(str, Enum):
    """Supported visual and audio effect types."""

    BLUR = "BLUR"
    BRIGHTNESS = "BRIGHTNESS"
    CONTRAST = "CONTRAST"
    CROP = "CROP"
    AUDIO_FADE = "AUDIO_FADE"
