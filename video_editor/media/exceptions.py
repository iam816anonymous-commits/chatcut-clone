"""Media Subsystem Domain Exceptions."""

from video_editor.ir.exceptions import VideoEditorError


class MediaError(VideoEditorError):
    """Base exception for all media inspection and asset resolution errors."""

    pass


class InputFileNotFoundError(MediaError):
    """Raised when an input source file does not exist on local disk."""

    pass


class InvalidMediaError(MediaError):
    """Raised when media inspection fails or file is corrupted/unreadable."""

    pass


class MediaInspectionError(MediaError):
    """Raised when media inspection process execution fails."""

    pass
