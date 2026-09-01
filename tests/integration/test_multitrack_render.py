"""End-to-End Multi-Track Video Overlay Render Integration Test.

Demonstrates:
Main Video Track (Z-Index 0) + Picture-In-Picture Overlay Video Track (Z-Index 1) -> Compiled RenderPlan -> FFmpeg Execution -> Rendered Media File
"""

import pytest
from video_editor.compiler.compiler import TimelineCompiler
from video_editor.engine.state_manager import StateManager
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.models import Asset, Clip, Transform
from video_editor.ir.operations import AddClipOperation, AddTrackOperation
from video_editor.media.inspector import MediaInspector
from video_editor.rendering.ffmpeg import FFmpegRenderer
from video_editor.rendering.runtime import discover_runtime

HAS_FFMPEG = discover_runtime().ffmpeg_available


@pytest.mark.skipif(not HAS_FFMPEG, reason="FFmpeg runtime binary unavailable in test environment")
def test_multitrack_video_overlay_render(tmp_path):
    renderer = FFmpegRenderer()

    # 1. Create two synthetic 4-second video media fixtures
    bg_fixture = tmp_path / "bg_video.mp4"
    pip_fixture = tmp_path / "pip_video.mp4"

    # Main BG video (green)
    renderer.executor.execute([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=green:s=1280x720:r=30:d=4.0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(bg_fixture)
    ])

    # PIP overlay video (blue)
    renderer.executor.execute([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=640x360:r=30:d=2.0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(pip_fixture)
    ])

    assert bg_fixture.exists() and bg_fixture.stat().st_size > 0
    assert pip_fixture.exists() and pip_fixture.stat().st_size > 0

    # 2. Build VideoProject IR
    sm = StateManager()
    asset_bg = Asset(type=AssetType.VIDEO, path=str(bg_fixture), duration_us=4_000_000)
    asset_pip = Asset(type=AssetType.VIDEO, path=str(pip_fixture), duration_us=2_000_000)
    sm.register_asset(asset_bg)
    sm.register_asset(asset_pip)

    # Main BG Track (Index 0)
    sm.apply_operation(AddTrackOperation(track_name="BG Track", track_type=TrackType.VIDEO, index=0))
    t0_id = sm.project.tracks[0].id
    clip_bg = Clip(
        asset_id=asset_bg.id,
        timeline_start_us=0,
        timeline_duration_us=4_000_000,
        source_start_us=0,
        source_duration_us=4_000_000,
    )
    sm.apply_operation(AddClipOperation(track_id=t0_id, clip=clip_bg))

    # PIP Overlay Track (Index 1)
    sm.apply_operation(AddTrackOperation(track_name="PIP Track", track_type=TrackType.VIDEO, index=1))
    t1_id = sm.project.tracks[1].id
    clip_pip = Clip(
        asset_id=asset_pip.id,
        timeline_start_us=1_000_000,  # PIP appears at 1s to 3s
        timeline_duration_us=2_000_000,
        source_start_us=0,
        source_duration_us=2_000_000,
        transform=Transform(position_x=100.0, position_y=50.0, scale_x=0.5, scale_y=0.5),
    )
    sm.apply_operation(AddClipOperation(track_id=t1_id, clip=clip_pip))

    # 3. Compile IR to RenderPlan
    compiler = TimelineCompiler()
    plan = compiler.compile(sm.project)

    assert len(plan.video_tracks) == 2
    assert plan.total_duration_us == 4_000_000

    # 4. Render Plan to Output MP4
    output_mp4 = tmp_path / "multitrack_pip_output.mp4"
    result = renderer.render_plan(plan, str(output_mp4))

    assert result.success is True
    assert output_mp4.exists()
    assert output_mp4.stat().st_size > 0

    # 5. Inspect Rendered Output
    inspector = MediaInspector()
    meta = inspector.inspect(str(output_mp4))
    assert meta.duration_us is not None
    assert abs(meta.duration_us - 4_000_000) < 300_000
