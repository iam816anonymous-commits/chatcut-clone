"""Runtime Binary Executable Discovery & Capabilities Inspection."""

import shutil
import subprocess
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RuntimeCapabilities(BaseModel):
    """Inspected system runtime binary availability and version information."""

    model_config = ConfigDict(extra="ignore")

    ffmpeg_available: bool = False
    ffmpeg_path: Optional[str] = None
    ffmpeg_version: Optional[str] = None
    ffprobe_available: bool = False
    ffprobe_path: Optional[str] = None
    ffprobe_version: Optional[str] = None


def _get_version_string(executable_path: str) -> Optional[str]:
    """Execute binary with -version and extract first line."""
    try:
        res = subprocess.run(
            [executable_path, "-version"],
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
        if res.returncode == 0 and res.stdout:
            lines = res.stdout.strip().splitlines()
            if lines:
                return lines[0].strip()
    except Exception:
        pass
    return None


def discover_runtime(
    ffmpeg_path: Optional[str] = None, ffprobe_path: Optional[str] = None
) -> RuntimeCapabilities:
    """Discover availability and paths for ffmpeg and ffprobe binaries."""
    resolved_ffmpeg = ffmpeg_path or shutil.which("ffmpeg")
    resolved_ffprobe = ffprobe_path or shutil.which("ffprobe")

    ffmpeg_avail = resolved_ffmpeg is not None
    ffprobe_avail = resolved_ffprobe is not None

    ffmpeg_ver = _get_version_string(resolved_ffmpeg) if resolved_ffmpeg else None
    ffprobe_ver = _get_version_string(resolved_ffprobe) if resolved_ffprobe else None

    return RuntimeCapabilities(
        ffmpeg_available=ffmpeg_avail,
        ffmpeg_path=resolved_ffmpeg,
        ffmpeg_version=ffmpeg_ver,
        ffprobe_available=ffprobe_avail,
        ffprobe_path=resolved_ffprobe,
        ffprobe_version=ffprobe_ver,
    )
