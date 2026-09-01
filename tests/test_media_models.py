"""Unit tests for media domain models."""

import pytest
from video_editor.media.models import (
    AudioStreamMetadata,
    ContainerMetadata,
    MediaMetadata,
    MediaType,
    VideoStreamMetadata,
)


def test_media_metadata_duration_fallbacks():
    container = ContainerMetadata(format_name="mov,mp4", duration_us=10_000_000, size_bytes=1024)
    v_stream = VideoStreamMetadata(
        index=0,
        codec_name="h264",
        width=1080,
        height=1920,
        fps=30.0,
        r_frame_rate="30/1",
        avg_frame_rate="30/1",
        duration_us=9_000_000,
    )
    media = MediaMetadata(
        file_path="/media/video.mp4",
        media_type=MediaType.VIDEO,
        container=container,
        video_streams=[v_stream],
    )

    assert media.duration_us == 10_000_000
    assert media.primary_video_stream.codec_name == "h264"
    assert media.primary_audio_stream is None


def test_media_metadata_audio_only():
    container = ContainerMetadata(format_name="mp3", duration_us=None, size_bytes=512)
    a_stream = AudioStreamMetadata(
        index=0, codec_name="mp3", sample_rate=44100, channels=2, duration_us=5_000_000
    )
    media = MediaMetadata(
        file_path="/audio.mp3",
        media_type=MediaType.AUDIO,
        container=container,
        audio_streams=[a_stream],
    )

    assert media.duration_us == 5_000_000
    assert media.primary_audio_stream.sample_rate == 44100
    assert media.primary_video_stream is None
