"""Animation Compiler Engine for Video Editing IR.

Compiles keyframe tracks (position, scale, opacity) into FFmpeg filter expressions or zoompan/eval nodes.
"""

from typing import Dict, List, Optional
from video_editor.ir.animation import AnimationTrack, AnimatedProperty, Keyframe
from video_editor.compiler.interpolation import interpolate_keyframes


def compile_animation_eval_expression(
    animation_tracks: List[AnimationTrack],
    property_type: AnimatedProperty,
    duration_us: int,
    fps: float,
    default_value: float,
) -> str:
    """Compiles keyframes for a property into an FFmpeg time-based evaluation string (e.g., using 't').

    If no keyframes exist for property_type, returns string representation of default_value.
    For keyframe tracks, builds an FFmpeg mathematical piecewise expression or evaluates keyframes over time.

    Args:
        animation_tracks: List of animation tracks on clip.
        property_type: Target animated property (e.g. AnimatedProperty.OPACITY).
        duration_us: Total duration of the clip in microseconds.
        fps: Frames per second of canvas/clip.
        default_value: Fallback static value if property is not animated.

    Returns:
        str: FFmpeg filter expression string (e.g. "if(lte(t,1.0),0.0+t*1.0,1.0)").
    """
    track = next((t for t in animation_tracks if t.property == property_type), None)
    if not track or not track.keyframes:
        return str(default_value)

    keyframes = sorted(track.keyframes, key=lambda k: k.time_us)
    if len(keyframes) == 1:
        return str(keyframes[0].value)

    # Build nested if-else expression for FFmpeg filter evaluation (t is in seconds)
    # Piecewise linear: if(lte(t, t1), val1, if(lte(t, t2), val1 + (t-t1)/(t2-t1)*(val2-val1), ...))
    expr = str(keyframes[-1].value)

    for i in range(len(keyframes) - 2, -1, -1):
        k1 = keyframes[i]
        k2 = keyframes[i + 1]
        t1_sec = k1.time_us / 1000000.0
        t2_sec = k2.time_us / 1000000.0
        val1 = k1.value
        val2 = k2.value

        if k1.interpolation == "HOLD" or t1_sec == t2_sec:
            segment_expr = str(val1)
        else:
            slope = (val2 - val1) / (t2_sec - t1_sec)
            segment_expr = f"{val1}+{slope:.6f}*(t-{t1_sec:.6f})"

        if i == 0:
            expr = f"if(lte(t,{t1_sec:.6f}),{val1},if(lte(t,{t2_sec:.6f}),{segment_expr},{expr}))"
        else:
            expr = f"if(lte(t,{t2_sec:.6f}),{segment_expr},{expr})"

    return expr
