"""Unit tests for time precision hardening and invariant checks."""

import pytest
from pydantic import ValidationError
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.exceptions import InvalidTimeRangeError
from video_editor.ir.models import Asset, Clip, Track, VideoProject
from video_editor.ir.time import TimelineTime
from video_editor.ir.validation import validate_clip_time_bounds, validate_project_integrity


def test_timeline_time_float_conversion_determinism():
    t1 = TimelineTime.from_seconds(1.234567)
    assert t1.microseconds == 1_234_567
    assert t1.seconds == 1.234567

    # Multi-step arithmetic without float drift
    t_step = TimelineTime.from_seconds(0.1)  # 100,000 us
    accum = TimelineTime(0)
    for _ in range(10):
        accum = accum + t_step
    assert accum.microseconds == 1_000_000
    assert accum.seconds == 1.0


def test_clip_negative_start_rejection():
    with pytest.raises(ValidationError):
        Clip(
            timeline_start_us=-100,
            timeline_duration_us=1_000_000,
            source_start_us=0,
            source_duration_us=1_000_000,
        )


def test_clip_zero_duration_rejection():
    with pytest.raises(ValidationError):
        Clip(
            timeline_start_us=0,
            timeline_duration_us=0,  # Zero duration rejected
            source_start_us=0,
            source_duration_us=1_000_000,
        )

    with pytest.raises(ValidationError):
        Clip(
            timeline_start_us=0,
            timeline_duration_us=1_000_000,
            source_start_us=0,
            source_duration_us=0,  # Zero source duration rejected
        )


def test_clip_source_exceeds_asset_duration():
    asset = Asset(type=AssetType.VIDEO, path="/video.mp4", duration_us=5_000_000)
    clip = Clip(
        asset_id=asset.id,
        timeline_start_us=0,
        timeline_duration_us=6_000_000,
        source_start_us=0,
        source_duration_us=6_000_000,  # 6s > asset 5s
    )

    with pytest.raises(InvalidTimeRangeError):
        validate_clip_time_bounds(clip, asset.duration_us)
