"""Canvas Normalization and Background Source Generation Engine."""

from typing import Tuple
from video_editor.compiler.filter_graph import FilterGraph
from video_editor.ir.models import ProjectSettings


class CanvasNormalizer:
    """Normalizes project canvas properties and generates background stream filter nodes."""

    @staticmethod
    def get_canvas_dimensions(settings: ProjectSettings) -> Tuple[int, int, float, str]:
        """Extract canvas width, height, fps, and background hex color."""
        return settings.width, settings.height, settings.fps, settings.background_color

    @staticmethod
    def add_background_color_node(
        graph: FilterGraph,
        width: int,
        height: int,
        fps: float,
        duration_us: int,
        color_hex: str = "#000000",
        output_label: str = "bg_canvas",
    ) -> str:
        """Add an FFmpeg color filter node producing a solid background canvas stream."""
        duration_sec = f"{duration_us / 1_000_000.0:.6f}"
        clean_color = color_hex.replace("#", "0x")
        if not clean_color.startswith("0x"):
            clean_color = "black"

        graph.add_node(
            inputs=[],
            filter_name="color",
            params=[
                f"c={clean_color}",
                f"s={width}x{height}",
                f"r={fps}",
                f"d={duration_sec}",
            ],
            outputs=[output_label],
        )
        return output_label

    @staticmethod
    def add_background_silence_node(
        graph: FilterGraph,
        duration_us: int,
        sample_rate: int = 48000,
        output_label: str = "bg_silence",
    ) -> str:
        """Add an FFmpeg anullsrc filter node producing a silent audio background stream."""
        duration_sec = f"{duration_us / 1_000_000.0:.6f}"
        graph.add_node(
            inputs=[],
            filter_name="anullsrc",
            params=[
                f"r={sample_rate}",
                "cl=stereo",
                f"d={duration_sec}",
            ],
            outputs=[output_label],
        )
        return output_label
