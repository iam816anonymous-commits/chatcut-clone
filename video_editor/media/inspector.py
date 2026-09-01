"""FFprobe JSON Media Inspector."""

import json
import os
from typing import Any, Dict, List, Optional

from video_editor.media.exceptions import (
    InputFileNotFoundError,
    InvalidMediaError,
    MediaInspectionError,
)
from video_editor.media.models import (
    AudioStreamMetadata,
    ContainerMetadata,
    MediaMetadata,
    MediaType,
    VideoStreamMetadata,
)
from video_editor.rendering.executor import ProcessExecutor


def parse_rational_fps(fps_str: str) -> float:
    """Parse FFprobe rational frame rate string e.g. '30000/1001' or '24/1'."""
    if not fps_str or fps_str == "0/0":
        return 30.0
    if "/" in fps_str:
        try:
            num, den = fps_str.split("/")
            n, d = float(num), float(den)
            if d == 0:
                return 30.0
            return n / d
        except Exception:
            return 30.0
    try:
        val = float(fps_str)
        return val if val > 0 else 30.0
    except Exception:
        return 30.0


def parse_seconds_to_us(sec_val: Any) -> Optional[int]:
    """Parse string or float duration in seconds to integer microseconds."""
    if sec_val is None:
        return None
    try:
        s = float(sec_val)
        if s < 0:
            return None
        return round(s * 1_000_000)
    except (ValueError, TypeError):
        return None


class MediaInspector:
    """Inspects local media files using ffprobe JSON output."""

    def __init__(self, ffprobe_path: str = "ffprobe", timeout: float = 30.0) -> None:
        self.ffprobe_path = ffprobe_path
        self.executor = ProcessExecutor(default_timeout=timeout)

    def inspect(self, file_path: str) -> MediaMetadata:
        """Inspect media file and return typed MediaMetadata."""
        abs_path = os.path.abspath(os.path.realpath(file_path))
        if not os.path.exists(abs_path):
            raise InputFileNotFoundError(f"Media file not found: {abs_path}", {"file_path": abs_path})
        if os.path.isdir(abs_path):
            raise InputFileNotFoundError(f"Path is a directory, not a media file: {abs_path}", {"file_path": abs_path})

        cmd = [
            self.ffprobe_path,
            "-v", "error",
            "-show_format",
            "-show_streams",
            "-of", "json",
            abs_path,
        ]

        result = self.executor.execute(cmd)
        if not result.success:
            raise InvalidMediaError(
                f"FFprobe failed to inspect file: {result.stderr.strip() or 'Unknown error'}",
                {"file_path": abs_path, "stderr": result.stderr, "exit_code": result.exit_code},
            )

        try:
            probe_data: Dict[str, Any] = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise InvalidMediaError(
                f"Failed to parse FFprobe JSON output: {str(e)}",
                {"file_path": abs_path, "stdout": result.stdout},
            ) from e

        format_data = probe_data.get("format", {})
        streams_data = probe_data.get("streams", [])

        # Parse Container Metadata
        container_duration_us = parse_seconds_to_us(format_data.get("duration"))
        file_size_bytes = int(format_data.get("size", os.path.getsize(abs_path)))
        bit_rate_val = format_data.get("bit_rate")
        container_bit_rate = int(bit_rate_val) if bit_rate_val and str(bit_rate_val).isdigit() else None

        container = ContainerMetadata(
            format_name=format_data.get("format_name", "unknown"),
            format_long_name=format_data.get("format_long_name"),
            duration_us=container_duration_us,
            size_bytes=file_size_bytes,
            bit_rate=container_bit_rate,
        )

        video_streams: List[VideoStreamMetadata] = []
        audio_streams: List[AudioStreamMetadata] = []

        for stream in streams_data:
            codec_type = stream.get("codec_type")
            index = int(stream.get("index", 0))

            if codec_type == "video":
                # Check for attached image/cover art or image container
                width = int(stream.get("width", 0))
                height = int(stream.get("height", 0))
                if width > 0 and height > 0:
                    r_fps_str = stream.get("r_frame_rate", "30/1")
                    fps_val = parse_rational_fps(r_fps_str)
                    v_duration_us = parse_seconds_to_us(stream.get("duration"))
                    v_bitrate = int(stream.get("bit_rate")) if stream.get("bit_rate") and str(stream.get("bit_rate")).isdigit() else None

                    v_meta = VideoStreamMetadata(
                        index=index,
                        codec_name=stream.get("codec_name", "unknown"),
                        codec_long_name=stream.get("codec_long_name"),
                        width=width,
                        height=height,
                        fps=fps_val,
                        r_frame_rate=r_fps_str,
                        avg_frame_rate=stream.get("avg_frame_rate", r_fps_str),
                        pix_fmt=stream.get("pix_fmt"),
                        duration_us=v_duration_us,
                        bit_rate=v_bitrate,
                    )
                    video_streams.append(v_meta)

            elif codec_type == "audio":
                s_rate = int(stream.get("sample_rate", 44100))
                ch = int(stream.get("channels", 2))
                a_duration_us = parse_seconds_to_us(stream.get("duration"))
                a_bitrate = int(stream.get("bit_rate")) if stream.get("bit_rate") and str(stream.get("bit_rate")).isdigit() else None

                a_meta = AudioStreamMetadata(
                    index=index,
                    codec_name=stream.get("codec_name", "unknown"),
                    codec_long_name=stream.get("codec_long_name"),
                    sample_rate=s_rate,
                    channels=ch,
                    channel_layout=stream.get("channel_layout"),
                    duration_us=a_duration_us,
                    bit_rate=a_bitrate,
                )
                audio_streams.append(a_meta)

        # Classify MediaType
        if video_streams:
            # Check if static image container (png, jpeg, webp, single frame)
            fmt_name = container.format_name.lower()
            if any(img_fmt in fmt_name for img_fmt in ["image2", "png", "jpeg", "jpg", "webp", "bmp"]) or (
                container_duration_us is None and not audio_streams
            ):
                m_type = MediaType.IMAGE
            else:
                m_type = MediaType.VIDEO
        elif audio_streams:
            m_type = MediaType.AUDIO
        else:
            m_type = MediaType.UNKNOWN

        return MediaMetadata(
            file_path=abs_path,
            media_type=m_type,
            container=container,
            video_streams=video_streams,
            audio_streams=audio_streams,
            raw_probe=probe_data,
        )
