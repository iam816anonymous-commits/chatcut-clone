"""Rendering Subsystem Domain Exceptions."""

from video_editor.ir.exceptions import VideoEditorError


class RenderingError(VideoEditorError):
    """Base exception for rendering process failures."""

    pass


class ExecutableNotFoundError(RenderingError):
    """Raised when ffmpeg or ffprobe executable binaries are not found."""

    pass


class RenderExecutionError(RenderingError):
    """Raised when rendering process returns a non-zero exit code."""

    pass


class RenderTimeoutError(RenderingError):
    """Raised when rendering process exceeds execution timeout."""

    pass


class OutputValidationError(RenderingError):
    """Raised when output file validation checks fail (e.g. output missing or overwriting input)."""

    pass


class InputOverwriteError(OutputValidationError):
    """Raised when output path matches input path."""

    pass


class InvalidDimensionsError(RenderingError):
    """Raised when target width or height are invalid or exceed resource bounds."""

    pass
