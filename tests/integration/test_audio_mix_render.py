"""End-to-End Multi-Track Audio Mixing Render Integration Test.

Demonstrates:
Video Track + Primary Audio Track + Secondary Music Audio Track -> Compiled RenderPlan -> FFmpeg Execution -> Rendered Media File
"""

import pytest
from video_editor.compiler.compiler import TimelineCompiler
from video_editor.engine.state_manager import StateManager
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.models import Asset, AudioConfig, Clip
from video_editor.ir.operations import AddClipOperation, AddTrackOperation
from video_editor.media.inspector import MediaInspector
from video_editor.rendering.ffmpeg import FFmpegRenderer
from video_editor.rendering.runtime import discover_runtime

HAS_FFMPEG = discover_runtime().ffmpeg_available


@pytest.mark.skipif(not HAS_FFMPEG, reason="FFmpeg runtime binary unavailable in test environment")
def test_audio_mixing_render(tmp_path):
    renderer = FFmpegRenderer()

    # 1. Create synthetic video fixture and synthetic audio fixture
    video_fixture = tmp_path / "video_source.mp4"
    music_fixture = tmp_path / "music_source.mp3"

    # Video fixture (3 seconds, black video + 440Hz tone)
    renderer.executor.execute([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=640x360:r=30:d=3.0",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=3.0",
        "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", str(video_fixture)
    ])

    # Music fixture (3 seconds, 880Hz tone)
    renderer.executor.execute([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=880:duration=3.0",
        "-c:a", "aac", str(music_fixture)
    ])

    assert video_fixture.exists() and video_fixture.stat().st_size > 0
    assert music_fixture.exists() and music_fixture.stat().st_size > 0

    # 2. Build VideoProject IR
    sm = StateManager()
    asset_v = Asset(type=AssetType.VIDEO, path=str(video_fixture), duration_us=3_000_000)
    asset_a = Asset(type=AssetType.AUDIO, path=str(music_fixture), duration_us=3_000_000)
    sm.register_asset(asset_v)
    sm.register_asset(asset_a)

    # Video Track
    sm.apply_operation(AddTrackOperation(track_name="Video", track_type=TrackType.VIDEO, index=0))
    v_track_id = sm.project.tracks[0].id
    clip_v = Clip(
        asset_id=asset_v.id,
        timeline_start_us=0,
        timeline_duration_us=3_000_000,
        source_start_us=0,
        source_duration_us=3_000_000,
    )
    sm.apply_operation(AddClipOperation(track_id=v_track_id, clip=clip_v))

    # Audio Track (Background Music)
    sm.apply_operation(AddTrackOperation(track_name="Music Track", track_type=TrackType.AUDIO, index=1))
    a_track_id = sm.project.tracks[1].id
    clip_a = Clip(
        asset_id=asset_a.id,
        timeline_start_us=1_000_000,  # Delayed 1 second
        timeline_duration_us=2_000_000,
        source_start_us=0,
        source_duration_us=2_000_000,
        audio=AudioConfig(volume=0.5),
    )
    sm.apply_operation(AddClipOperation(track_id=a_track_id, clip=clip_a))

    # 3. Compile IR to RenderPlan
    compiler = TimelineCompiler()
    plan = compiler.compile(sm.project)

    assert len(plan.audio_tracks) == 1
    assert plan.total_duration_us == 3_000_000

    # 4. Render Plan to Output MP4
    output_mp4 = tmp_path / "audio_mix_output.mp4"
    result = renderer.render_plan(plan, str(output_mp4))

    assert result.success is True
    assert output_mp4.exists()
    assert output_mp4.stat().st_size > 0

    # 5. Inspect Rendered Output
    inspector = MediaInspector()
    meta = inspector.inspect(str(output_mp4))
    assert meta.primary_audio_stream is not None
    assert meta.duration_us is not None
    assert abs(meta.duration_us - 3_000_000) < 300_000
