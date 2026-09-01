"""Progress Monitor and Realtime FFmpeg Key/Value Output Parser."""

from typing import Callable, Optional
from video_editor.runtime.models import RenderProgress


class ProgressMonitor:
    """Parses key=value output lines from FFmpeg (`-progress pipe:1`) into RenderProgress models."""

    def __init__(
        self,
        total_duration_us: int = 0,
        on_progress_callback: Optional[Callable[[RenderProgress], None]] = None,
    ) -> None:
        self.total_duration_us = total_duration_us
        self.on_progress_callback = on_progress_callback
        self.current_progress = RenderProgress(total_duration_us=total_duration_us)

    def parse_line(self, line: str) -> None:
        line = line.strip()
        if not line or "=" not in line:
            return

        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()

        if key == "frame":
            try:
                self.current_progress.frame = int(val)
            except ValueError:
                pass
        elif key == "fps":
            try:
                self.current_progress.fps = float(val)
            except ValueError:
                pass
        elif key == "out_time_us":
            try:
                us = int(val)
                self.current_progress.current_time_us = us
                if self.total_duration_us > 0:
                    pct = min(100.0, max(0.0, (us / float(self.total_duration_us)) * 100.0))
                    self.current_progress.percent = round(pct, 2)
            except ValueError:
                pass
        elif key == "speed":
            try:
                spd_str = val.replace("x", "")
                self.current_progress.speed = float(spd_str)
            except ValueError:
                pass

        if key == "progress" and self.on_progress_callback:
            self.on_progress_callback(self.current_progress.model_copy())
