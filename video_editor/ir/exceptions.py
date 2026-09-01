"""Domain Exceptions for Universal Video Editing IR and State Engine."""

from typing import Any, Dict, Optional


class VideoEditorError(Exception):
    """Base exception for all video editor errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AssetNotFoundError(VideoEditorError):
    """Raised when a referenced asset ID does not exist in project inventory."""

    pass


class TrackNotFoundError(VideoEditorError):
    """Raised when a referenced track ID does not exist in project."""

    pass


class ClipNotFoundError(VideoEditorError):
    """Raised when a referenced clip ID does not exist in project."""

    pass


class InvalidTimeRangeError(VideoEditorError):
    """Raised when time range boundaries or durations are invalid."""

    pass


class TrackLockedError(VideoEditorError):
    """Raised when attempting to modify a locked track."""

    pass


class InvalidTrackTypeError(VideoEditorError):
    """Raised when a clip is placed on an incompatible track type."""

    pass


class ClipOverlapError(VideoEditorError):
    """Raised when clips overlap on a single-clip-per-time track."""

    pass


class InvalidOperationError(VideoEditorError):
    """Raised when an operation payload is malformed or invalid."""

    pass


class ProjectIntegrityError(VideoEditorError):
    """Raised when overall project state integrity checks fail."""

    pass


class HistoryError(VideoEditorError):
    """Raised when undo/redo stack limits or operations fail."""

    pass
