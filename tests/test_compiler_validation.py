"""Unit tests for compiler pre-renderability validation gate."""

import pytest
from video_editor.compiler.exceptions import (
    UnrenderableProjectError,
    UnsupportedTimelineStructureError,
    UnsupportedTrackTypeError,
)
from video_editor.compiler.validation import validate_project_renderability
from video_editor.ir.enums import TrackType
from video_editor.ir.models import Clip, TextStyle, Track, VideoProject


def test_empty_project_validation_fails():
    project = VideoProject()
    with pytest.raises(UnrenderableProjectError):
        validate_project_renderability(project)


def test_unsupported_text_track_fails():
    project = VideoProject()
    track = Track(name="Subtitles", type=TrackType.TEXT, index=0)
    clip = Clip(
        timeline_start_us=0,
        timeline_duration_us=1_000_000,
        source_start_us=0,
        source_duration_us=1_000_000,
        text=TextStyle(content="Hello"),
    )
    track.clips.append(clip)
    project.tracks.append(track)

    with pytest.raises(UnsupportedTrackTypeError):
        validate_project_renderability(project)


def test_multiple_video_tracks_fails():
    project = VideoProject()
    t1 = Track(name="V1", type=TrackType.VIDEO, index=0)
    c1 = Clip(
        timeline_start_us=0,
        timeline_duration_us=1_000_000,
        source_start_us=0,
        source_duration_us=1_000_000,
    )
    t1.clips.append(c1)

    t2 = Track(name="V2", type=TrackType.VIDEO, index=1)
    c2 = Clip(
        timeline_start_us=0,
        timeline_duration_us=1_000_000,
        source_start_us=0,
        source_duration_us=1_000_000,
    )
    t2.clips.append(c2)

    project.tracks.extend([t1, t2])

    with pytest.raises(UnsupportedTimelineStructureError):
        validate_project_renderability(project)
