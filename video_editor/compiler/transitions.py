"""Transition Compiler Engine for Video Editing IR.

Compiles video transitions (`xfade`) and audio transitions (`acrossfade` or `afade`) between adjacent clips.
"""

from typing import Dict, List, Optional, Tuple
from video_editor.ir.transitions import Transition, TransitionType, TransitionCategory
from video_editor.ir.exceptions import InvalidTransitionError


TRANSITION_TYPE_MAP: Dict[TransitionType, str] = {
    TransitionType.CROSSFADE: "fade",
    TransitionType.FADE: "fade",
    TransitionType.FADE_BLACK: "fadeblack",
    TransitionType.FADE_WHITE: "fadewhite",
    TransitionType.WIPE_LEFT: "wipeleft",
    TransitionType.WIPE_RIGHT: "wiperight",
    TransitionType.WIPE_UP: "wipeup",
    TransitionType.WIPE_DOWN: "wipedown",
    TransitionType.SLIDE_LEFT: "slideleft",
    TransitionType.SLIDE_RIGHT: "slideright",
    TransitionType.DISSOLVE: "dissolve",
}


def compile_video_transition(
    transition: Transition,
    offset_us: int,
) -> str:
    """Generates FFmpeg `xfade` filter string for video transitions.

    Args:
        transition: Transition spec instance.
        offset_us: Timeline start offset in microseconds where transition transition occurs.

    Returns:
        str: FFmpeg xfade filter expression (e.g. "xfade=transition=fade:duration=1.000000:offset=4.000000").

    Raises:
        InvalidTransitionError: If transition type is not supported for video.
    """
    ff_transition = TRANSITION_TYPE_MAP.get(transition.type)
    if not ff_transition:
        raise InvalidTransitionError(f"Unsupported video transition type: {transition.type}")

    duration_sec = transition.duration_us / 1000000.0
    offset_sec = offset_us / 1000000.0

    return f"xfade=transition={ff_transition}:duration={duration_sec:.6f}:offset={offset_sec:.6f}"


def compile_audio_transition(
    transition: Transition,
) -> str:
    """Generates FFmpeg `acrossfade` filter string for audio crossfades.

    Args:
        transition: Transition spec instance.

    Returns:
        str: FFmpeg acrossfade filter expression (e.g. "acrossfade=d=1.000000:c1=tri:c2=tri").
    """
    duration_sec = transition.duration_us / 1000000.0
    return f"acrossfade=d={duration_sec:.6f}:c1=tri:c2=tri"
