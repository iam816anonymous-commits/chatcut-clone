"""Pre-compilation Project Renderability Validation Gate."""

from video_editor.compiler.exceptions import UnrenderableProjectError
from video_editor.ir.models import VideoProject
from video_editor.ir.validation import validate_project_integrity


def validate_project_renderability(project: VideoProject) -> None:
    """Validate project integrity and verify renderability under Phase 2C rules.

    Phase 2C Compiler Scope Rules:
    1. Project must pass standard IR integrity checks (`validate_project_integrity`).
    2. Project must contain at least one non-empty track with renderable clips.
    3. Multi-track VIDEO compositing is fully supported (Z-ordered overlays).
    4. Multi-track AUDIO mixing is fully supported.
    5. TEXT and SUBTITLE overlay rendering are fully supported via drawtext filters.
    """
    validate_project_integrity(project)

    active_tracks = [t for t in project.tracks if not t.muted and len(t.clips) > 0]
    if not active_tracks:
        raise UnrenderableProjectError(
            f"Project '{project.id}' contains zero active tracks with renderable clips",
            {"project_id": project.id},
        )

    # Validate Phase 2D Clip Properties (speed, transitions, keyframes, effects)
    for track in project.tracks:
        for clip in track.clips:
            if hasattr(clip, "speed") and clip.speed <= 0.0:
                raise UnrenderableProjectError(
                    f"Clip '{clip.id}' has invalid speed multiplier {clip.speed}",
                    {"clip_id": clip.id, "speed": clip.speed},
                )

            # Transition duration check
            for trans_attr in ("transition_in", "transition_out", "in_transition", "out_transition"):
                trans = getattr(clip, trans_attr, None)
                if trans is not None:
                    if trans.duration_us <= 0:
                        raise UnrenderableProjectError(
                            f"Clip '{clip.id}' has transition duration <= 0: {trans.duration_us}us",
                            {"clip_id": clip.id, "duration_us": trans.duration_us},
                        )
                    if trans.duration_us > clip.timeline_duration_us:
                        raise UnrenderableProjectError(
                            f"Clip '{clip.id}' transition duration {trans.duration_us}us exceeds clip duration {clip.timeline_duration_us}us",
                            {"clip_id": clip.id, "trans_duration": trans.duration_us, "clip_duration": clip.timeline_duration_us},
                        )
