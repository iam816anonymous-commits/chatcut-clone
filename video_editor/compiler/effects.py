"""Visual Effect Compiler Engine for Video Editing IR.

Compiles reusable/temporal effects (BLUR, BRIGHTNESS, CONTRAST, GRAYSCALE, VIGNETTE) into FFmpeg filter nodes with optional enable expressions (`enable='between(t,start,end)'`).
"""

from typing import Dict, List, Optional
from video_editor.ir.effects import Effect, EffectType
from video_editor.ir.exceptions import InvalidEffectError


def compile_effect_filter(
    effect: Effect,
) -> str:
    """Compiles an Effect specification into an FFmpeg filter string.

    Supports optional temporal interval filtering using FFmpeg's `enable` evaluation string.

    Args:
        effect: Effect domain model instance.

    Returns:
        str: FFmpeg filter string (e.g. "boxblur=luma_radius=10:enable='between(t,1.0,3.0)'").

    Raises:
        InvalidEffectError: If effect parameters or type are invalid.
    """
    enable_suffix = ""
    if effect.start_time_us is not None and effect.duration_us is not None:
        start_sec = effect.start_time_us / 1000000.0
        end_sec = (effect.start_time_us + effect.duration_us) / 1000000.0
        enable_suffix = f":enable='between(t,{start_sec:.6f},{end_sec:.6f})'"

    if effect.type == EffectType.BLUR:
        radius = effect.parameters.get("radius", 5)
        return f"boxblur=luma_radius={radius}:luma_power=1{enable_suffix}"

    elif effect.type == EffectType.BRIGHTNESS:
        b = effect.parameters.get("brightness", 0.0)
        return f"eq=brightness={b:.4f}{enable_suffix}"

    elif effect.type == EffectType.CONTRAST:
        c = effect.parameters.get("contrast", 1.0)
        return f"eq=contrast={c:.4f}{enable_suffix}"

    elif effect.type == EffectType.GRAYSCALE:
        return f"hue=s=0{enable_suffix}"

    elif effect.type == EffectType.VIGNETTE:
        angle = effect.parameters.get("angle", "PI/5")
        return f"vignette=angle={angle}{enable_suffix}"

    else:
        raise InvalidEffectError(f"Unsupported effect type: {effect.type}")


def compile_effect_chain(
    effects: List[Effect],
) -> List[str]:
    """Compiles a list of visual effects into a list of sequential FFmpeg filter strings.

    Args:
        effects: List of Effect instances.

    Returns:
        List[str]: List of compiled FFmpeg filter strings.
    """
    if not effects:
        return []
    return [compile_effect_filter(eff) for eff in effects]
