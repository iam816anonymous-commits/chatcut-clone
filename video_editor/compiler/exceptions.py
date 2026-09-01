"""Compiler Subsystem Domain Exceptions."""

from video_editor.ir.exceptions import VideoEditorError


class CompilerError(VideoEditorError):
    """Base exception for all timeline compilation errors."""

    pass


class RenderValidationError(CompilerError):
    """Raised when a project IR fails pre-compilation renderability checks."""

    pass


class UnsupportedTrackTypeError(RenderValidationError):
    """Raised when project contains track types unsupported by the compiler."""

    pass


class UnsupportedTimelineStructureError(RenderValidationError):
    """Raised when project contains unsupported timeline structures (e.g. multiple video tracks)."""

    pass


class UnrenderableProjectError(RenderValidationError):
    """Raised when project contains zero renderable tracks or clips."""

    pass


class InvalidRenderPlanError(CompilerError):
    """Raised when a generated RenderPlan fails integrity validation."""

    pass
