"""Unit tests for complex multi-track projects containing video, PIP, audio, and text."""

from video_editor.compiler.compiler import TimelineCompiler
from video_editor.compiler.planner import RenderPlanner
from video_editor.ir.enums import AssetType, TextAlignment, TrackType
from video_editor.ir.models import Asset, Clip, TextStyle, Track, Transform, VideoProject


def test_multitrack_complex_project_compilation(tmp_path):
    v_file = tmp_path / "main.mp4"
    v_file.write_text("dummy")
    pip_file = tmp_path / "pip.mp4"
    pip_file.write_text("dummy")
    a_file = tmp_path / "music.mp3"
    a_file.write_text("dummy")

    project = VideoProject()
    asset_v = Asset(type=AssetType.VIDEO, path=str(v_file), duration_us=10_000_000)
    asset_pip = Asset(type=AssetType.VIDEO, path=str(pip_file), duration_us=10_000_000)
    asset_a = Asset(type=AssetType.AUDIO, path=str(a_file), duration_us=10_000_000)
    project.assets[asset_v.id] = asset_v
    project.assets[asset_pip.id] = asset_pip
    project.assets[asset_a.id] = asset_a

    # 1. Main Video Track (Index 0)
    t_v1 = Track(name="Main Video", type=TrackType.VIDEO, index=0)
    c_v1 = Clip(
        asset_id=asset_v.id,
        timeline_start_us=0,
        timeline_duration_us=10_000_000,
        source_start_us=0,
        source_duration_us=10_000_000,
    )
    t_v1.clips.append(c_v1)

    # 2. PIP Overlay Track (Index 1)
    t_v2 = Track(name="PIP Overlay", type=TrackType.VIDEO, index=1)
    c_v2 = Clip(
        asset_id=asset_pip.id,
        timeline_start_us=2_000_000,
        timeline_duration_us=4_000_000,
        source_start_us=0,
        source_duration_us=4_000_000,
        transform=Transform(position_x=100.0, position_y=200.0, scale_x=0.5, scale_y=0.5),
    )
    t_v2.clips.append(c_v2)

    # 3. Text Overlay Track (Index 2)
    t_txt = Track(name="Title", type=TrackType.TEXT, index=2)
    c_txt = Clip(
        timeline_start_us=1_000_000,
        timeline_duration_us=5_000_000,
        source_start_us=0,
        source_duration_us=5_000_000,
        text=TextStyle(content="Sample Title", font_size=48, alignment=TextAlignment.CENTER),
    )
    t_txt.clips.append(c_txt)

    # 4. Audio Track (Index 3)
    t_a1 = Track(name="Music", type=TrackType.AUDIO, index=3)
    c_a1 = Clip(
        asset_id=asset_a.id,
        timeline_start_us=0,
        timeline_duration_us=10_000_000,
        source_start_us=0,
        source_duration_us=10_000_000,
        audio=Asset(type=AssetType.AUDIO, path=str(a_file), duration_us=10_000_000),  # dummy fallback
    )
    t_a1.clips.append(c_a1)

    project.tracks.extend([t_v1, t_v2, t_txt, t_a1])

    compiler = TimelineCompiler()
    plan = compiler.compile(project)

    assert len(plan.video_tracks) == 2
    assert len(plan.audio_tracks) == 1
    assert len(plan.text_tracks) == 1

    planner = RenderPlanner()
    cmd = planner.plan_to_command(plan, "/out/render.mp4")
    cmd_str = cmd.to_display_string()

    assert "-filter_complex" in cmd_str
    assert "overlay=" in cmd_str
    assert "drawtext=" in cmd_str
    assert "adelay=" in cmd_str
    assert "Sample Title" in cmd_str
