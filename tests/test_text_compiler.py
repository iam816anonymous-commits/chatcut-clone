"""Unit tests for TextCompiler drawtext filter overlay node generation."""

from video_editor.compiler.filter_graph import FilterGraph, LabelAllocator
from video_editor.compiler.models import (
    RenderOutputSettings,
    RenderPlan,
    RenderSegment,
    RenderTrack,
)
from video_editor.compiler.text_compiler import TextCompiler
from video_editor.ir.enums import TextAlignment, TrackType
from video_editor.ir.models import TextStyle


def test_text_compiler_overlay_generation():
    text_style = TextStyle(
        content="Cinematic Headline",
        font_size=64,
        font_color="#FFFF00",
        alignment=TextAlignment.CENTER,
    )

    t_track = RenderTrack(
        track_id="txt1",
        track_type=TrackType.TEXT,
        index=0,
        items=[
            RenderSegment(
                clip_id="c_txt",
                asset_id="",
                input_index=0,
                timeline_start_us=1_000_000,
                timeline_duration_us=4_000_000,
                source_start_us=0,
                source_duration_us=4_000_000,
                text_style=text_style,
            )
        ],
    )

    plan = RenderPlan(
        project_id="p1",
        total_duration_us=5_000_000,
        output_settings=RenderOutputSettings(width=1080, height=1920, fps=30.0),
        inputs=[],
        tracks=[t_track],
    )

    compiler = TextCompiler()
    graph = FilterGraph()
    allocator = LabelAllocator()

    out_label = compiler.compile_text_overlays(plan, graph, allocator, input_video_label="v_comp0")

    assert out_label == "txt_out0"
    spec = graph.to_filter_complex_string()

    assert "[v_comp0] drawtext=text='Cinematic Headline':fontcolor=0xFFFF00:fontsize=64:x=(w-tw)/2:y=(h-th)/2:enable='between(t\\,1.000000\\,5.000000)' [txt_out0]" in spec
