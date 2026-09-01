"""Deterministic FilterGraph Node Ordering Specification."""

from typing import List


class RenderingOrder:
    """Defines explicit, deterministic filter sequence order for video and audio processing chains."""

    VIDEO_FILTER_SEQUENCE: List[str] = [
        "trim",
        "setpts",
        "effects",
        "scale",
        "fps",
        "overlay",
        "xfade",
        "drawtext",
    ]

    AUDIO_FILTER_SEQUENCE: List[str] = [
        "atrim",
        "asetpts",
        "atempo",
        "aformat",
        "volume",
        "acrossfade",
        "adelay",
        "amix",
    ]
