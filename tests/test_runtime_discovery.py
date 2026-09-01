"""Unit tests for Runtime discovery mock behavior."""

from unittest.mock import patch
from video_editor.rendering.runtime import discover_runtime


@patch("shutil.which")
def test_discover_runtime_mocked(mock_which):
    mock_which.side_effect = lambda name: f"/usr/bin/{name}" if name in ["ffmpeg", "ffprobe"] else None

    caps = discover_runtime()
    assert caps.ffmpeg_available is True
    assert caps.ffmpeg_path == "/usr/bin/ffmpeg"
    assert caps.ffprobe_available is True
    assert caps.ffprobe_path == "/usr/bin/ffprobe"
