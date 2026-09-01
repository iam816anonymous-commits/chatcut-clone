"""Unit tests for MediaInspector and rational FPS parsing."""

import json
import pytest
from unittest.mock import MagicMock
from video_editor.media.exceptions import InputFileNotFoundError, InvalidMediaError
from video_editor.media.inspector import MediaInspector, parse_rational_fps, parse_seconds_to_us
from video_editor.media.models import MediaType
from video_editor.rendering.executor import ProcessResult


def test_parse_rational_fps():
    assert parse_rational_fps("30000/1001") == pytest.approx(29.97002997)
    assert parse_rational_fps("60000/1001") == pytest.approx(59.94005994)
    assert parse_rational_fps("24/1") == 24.0
    assert parse_rational_fps("0/0") == 30.0
    assert parse_rational_fps("") == 30.0


def test_parse_seconds_to_us():
    assert parse_seconds_to_us("10.5") == 10_500_000
    assert parse_seconds_to_us(5) == 5_000_000
    assert parse_seconds_to_us("-1") is None
    assert parse_seconds_to_us("invalid") is None


def test_inspector_missing_file_raises_exception():
    inspector = MediaInspector()
    with pytest.raises(InputFileNotFoundError):
        inspector.inspect("/non_existent_file.mp4")


def test_inspector_ffprobe_mock_parsing(tmp_path):
    fake_file = tmp_path / "sample.mp4"
    fake_file.write_text("fake video data")

    inspector = MediaInspector()
    mock_executor = MagicMock()

    probe_json = {
        "format": {
            "format_name": "mov,mp4",
            "duration": "10.0",
            "size": "1024",
            "bit_rate": "1000000"
        },
        "streams": [
            {
                "codec_type": "video",
                "index": 0,
                "codec_name": "h264",
                "width": 1080,
                "height": 1920,
                "r_frame_rate": "30/1",
                "duration": "10.0"
            },
            {
                "codec_type": "audio",
                "index": 1,
                "codec_name": "aac",
                "sample_rate": 48000,
                "channels": 2,
                "duration": "10.0"
            }
        ]
    }

    mock_executor.execute.return_value = ProcessResult(
        success=True,
        exit_code=0,
        stdout=json.dumps(probe_json),
        stderr="",
        duration_ms=10.0
    )
    inspector.executor = mock_executor

    meta = inspector.inspect(str(fake_file))
    assert meta.media_type == MediaType.VIDEO
    assert meta.container.duration_us == 10_000_000
    assert meta.primary_video_stream.width == 1080
    assert meta.primary_audio_stream.sample_rate == 48000
