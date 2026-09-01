"""FFmpeg Renderer Foundation Primitives and RenderPlan execution."""

import os
from typing import Callable, Optional

from video_editor.compiler.models import RenderPlan
from video_editor.compiler.planner import RenderPlanner
from video_editor.ir.models import VideoProject
from video_editor.media.exceptions import InputFileNotFoundError
from video_editor.rendering.base import BaseRenderer
from video_editor.rendering.command import FFmpegCommand
from video_editor.rendering.exceptions import (
    InputOverwriteError,
    InvalidDimensionsError,
    OutputValidationError,
    RenderExecutionError,
)
from video_editor.rendering.executor import ProcessExecutor, ProcessResult


def validate_paths(input_path: str, output_path: str) -> tuple[str, str]:
    """Validate and canonicalize input and output paths, guarding against overwrite."""
    abs_input = os.path.abspath(os.path.realpath(input_path))
    abs_output = os.path.abspath(os.path.realpath(output_path))

    if not os.path.exists(abs_input):
        raise InputFileNotFoundError(f"Input media file not found: {abs_input}", {"input_path": abs_input})
    if os.path.isdir(abs_input):
        raise InputFileNotFoundError(f"Input path is a directory: {abs_input}", {"input_path": abs_input})

    if abs_input == abs_output:
        raise InputOverwriteError(
            f"Output path cannot match input path: {abs_output}",
            {"input_path": abs_input, "output_path": abs_output},
        )

    out_dir = os.path.dirname(abs_output)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    if os.path.exists(abs_output) and os.path.isdir(abs_output):
        raise OutputValidationError(
            f"Output path points to an existing directory: {abs_output}",
            {"output_path": abs_output},
        )

    return abs_input, abs_output


def verify_rendered_output(output_path: str) -> None:
    """Verify that output file exists on disk and is non-empty after render."""
    if not os.path.exists(output_path):
        raise OutputValidationError(
            f"Render completed but output file missing from disk: {output_path}",
            {"output_path": output_path},
        )
    if os.path.getsize(output_path) == 0:
        raise OutputValidationError(
            f"Render completed but output file is empty (0 bytes): {output_path}",
            {"output_path": output_path},
        )


class FFmpegRenderer(BaseRenderer):
    """FFmpeg rendering engine implementing deterministic media processing primitives and RenderPlan execution."""

    def __init__(self, ffmpeg_path: str = "ffmpeg", timeout: float = 120.0) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.executor = ProcessExecutor(default_timeout=timeout)
        self.planner = RenderPlanner()

    def render(
        self,
        project: VideoProject,
        output_path: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> ProcessResult:
        """Proof-of-concept renderer boundary placeholder. Use render_plan() for compiled projects."""
        raise NotImplementedError("Direct IR rendering is deprecated. Compile project to RenderPlan and call render_plan().")

    def render_plan(self, plan: RenderPlan, output_path: str) -> ProcessResult:
        """Execute a compiled RenderPlan to produce a rendered media file."""
        abs_output = os.path.abspath(os.path.realpath(output_path))
        out_dir = os.path.dirname(abs_output)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        cmd = self.planner.plan_to_command(plan, abs_output, ffmpeg_path=self.ffmpeg_path)
        res = self.executor.execute(cmd)

        if not res.success:
            raise RenderExecutionError(
                f"RenderPlan execution failed: {res.stderr.strip()}",
                {"command": res.command, "stderr": res.stderr, "exit_code": res.exit_code},
            )

        verify_rendered_output(abs_output)
        return res

    def render_transcode(
        self, input_path: str, output_path: str, video_codec: str = "libx264", audio_codec: str = "aac"
    ) -> ProcessResult:
        """Primitive A: Simple deterministic transcode or stream copy."""
        abs_in, abs_out = validate_paths(input_path, output_path)

        cmd = FFmpegCommand(
            executable=self.ffmpeg_path,
            arguments=["-y", "-i", abs_in, "-c:v", video_codec, "-c:a", audio_codec, abs_out],
        )

        res = self.executor.execute(cmd)
        if not res.success:
            raise RenderExecutionError(
                f"Transcode operation failed: {res.stderr.strip()}",
                {"command": res.command, "stderr": res.stderr, "exit_code": res.exit_code},
            )

        verify_rendered_output(abs_out)
        return res

    def render_trim(
        self, input_path: str, output_path: str, start_us: int, duration_us: int, reencode: bool = True
    ) -> ProcessResult:
        """Primitive B: Simple deterministic video trim."""
        abs_in, abs_out = validate_paths(input_path, output_path)

        if start_us < 0:
            raise ValueError(f"Trim start_us must be >= 0, got {start_us}")
        if duration_us <= 0:
            raise ValueError(f"Trim duration_us must be > 0, got {duration_us}")

        start_sec = start_us / 1_000_000.0
        duration_sec = duration_us / 1_000_000.0

        args = ["-y", "-ss", f"{start_sec:.6f}", "-i", abs_in, "-t", f"{duration_sec:.6f}"]
        if reencode:
            args.extend(["-c:v", "libx264", "-c:a", "aac"])
        else:
            args.extend(["-c", "copy"])
        args.append(abs_out)

        cmd = FFmpegCommand(executable=self.ffmpeg_path, arguments=args)
        res = self.executor.execute(cmd)

        if not res.success:
            raise RenderExecutionError(
                f"Trim operation failed: {res.stderr.strip()}",
                {"command": res.command, "stderr": res.stderr, "exit_code": res.exit_code},
            )

        verify_rendered_output(abs_out)
        return res

    def render_scale(self, input_path: str, output_path: str, width: int, height: int) -> ProcessResult:
        """Primitive C: Simple deterministic spatial scaling."""
        abs_in, abs_out = validate_paths(input_path, output_path)

        if width < 1 or height < 1 or width > 7680 or height > 4320:
            raise InvalidDimensionsError(
                f"Invalid target dimensions: {width}x{height}",
                {"width": width, "height": height},
            )

        vf = f"scale={width}:{height}"
        cmd = FFmpegCommand(
            executable=self.ffmpeg_path,
            arguments=["-y", "-i", abs_in, "-vf", vf, "-c:v", "libx264", "-c:a", "aac", abs_out],
        )

        res = self.executor.execute(cmd)
        if not res.success:
            raise RenderExecutionError(
                f"Scale operation failed: {res.stderr.strip()}",
                {"command": res.command, "stderr": res.stderr, "exit_code": res.exit_code},
            )

        verify_rendered_output(abs_out)
        return res
