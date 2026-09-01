"""Abstract Base Class for Video Rendering Adapters."""

from abc import ABC, abstractmethod
from typing import Callable, Optional
from video_editor.ir.models import VideoProject
from video_editor.rendering.executor import ProcessResult


class BaseRenderer(ABC):
    """Abstract interface for all video rendering backends.

    Renderers are strictly read-only consumers of the VideoProject IR.
    Renderers MUST NEVER mutate StateManager or project state directly.
    """

    @abstractmethod
    def render(
        self,
        project: VideoProject,
        output_path: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> ProcessResult:
        """Render VideoProject state to an output media file on local disk.

        Args:
            project: Read-only VideoProject IR state instance.
            output_path: Canonical target destination path on local disk.
            progress_callback: Optional progress callback function.

        Returns:
            ProcessResult containing execution stats and status.
        """
        pass
