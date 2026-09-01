"""Validation Layer and Integrity Checker for Universal Video Editing IR."""

from typing import List
from video_editor.ir.enums import TrackType, AssetType
from video_editor.ir.exceptions import (
    AssetNotFoundError,
    ClipNotFoundError,
    ClipOverlapError,
    InvalidTimeRangeError,
    InvalidTrackTypeError,
    ProjectIntegrityError,
    TrackLockedError,
    TrackNotFoundError,
)
from video_editor.ir.models import Clip, Track, VideoProject

# Canonical Version Policy Boundary
SUPPORTED_MAJOR_VERSIONS = {"1"}


def validate_clip_time_bounds(clip: Clip, asset_duration_us: int | None = None) -> None:
    """Validate clip timing parameters."""
    if clip.timeline_start_us < 0:
        raise InvalidTimeRangeError(
            f"Clip timeline_start_us must be >= 0, got {clip.timeline_start_us}",
            {"clip_id": clip.id, "timeline_start_us": clip.timeline_start_us},
        )
    if clip.timeline_duration_us <= 0:
        raise InvalidTimeRangeError(
            f"Clip timeline_duration_us must be > 0, got {clip.timeline_duration_us}",
            {"clip_id": clip.id, "timeline_duration_us": clip.timeline_duration_us},
        )
    if clip.source_start_us < 0:
        raise InvalidTimeRangeError(
            f"Clip source_start_us must be >= 0, got {clip.source_start_us}",
            {"clip_id": clip.id, "source_start_us": clip.source_start_us},
        )
    if clip.source_duration_us <= 0:
        raise InvalidTimeRangeError(
            f"Clip source_duration_us must be > 0, got {clip.source_duration_us}",
            {"clip_id": clip.id, "source_duration_us": clip.source_duration_us},
        )

    if asset_duration_us is not None:
        if clip.source_end_us > asset_duration_us:
            raise InvalidTimeRangeError(
                f"Clip source range ({clip.source_start_us} to {clip.source_end_us} us) "
                f"exceeds asset duration ({asset_duration_us} us)",
                {
                    "clip_id": clip.id,
                    "source_end_us": clip.source_end_us,
                    "asset_duration_us": asset_duration_us,
                },
            )


def check_clip_overlaps(clips: List[Clip]) -> None:
    """Check if any clips in a track overlap in timeline range."""
    sorted_clips = sorted(clips, key=lambda c: c.timeline_start_us)
    for i in range(len(sorted_clips) - 1):
        c1 = sorted_clips[i]
        c2 = sorted_clips[i + 1]
        if c1.timeline_end_us > c2.timeline_start_us:
            raise ClipOverlapError(
                f"Clips '{c1.id}' and '{c2.id}' overlap in timeline range "
                f"({c1.timeline_start_us}-{c1.timeline_end_us} vs {c2.timeline_start_us}-{c2.timeline_end_us})",
                {
                    "clip1_id": c1.id,
                    "clip2_id": c2.id,
                    "clip1_end": c1.timeline_end_us,
                    "clip2_start": c2.timeline_start_us,
                },
            )


def validate_track_clip_compatibility(track: Track, clip: Clip) -> None:
    """Ensure clip payload matches track layer type."""
    if track.type == TrackType.TEXT or track.type == TrackType.SUBTITLE:
        if clip.text is None:
            raise InvalidTrackTypeError(
                f"Text/Subtitle track '{track.id}' requires text style on clip '{clip.id}'",
                {"track_id": track.id, "clip_id": clip.id},
            )


def validate_project_integrity(project: VideoProject) -> None:
    """Run comprehensive business logic and structural integrity validation."""
    # Validate Schema Version Boundary
    major_ver = project.version.split(".")[0]
    if major_ver not in SUPPORTED_MAJOR_VERSIONS:
        raise ProjectIntegrityError(
            f"Unsupported IR version '{project.version}'. Major version '{major_ver}' is not supported.",
            {"version": project.version},
        )

    track_ids = set()
    clip_ids = set()

    for track in project.tracks:
        if track.id in track_ids:
            raise ProjectIntegrityError(
                f"Duplicate track ID '{track.id}' found in project",
                {"track_id": track.id},
            )
        track_ids.add(track.id)

        for clip in track.clips:
            if clip.id in clip_ids:
                raise ProjectIntegrityError(
                    f"Duplicate clip ID '{clip.id}' found in project",
                    {"clip_id": clip.id},
                )
            clip_ids.add(clip.id)

            asset_duration = None
            if clip.asset_id is not None:
                if clip.asset_id not in project.assets:
                    raise AssetNotFoundError(
                        f"Clip '{clip.id}' references missing asset '{clip.asset_id}'",
                        {"clip_id": clip.id, "asset_id": clip.asset_id},
                    )
                asset_duration = project.assets[clip.asset_id].duration_us

            validate_clip_time_bounds(clip, asset_duration)
            validate_track_clip_compatibility(track, clip)

        # Explicit Overlap Policy: Single-layer visual tracks (VIDEO) disallow overlaps.
        # Audio tracks (AUDIO) and text/subtitle overlay tracks explicitly ALLOW overlaps for mixing and compositing.
        if track.type == TrackType.VIDEO:
            check_clip_overlaps(track.clips)
