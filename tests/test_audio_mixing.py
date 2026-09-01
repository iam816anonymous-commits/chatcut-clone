"""Unit tests for AudioCompiler multi-track amix filter node generation."""

from video_editor.compiler.audio_compiler import AudioCompiler
from video_editor.compiler.filter_graph import FilterGraph, LabelAllocator
from video_editor.compiler.models import (
    RenderInput,
    RenderOutputSettings,
    RenderPlan,
    RenderSegment,
    RenderTrack,
)
from video_editor.ir.enums import TrackType


def test_audio_compiler_multi_track_mixing():
    inp1 = RenderInput(input_index=0, asset_id="a1", file_path="/voice.mp3")
    inp2 = RenderInput(input_index=1, asset_id="a2", file_path="/music.mp3")

    a_track1 = RenderTrack(
        track_id="t1",
        track_type=TrackType.AUDIO,
        index=0,
        items=[
            RenderSegment(
                clip_id="c1",
                asset_id="a1",
                input_index=0,
                timeline_start_us=0,
                timeline_duration_us=5_000_000,
                source_start_us=0,
                source_duration_us=5_000_000,
                volume=1.0,
            )
        ],
    )

    a_track2 = RenderTrack(
        track_id="t2",
        track_type=TrackType.AUDIO,
        index=1,
        items=[
            RenderSegment(
                clip_id="c2",
                asset_id="a2",
                input_index=1,
                timeline_start_us=2_000_000,  # Overlaps voice track
                timeline_duration_us=5_000_000,
                source_start_us=0,
                source_duration_us=5_000_000,
                volume=0.3,
            )
        ],
    )

    plan = RenderPlan(
        project_id="p1",
        total_duration_us=7_000_000,
        output_settings=RenderOutputSettings(width=1080, height=1920, fps=30.0, audio_sample_rate=48000),
        inputs=[inp1, inp2],
        tracks=[a_track1, a_track2],
    )

    compiler = AudioCompiler()
    graph = FilterGraph()
    allocator = LabelAllocator()

    out_label = compiler.compile_audio_mix(plan, graph, allocator)

    assert out_label == "a_mix0"
    spec = graph.to_filter_complex_string()

    assert "[a_del0][a_del1] amix=inputs=2:duration=longest:dropout_transition=0 [a_mix0]" in spec
