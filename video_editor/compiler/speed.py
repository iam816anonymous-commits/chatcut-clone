"""Speed Control Compiler Engine for Video Editing IR.

Generates setpts (video) and chained atempo (audio) filter nodes for speed multiplier adjustments.
"""

from typing import List, Tuple
from video_editor.ir.exceptions import InvalidOperationError


def compile_video_speed_filter(speed: float) -> str:
    """Generates FFmpeg setpts filter string for video speed adjustment.

    Args:
        speed: Speed multiplier (e.g., 0.5 for half speed / slow motion, 2.0 for double speed).

    Returns:
        str: FFmpeg filter string (e.g. "setpts=2.0*PTS" or "setpts=0.5*PTS").

    Raises:
        InvalidOperationError: If speed <= 0.0.
    """
    if speed <= 0.0:
        raise InvalidOperationError(f"Speed multiplier must be > 0.0, got {speed}")

    pts_factor = 1.0 / speed
    return f"setpts={pts_factor:.6f}*PTS"


def compile_audio_speed_filters(speed: float) -> List[str]:
    """Generates FFmpeg chained atempo filter strings for audio speed adjustment.

    FFmpeg's `atempo` filter is limited to values between 0.5 and 2.0.
    For speeds outside this range (e.g., 0.25 or 4.0), multiple atempo filters are chained.

    Args:
        speed: Speed multiplier (e.g. 0.25, 0.5, 2.0, 4.0).

    Returns:
        List[str]: List of atempo filter string representations (e.g. ["atempo=2.0", "atempo=2.0"]).

    Raises:
        InvalidOperationError: If speed <= 0.0.
    """
    if speed <= 0.0:
        raise InvalidOperationError(f"Speed multiplier must be > 0.0, got {speed}")

    if speed == 1.0:
        return ["atempo=1.0"]

    filters: List[str] = []
    rem_speed = speed

    if rem_speed > 1.0:
        while rem_speed > 2.0:
            filters.append("atempo=2.0")
            rem_speed /= 2.0
        filters.append(f"atempo={rem_speed:.6f}")
    else:
        while rem_speed < 0.5:
            filters.append("atempo=0.5")
            rem_speed /= 0.5
        filters.append(f"atempo={rem_speed:.6f}")

    return filters
