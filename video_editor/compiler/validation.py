"""Pre-compilation Project Renderability Validation Gate."""

from video_editor.compiler.exceptions import (
    UnrenderableProjectError,
    UnsupportedTimelineStructureError,
    UnsupportedTrackTypeError,
)
from video_editor.ir.enums import TrackType
from video_editor.ir.models import VideoProject
from video_editor.ir.validation import validate_project_integrity


def validate_project_renderability(project: VideoProject) -> None:
    """Validate project integrity and verify renderability under Phase 2B rules.

    Phase 2B Compiler Scope Rules:
    1. Project must pass standard IR integrity checks (`validate_project_integrity`).
    2. Project must contain at least one non-empty track with renderable clips.
    3. TEXT and SUBTITLE tracks are explicitly unsupported in Phase 2B compiler.
    4. At most ONE VIDEO track is supported in Phase 2B (no multi-layer video compositing yet).
    """
    validate_project_integrity(project)

    active_tracks = [t for t in project.tracks if not t.muted and len(t.clips) > 0]
    if not active_tracks:
        raise UnrenderableProjectError(
            f"Project '{project.id}' contains zero active tracks with renderable clips",
            {"project_id": project.id},
        )

    video_tracks = []
    for track in project.tracks:
        if track.type in (TrackType.TEXT, TrackType.SUBTITLE):
            raise UnsupportedTrackTypeError(
                f"Track '{track.name}' ({track.id}) uses type '{track.type}', which is unsupported in Phase 2B compiler.",
                {"track_id": track.id, "track_type": track.type},
            )
        if track.type == TrackType.VIDEO and not track.muted and len(track.clips) > 0:
            video_tracks.append(track)

    if len(video_tracks) > 1:
        raise UnsupportedTimelineStructureError(
            f"Project contains {len(video_tracks)} active VIDEO tracks. Phase 2B supports at most 1 active VIDEO track.",
            {"active_video_track_count": len(video_tracks)},
        )
