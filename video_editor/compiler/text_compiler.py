"""Text Track Compiler for TEXT and SUBTITLE Drawtext Filters."""

from typing import List
from video_editor.compiler.escaping import escape_drawtext_str
from video_editor.compiler.filter_graph import FilterGraph, LabelAllocator
from video_editor.compiler.models import RenderPlan, RenderSegment
from video_editor.ir.enums import TrackType, TextAlignment


class TextCompiler:
    """Compiles TEXT and SUBTITLE tracks into drawtext overlay filter nodes."""

    def compile_text_overlays(
        self,
        plan: RenderPlan,
        graph: FilterGraph,
        allocator: LabelAllocator,
        input_video_label: str,
    ) -> str:
        """Apply text and subtitle overlays onto the input video stream label.

        Returns:
            Output video stream label with text overlays applied.
        """
        text_tracks = [
            t for t in plan.tracks if t.track_type in (TrackType.TEXT, TrackType.SUBTITLE)
        ]
        text_tracks.sort(key=lambda t: t.index)

        current_label = input_video_label

        for track in text_tracks:
            for item in track.items:
                if isinstance(item, RenderSegment) and item.text_style:
                    txt = item.text_style
                    escaped_content = escape_drawtext_str(txt.content)
                    font_color = txt.font_color.replace("#", "0x")
                    font_size = txt.font_size

                    # Calculate position X / Y
                    if txt.alignment == TextAlignment.LEFT:
                        x_expr = "100"
                    elif txt.alignment == TextAlignment.RIGHT:
                        x_expr = "w-tw-100"
                    else:
                        x_expr = "(w-tw)/2"

                    y_expr = "(h-th)/2"

                    # Calculate timeline enable interval
                    t_start = item.timeline_start_us / 1_000_000.0
                    t_end = item.timeline_end_us / 1_000_000.0
                    enable_expr = f"between(t\\,{t_start:.6f}\\,{t_end:.6f})"

                    next_label = allocator.allocate_video("txt_out")

                    drawtext_params = [
                        f"text='{escaped_content}'",
                        f"fontcolor={font_color}",
                        f"fontsize={font_size}",
                        f"x={x_expr}",
                        f"y={y_expr}",
                        f"enable='{enable_expr}'",
                    ]

                    graph.add_node(
                        inputs=[current_label],
                        filter_name="drawtext",
                        params=drawtext_params,
                        outputs=[next_label],
                    )

                    current_label = next_label

        return current_label
