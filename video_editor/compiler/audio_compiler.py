"""Multi-Track Audio Compiler for Timeline Alignment, Volume & Mixing."""

from typing import List, Optional
from video_editor.compiler.filter_graph import FilterGraph, LabelAllocator
from video_editor.compiler.models import RenderGap, RenderPlan, RenderSegment
from video_editor.compiler.speed import compile_audio_speed_filters
from video_editor.ir.enums import TrackType


class AudioCompiler:
    """Compiles audio tracks, applies adelay timeline alignment, volume, and amix mixing."""

    def compile_audio_mix(
        self,
        plan: RenderPlan,
        graph: FilterGraph,
        allocator: LabelAllocator,
    ) -> Optional[str]:
        """Compile audio tracks, align with adelay, adjust gain, and mix via amix.

        Returns:
            Output stream label for mixed audio stream, or None if project has no audio streams.
        """
        sample_rate = plan.output_settings.audio_sample_rate
        audio_tracks = [t for t in plan.tracks if t.track_type == TrackType.AUDIO]

        processed_audio_labels: List[str] = []

        for track in audio_tracks:
            for item in track.items:
                if isinstance(item, RenderSegment):
                    s_start = f"{item.source_start_us / 1_000_000.0:.6f}"
                    s_end = f"{(item.source_start_us + item.source_duration_us) / 1_000_000.0:.6f}"
                    delay_ms = int(item.timeline_start_us / 1_000.0)

                    # 1. Trim
                    t_label = allocator.allocate_audio("a_trim")
                    graph.add_node(
                        inputs=[f"{item.input_index}:a"],
                        filter_name="atrim",
                        params=[f"start={s_start}", f"end={s_end}"],
                        outputs=[t_label],
                    )

                    # 2. PTS Reset
                    pts_label = allocator.allocate_audio("a_pts")
                    graph.add_node(
                        inputs=[t_label],
                        filter_name="asetpts",
                        params=["PTS-STARTPTS"],
                        outputs=[pts_label],
                    )

                    last_audio_label = pts_label

                    # Speed Factor (chained atempo filters)
                    if item.speed != 1.0:
                        atempo_filters = compile_audio_speed_filters(item.speed)
                        for atempo_str in atempo_filters:
                            atempo_params = atempo_str.split("=", 1)[1]
                            spd_label = allocator.allocate_audio("a_spd")
                            graph.add_node(
                                inputs=[last_audio_label],
                                filter_name="atempo",
                                params=[atempo_params],
                                outputs=[spd_label],
                            )
                            last_audio_label = spd_label

                    # 3. Format Normalization
                    fmt_label = allocator.allocate_audio("a_fmt")
                    graph.add_node(
                        inputs=[last_audio_label],
                        filter_name="aformat",
                        params=[f"sample_rates={sample_rate}", "channel_layouts=stereo"],
                        outputs=[fmt_label],
                    )

                    # 4. Volume Gain Adjustment
                    vol_label = allocator.allocate_audio("a_vol")
                    graph.add_node(
                        inputs=[fmt_label],
                        filter_name="volume",
                        params=[f"{item.volume:.2f}"],
                        outputs=[vol_label],
                    )

                    # 5. Timeline Alignment via adelay
                    del_label = allocator.allocate_audio("a_del")
                    graph.add_node(
                        inputs=[vol_label],
                        filter_name="adelay",
                        params=[f"delays={delay_ms}|{delay_ms}"],
                        outputs=[del_label],
                    )

                    processed_audio_labels.append(del_label)

        if not processed_audio_labels:
            return None

        if len(processed_audio_labels) == 1:
            return processed_audio_labels[0]

        # Mix multiple streams via amix
        mix_label = allocator.allocate_audio("a_mix")
        graph.add_node(
            inputs=processed_audio_labels,
            filter_name="amix",
            params=[f"inputs={len(processed_audio_labels)}", "duration=longest", "dropout_transition=0"],
            outputs=[mix_label],
        )

        return mix_label
