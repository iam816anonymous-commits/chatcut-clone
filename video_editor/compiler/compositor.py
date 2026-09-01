"""Multi-Track Video Compositor for Z-Ordered Visual Overlay Chains."""

from typing import List
from video_editor.compiler.effects import compile_effect_filter
from video_editor.compiler.filter_graph import FilterGraph, LabelAllocator
from video_editor.compiler.models import RenderGap, RenderPlan, RenderSegment, RenderTrack
from video_editor.compiler.speed import compile_video_speed_filter
from video_editor.ir.enums import TrackType


class VideoCompositor:
    """Compiles Z-ordered video tracks into an FFmpeg overlay filter graph chain."""

    def compile_visual_composition(
        self,
        plan: RenderPlan,
        graph: FilterGraph,
        allocator: LabelAllocator,
    ) -> str:
        """Compile video tracks in deterministic z-index order and layer overlays on canvas.

        Returns:
            Output stream label for composite visual stream.
        """
        canvas_width = plan.output_settings.width
        canvas_height = plan.output_settings.height
        fps = plan.output_settings.fps
        duration_sec = f"{plan.total_duration_us / 1_000_000.0:.6f}"

        # 1. Base Canvas Stream
        bg_label = allocator.allocate_video("v_bg")
        graph.add_node(
            inputs=[],
            filter_name="color",
            params=[
                "c=0x000000",
                f"s={canvas_width}x{canvas_height}",
                f"r={fps}",
                f"d={duration_sec}",
            ],
            outputs=[bg_label],
        )

        current_base_label = bg_label

        # 2. Collect Video Tracks sorted by z-index
        video_tracks = [t for t in plan.tracks if t.track_type == TrackType.VIDEO]
        video_tracks.sort(key=lambda t: t.index)

        # 3. Layer each video track onto composite canvas via overlay filters
        for track in video_tracks:
            for item in track.items:
                if isinstance(item, RenderSegment):
                    s_start = f"{item.source_start_us / 1_000_000.0:.6f}"
                    s_end = f"{(item.source_start_us + item.source_duration_us) / 1_000_000.0:.6f}"
                    t_start = item.timeline_start_us / 1_000_000.0
                    t_end = item.timeline_end_us / 1_000_000.0

                    # Trim
                    t_label = allocator.allocate_video("v_trim")
                    graph.add_node(
                        inputs=[f"{item.input_index}:v"],
                        filter_name="trim",
                        params=[f"start={s_start}", f"end={s_end}"],
                        outputs=[t_label],
                    )

                    # PTS Reset & Speed Factor
                    pts_label = allocator.allocate_video("v_pts")
                    speed_filter_spec = compile_video_speed_filter(item.speed)
                    pts_param = f"PTS-STARTPTS+{speed_filter_spec.split('=', 1)[1]}" if "setpts=" in speed_filter_spec else "PTS-STARTPTS"
                    graph.add_node(
                        inputs=[t_label],
                        filter_name="setpts",
                        params=[pts_param],
                        outputs=[pts_label],
                    )

                    last_effect_label = pts_label

                    # Visual Effect Chain Processing
                    if item.effects:
                        for eff in item.effects:
                            eff_filter = compile_effect_filter(eff)
                            eff_name = eff_filter.split("=", 1)[0]
                            eff_params = eff_filter.split("=", 1)[1] if "=" in eff_filter else ""
                            eff_label = allocator.allocate_video("v_eff")
                            graph.add_node(
                                inputs=[last_effect_label],
                                filter_name=eff_name,
                                params=[eff_params] if eff_params else [],
                                outputs=[eff_label],
                            )
                            last_effect_label = eff_label

                    # Scale to canvas size or transform scale
                    scale_w = int(canvas_width * item.transform.scale_x)
                    scale_h = int(canvas_height * item.transform.scale_y)
                    if scale_w < 1:
                        scale_w = 1
                    if scale_h < 1:
                        scale_h = 1

                    sc_label = allocator.allocate_video("v_sc")
                    graph.add_node(
                        inputs=[last_effect_label],
                        filter_name="scale",
                        params=[f"{scale_w}:{scale_h}"],
                        outputs=[sc_label],
                    )

                    # FPS Normalization
                    fps_label = allocator.allocate_video("v_fps")
                    graph.add_node(
                        inputs=[sc_label],
                        filter_name="fps",
                        params=[f"{fps}"],
                        outputs=[fps_label],
                    )

                    # Position offsets
                    offset_x = int((canvas_width - scale_w) / 2.0 + item.transform.position_x)
                    offset_y = int((canvas_height - scale_h) / 2.0 + item.transform.position_y)

                    # Overlay onto current base canvas with timeline enable interval
                    next_base_label = allocator.allocate_video("v_comp")
                    enable_expr = f"between(t\\,{t_start:.6f}\\,{t_end:.6f})"

                    graph.add_node(
                        inputs=[current_base_label, fps_label],
                        filter_name="overlay",
                        params=[
                            f"x={offset_x}",
                            f"y={offset_y}",
                            f"enable='{enable_expr}'",
                        ],
                        outputs=[next_base_label],
                    )

                    current_base_label = next_base_label

        return current_base_label
