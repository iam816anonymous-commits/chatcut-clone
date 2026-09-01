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
