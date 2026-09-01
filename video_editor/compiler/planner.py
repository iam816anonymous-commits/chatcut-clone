"""RenderPlanner: Translates pure RenderPlan into executable FFmpegCommand."""

from video_editor.compiler.filter_graph import FilterGraph, LabelAllocator
from video_editor.compiler.models import RenderGap, RenderPlan, RenderSegment
from video_editor.ir.enums import TrackType
from video_editor.rendering.command import FFmpegCommand


class RenderPlanner:
    """Translates a compiled RenderPlan into an executable FFmpegCommand with a filter_complex graph."""

    def plan_to_command(self, plan: RenderPlan, output_path: str, ffmpeg_path: str = "ffmpeg") -> FFmpegCommand:
        """Construct FFmpegCommand argument array for a RenderPlan."""
        # 1. Base input arguments
        arguments = ["-y"]
        for inp in plan.inputs:
            arguments.extend(["-i", inp.file_path])

        # 2. Construct FilterGraph
        graph = FilterGraph()
        allocator = LabelAllocator()

        v_concat_inputs = []
        a_concat_inputs = []

        # Process Primary Video Track
        v_track = plan.primary_video_track
        if v_track:
            for item in v_track.items:
                if isinstance(item, RenderSegment):
                    v_label = allocator.allocate_video("v_seg")
                    s_start = f"{item.source_start_us / 1_000_000.0:.6f}"
                    s_end = f"{(item.source_start_us + item.source_duration_us) / 1_000_000.0:.6f}"

                    # Trim node
                    t_label = allocator.allocate_video("v_trim")
                    graph.add_node(
                        inputs=[f"{item.input_index}:v"],
                        filter_name="trim",
                        params=[f"start={s_start}", f"end={s_end}"],
                        outputs=[t_label],
                    )

                    # PTS reset, scale, and fps node
                    p_label = allocator.allocate_video("v_norm")
                    graph.add_node(
                        inputs=[t_label],
                        filter_name="setpts",
                        params=["PTS-STARTPTS"],
                        outputs=[p_label],
                    )

                    sc_label = allocator.allocate_video("v_sc")
                    graph.add_node(
                        inputs=[p_label],
                        filter_name="scale",
                        params=[f"{plan.output_settings.width}:{plan.output_settings.height}"],
                        outputs=[sc_label],
                    )

                    graph.add_node(
                        inputs=[sc_label],
                        filter_name="fps",
                        params=[f"{plan.output_settings.fps}"],
                        outputs=[v_label],
                    )
                    v_concat_inputs.append(v_label)

                elif isinstance(item, RenderGap):
                    gap_label = allocator.allocate_video("v_gap")
                    duration_sec = f"{item.timeline_duration_us / 1_000_000.0:.6f}"
                    graph.add_node(
                        inputs=[],
                        filter_name="color",
                        params=[
                            "c=black",
                            f"s={plan.output_settings.width}x{plan.output_settings.height}",
                            f"r={plan.output_settings.fps}",
                            f"d={duration_sec}",
                        ],
                        outputs=[gap_label],
                    )
                    v_concat_inputs.append(gap_label)

        # Process Primary Audio Track
        a_tracks = plan.audio_tracks
        if a_tracks:
            a_track = a_tracks[0]  # Primary audio track
            for item in a_track.items:
                if isinstance(item, RenderSegment):
                    a_label = allocator.allocate_audio("a_seg")
                    s_start = f"{item.source_start_us / 1_000_000.0:.6f}"
                    s_end = f"{(item.source_start_us + item.source_duration_us) / 1_000_000.0:.6f}"

                    t_label = allocator.allocate_audio("a_trim")
                    graph.add_node(
                        inputs=[f"{item.input_index}:a"],
                        filter_name="atrim",
                        params=[f"start={s_start}", f"end={s_end}"],
                        outputs=[t_label],
                    )

                    norm_label = allocator.allocate_audio("a_norm")
                    graph.add_node(
                        inputs=[t_label],
                        filter_name="asetpts",
                        params=["PTS-STARTPTS"],
                        outputs=[norm_label],
                    )

                    graph.add_node(
                        inputs=[norm_label],
                        filter_name="aformat",
                        params=[
                            f"sample_rates={plan.output_settings.audio_sample_rate}",
                            "channel_layouts=stereo",
                        ],
                        outputs=[a_label],
                    )
                    a_concat_inputs.append(a_label)

                elif isinstance(item, RenderGap):
                    gap_label = allocator.allocate_audio("a_gap")
                    duration_sec = f"{item.timeline_duration_us / 1_000_000.0:.6f}"
                    graph.add_node(
                        inputs=[],
                        filter_name="anullsrc",
                        params=[
                            f"r={plan.output_settings.audio_sample_rate}",
                            "cl=stereo",
                            f"d={duration_sec}",
                        ],
                        outputs=[gap_label],
                    )
                    a_concat_inputs.append(gap_label)

        # 3. Concatenate Concat Nodes
        has_v = len(v_concat_inputs) > 0
        has_a = len(a_concat_inputs) > 0

        if has_v and not has_a:
            # Video-only project concat
            outv_label = "outv"
            graph.add_node(
                inputs=v_concat_inputs,
                filter_name="concat",
                params=[f"n={len(v_concat_inputs)}", "v=1", "a=0"],
                outputs=[outv_label],
            )
            filter_complex_str = graph.to_filter_complex_string()
            arguments.extend(["-filter_complex", filter_complex_str, "-map", f"[{outv_label}]"])

        elif has_v and has_a:
            # Video + Audio project concat
            outv_label = "outv"
            outa_label = "outa"

            # Concat video stream
            graph.add_node(
                inputs=v_concat_inputs,
                filter_name="concat",
                params=[f"n={len(v_concat_inputs)}", "v=1", "a=0"],
                outputs=[outv_label],
            )
            # Concat audio stream
            graph.add_node(
                inputs=a_concat_inputs,
                filter_name="concat",
                params=[f"n={len(a_concat_inputs)}", "v=0", "a=1"],
                outputs=[outa_label],
            )

            filter_complex_str = graph.to_filter_complex_string()
            arguments.extend([
                "-filter_complex", filter_complex_str,
                "-map", f"[{outv_label}]",
                "-map", f"[{outa_label}]",
            ])

        elif not has_v and has_a:
            # Audio-only project concat
            outa_label = "outa"
            graph.add_node(
                inputs=a_concat_inputs,
                filter_name="concat",
                params=[f"n={len(a_concat_inputs)}", "v=0", "a=1"],
                outputs=[outa_label],
            )
            filter_complex_str = graph.to_filter_complex_string()
            arguments.extend(["-filter_complex", filter_complex_str, "-map", f"[{outa_label}]"])

        # Codec & Output formatting
        if has_v:
            arguments.extend(["-c:v", plan.output_settings.video_codec, "-pix_fmt", "yuv420p"])
        if has_a:
            arguments.extend(["-c:a", plan.output_settings.audio_codec])

        arguments.append(output_path)

        return FFmpegCommand(executable=ffmpeg_path, arguments=arguments)
