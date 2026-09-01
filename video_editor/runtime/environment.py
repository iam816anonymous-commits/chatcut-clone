"""FFmpeg Environment Inspector."""

import shutil
import subprocess
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict
from video_editor.runtime.errors import FFmpegNotAvailableError


class EnvironmentStatus(BaseModel):
    """Inspected status of FFmpeg and FFprobe binaries."""

    model_config = ConfigDict(extra="ignore")

    ffmpeg_available: bool
    ffprobe_available: bool
    ffmpeg_path: str
    ffprobe_path: str
    ffmpeg_version: str


class FFmpegEnvironmentInspector:
    """Inspects host system for FFmpeg and FFprobe availability and binary versions."""

    @classmethod
    def inspect(cls) -> EnvironmentStatus:
        ffmpeg_bin = shutil.which("ffmpeg") or ""
        ffprobe_bin = shutil.which("ffprobe") or ""

        version_str = "unknown"
        if ffmpeg_bin:
            try:
                res = subprocess.run(
                    [ffmpeg_bin, "-version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5,
                )
                if res.returncode == 0 and res.stdout:
                    version_str = res.stdout.splitlines()[0]
            except Exception:
                pass

        return EnvironmentStatus(
            ffmpeg_available=bool(ffmpeg_bin),
            ffprobe_available=bool(ffprobe_bin),
            ffmpeg_path=ffmpeg_bin,
            ffprobe_path=ffprobe_bin,
            ffmpeg_version=version_str,
        )

    @classmethod
    def require_environment(cls) -> EnvironmentStatus:
        status = cls.inspect()
        if not status.ffmpeg_available:
            raise FFmpegNotAvailableError("ffmpeg binary not found in system PATH")
        if not status.ffprobe_available:
            raise FFmpegNotAvailableError("ffprobe binary not found in system PATH")
        return status
