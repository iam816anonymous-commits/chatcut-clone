"""End-to-End Real Project Render Integration Test.

Demonstrates:
Project IR -> Validation -> Asset Resolution -> Timeline Compilation -> RenderPlan -> FFmpeg Execution -> Output Media File
"""

import pytest
import shutil
from video_editor.compiler.compiler import TimelineCompiler
from video_editor.engine.state_manager import StateManager
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.models import Asset, Clip
from video_editor.ir.operations import AddClipOperation, AddTrackOperation
from video_editor.media.inspector import MediaInspector
from video_editor.rendering.ffmpeg import FFmpegRenderer
from video_editor.rendering.runtime import discover_runtime

# Skip integration test if FFmpeg binary is missing from PATH
HAS_FFMPEG = discover_runtime().ffmpeg_available


@pytest.mark.skipif(not HAS_FFMPEG, reason="FFmpeg runtime binary unavailable in test environment")
def test_end_to_end_project_render(tmp_path):
    renderer = FFmpegRenderer()

    # 1. Create two tiny 2-second synthetic video media fixtures using FFmpeg
    fixture_a = tmp_path / "video_a.mp4"
    fixture_b = tmp_path / "video_b.mp4"

    # Generate Fixture A (red test source)
    renderer.executor.execute([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=red:s=640x360:r=30:d=2.0",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=2.0",
        "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", str(fixture_a)
    ])

    # Generate Fixture B (blue test source)
    renderer.executor.execute([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=640x360:r=30:d=2.0",
        "-f", "lavfi", "-i", "sine=frequency=880:duration=2.0",
        "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", str(fixture_b)
    ])

    assert fixture_a.exists() and fixture_a.stat().st_size > 0
    assert fixture_b.exists() and fixture_b.stat().st_size > 0

    # 2. Build VideoProject IR using StateManager
    sm = StateManager()
    asset_a = Asset(type=AssetType.VIDEO, path=str(fixture_a), duration_us=2_000_000)
    asset_b = Asset(type=AssetType.VIDEO, path=str(fixture_b), duration_us=2_000_000)
    sm.register_asset(asset_a)
    sm.register_asset(asset_b)

    # Add Video Track
    sm.apply_operation(AddTrackOperation(track_name="V1", track_type=TrackType.VIDEO))
    v_track_id = sm.project.tracks[0].id

    # Clip A: source 0s->2s, timeline 0s->2s
    clip_a = Clip(
        asset_id=asset_a.id,
        timeline_start_us=0,
        timeline_duration_us=2_000_000,
        source_start_us=0,
        source_duration_us=2_000_000,
    )
    # Clip B: source 0s->2s, timeline 2s->4s (sequential concat)
    clip_b = Clip(
        asset_id=asset_b.id,
        timeline_start_us=2_000_000,
        timeline_duration_us=2_000_000,
        source_start_us=0,
        source_duration_us=2_000_000,
    )
    sm.apply_operation(AddClipOperation(track_id=v_track_id, clip=clip_a))
    sm.apply_operation(AddClipOperation(track_id=v_track_id, clip=clip_b))

    # 3. Compile Project IR to RenderPlan
    compiler = TimelineCompiler()
    plan = compiler.compile(sm.project)

    assert plan.total_duration_us == 4_000_000
    assert len(plan.inputs) == 2

    # 4. Render Plan to Output MP4
    output_mp4 = tmp_path / "end_to_end_output.mp4"
    result = renderer.render_plan(plan, str(output_mp4))

    assert result.success is True
    assert output_mp4.exists()
    assert output_mp4.stat().st_size > 0

    # 5. Inspect Rendered Output via MediaInspector
    inspector = MediaInspector()
    meta = inspector.inspect(str(output_mp4))

    assert meta.duration_us is not None
    # Verify rendered duration approximately equals 4.0s (within 0.3s tolerance)
    assert abs(meta.duration_us - 4_000_000) < 300_000
    assert meta.primary_video_stream is not None
