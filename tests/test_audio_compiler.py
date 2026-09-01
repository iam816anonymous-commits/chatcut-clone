"""Unit tests for AudioCompiler trimming, adelay timeline alignment, and volume gain adjustment."""

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


def test_audio_compiler_single_track_alignment_and_volume():
    inp = RenderInput(input_index=0, asset_id="a1", file_path="/audio.mp3")
    a_track = RenderTrack(
        track_id="t1",
        track_type=TrackType.AUDIO,
        index=0,
        items=[
            RenderSegment(
                clip_id="c1",
                asset_id="a1",
                input_index=0,
                timeline_start_us=5_000_000,  # Starts at 5s on timeline -> adelay=5000|5000
                timeline_duration_us=4_000_000,
                source_start_us=1_000_000,
                source_duration_us=4_000_000,
                volume=0.5,
            )
        ],
    )

    plan = RenderPlan(
        project_id="p1",
        total_duration_us=10_000_000,
        output_settings=RenderOutputSettings(width=1080, height=1920, fps=30.0, audio_sample_rate=48000),
        inputs=[inp],
        tracks=[a_track],
    )

    compiler = AudioCompiler()
    graph = FilterGraph()
    allocator = LabelAllocator()

    out_label = compiler.compile_audio_mix(plan, graph, allocator)

    assert out_label == "a_del0"
    spec = graph.to_filter_complex_string()

    assert "atrim=start=1.000000:end=5.000000" in spec
    assert "asetpts=PTS-STARTPTS" in spec
    assert "aformat=sample_rates=48000:channel_layouts=stereo" in spec
    assert "volume=volume=0.50" in spec
    assert "adelay=delays=5000|5000" in spec
