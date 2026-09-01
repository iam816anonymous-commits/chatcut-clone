"""Unit tests for FilterGraph nodes and LabelAllocator determinism."""

from video_editor.compiler.filter_graph import FilterGraph, LabelAllocator


def test_label_allocator_determinism():
    allocator = LabelAllocator()
    assert allocator.allocate_video("v_seg") == "v_seg0"
    assert allocator.allocate_video("v_seg") == "v_seg1"
    assert allocator.allocate_audio("a_seg") == "a_seg0"
    assert allocator.allocate_audio("a_seg") == "a_seg1"


def test_filter_node_formatting():
    graph = FilterGraph()
    graph.add_node(
        inputs=["0:v"],
        filter_name="trim",
        params=["start=0.000000", "end=5.000000"],
        outputs=["v_trim0"],
    )
    graph.add_node(
        inputs=["v_trim0"],
        filter_name="setpts",
        params=["PTS-STARTPTS"],
        outputs=["v_norm0"],
    )

    filter_complex_str = graph.to_filter_complex_string()
    expected = (
        "[0:v] trim=start=0.000000:end=5.000000 [v_trim0];\n"
        "[v_trim0] setpts=PTS-STARTPTS [v_norm0]"
    )
    assert filter_complex_str == expected
