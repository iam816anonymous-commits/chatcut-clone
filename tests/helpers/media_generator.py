"""Deterministic Synthetic Test Media Generators using FFmpeg lavfi sources."""

import subprocess
from typing import Optional
from video_editor.runtime.environment import FFmpegEnvironmentInspector


class TestMediaGenerator:
    """Generates tiny, deterministic video and audio test assets locally using FFmpeg lavfi filters."""

    @classmethod
    def generate_test_video(
        cls,
        output_path: str,
        duration_sec: float = 2.0,
        width: int = 320,
        height: int = 240,
        fps: int = 30,
        color: str = "red",
    ) -> bool:
        """Generate a small synthetic MP4 video file using lavfi color source and sine audio."""
        env = FFmpegEnvironmentInspector.inspect()
        if not env.ffmpeg_available:
            return False

        cmd = [
            env.ffmpeg_path,
            "-y",
            "-f", "lavfi",
            "-i", f"color=c={color}:s={width}x{height}:r={fps}:d={duration_sec:.2f}",
            "-f", "lavfi",
            "-i", f"sine=f=440:r=48000:d={duration_sec:.2f}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            output_path,
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
            return res.returncode == 0
        except Exception:
            return False
