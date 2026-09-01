"""Execution Domain Exceptions for Real Rendering Runtime."""

from typing import Any, Dict, Optional


class RenderExecutionError(Exception):
    """Base exception for all rendering execution errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class FFmpegNotAvailableError(RenderExecutionError):
    """Raised when ffmpeg or ffprobe binaries are missing from environment."""

    pass


class FFmpegExecutionError(RenderExecutionError):
    """Raised when FFmpeg subprocess returns a non-zero exit code."""

    pass


class RenderTimeoutError(RenderExecutionError):
    """Raised when render process execution exceeds maximum allowed timeout."""

    pass


class RenderCancelledError(RenderExecutionError):
    """Raised when render execution is explicitly cancelled by caller."""

    pass


class OutputValidationError(RenderExecutionError):
    """Raised when post-render ffprobe validation checks fail."""

    pass


class ArtifactPublishingError(RenderExecutionError):
    """Raised when atomic file publishing or checksum calculation fails."""

    pass
