"""Deterministic Keyframe Interpolation Engine for Video Editing IR.

Supports HOLD and LINEAR interpolation for animated clip properties (position_x, position_y,
scale_x, scale_y, opacity, volume) across timeline microsecond offsets.
"""

import math
from typing import List, Union
from video_editor.ir.animation import Keyframe, InterpolationMode, AnimatedProperty
from video_editor.ir.exceptions import InvalidKeyframeError


def interpolate_keyframes(
    keyframes: List[Keyframe],
    time_us: int,
) -> float:
    """Calculates the interpolated value for a sequence of keyframes at a specific microsecond offset.

    Args:
        keyframes: List of Keyframe instances for a single property, ordered or unsorted.
        time_us: Target timeline/clip microsecond offset (>= 0).

    Returns:
        float: Interpolated property value.

    Raises:
        InvalidKeyframeError: If keyframes list is empty or invalid.
    """
    if not keyframes:
        raise InvalidKeyframeError("Cannot interpolate empty keyframes list")

    if time_us < 0:
        raise InvalidKeyframeError(f"Target interpolation time_us must be >= 0, got {time_us}")

    # Sort keyframes by time_us
    sorted_kf = sorted(keyframes, key=lambda k: k.time_us)

    # Boundary checks: before first keyframe or after last keyframe
    if time_us <= sorted_kf[0].time_us:
        return float(sorted_kf[0].value)
    if time_us >= sorted_kf[-1].time_us:
        return float(sorted_kf[-1].value)

    # Find bounding interval [kf_prev, kf_next]
    prev_kf = sorted_kf[0]
    next_kf = sorted_kf[-1]

    for i in range(len(sorted_kf) - 1):
        if sorted_kf[i].time_us <= time_us <= sorted_kf[i + 1].time_us:
            prev_kf = sorted_kf[i]
            next_kf = sorted_kf[i + 1]
            break

    if prev_kf.interpolation == InterpolationMode.HOLD:
        return float(prev_kf.value)

    # LINEAR interpolation
    interval_us = next_kf.time_us - prev_kf.time_us
    if interval_us == 0:
        return float(prev_kf.value)

    t = (time_us - prev_kf.time_us) / float(interval_us)
    interpolated = prev_kf.value + t * (next_kf.value - prev_kf.value)

    return float(interpolated)
