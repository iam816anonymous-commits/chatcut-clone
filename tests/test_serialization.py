"""Unit tests for VideoProject JSON serialization and deserialization."""

from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.models import Asset, Clip, Track, VideoProject
from video_editor.ir.validation import validate_project_integrity


def test_project_json_roundtrip():
    project = VideoProject(name="Test Roundtrip Project")
    asset = Asset(type=AssetType.VIDEO, path="/media/clip.mp4", duration_us=15_000_000)
    project.assets[asset.id] = asset

    track = Track(name="Main Video", type=TrackType.VIDEO, index=0)
    clip = Clip(
        asset_id=asset.id,
        timeline_start_us=1_000_000,
        timeline_duration_us=5_000_000,
        source_start_us=2_000_000,
        source_duration_us=5_000_000,
    )
    track.clips.append(clip)
    project.tracks.append(track)

    # Serialize to JSON string
    json_str = project.model_dump_json()

    # Deserialize back to VideoProject
    reconstructed = VideoProject.model_validate_json(json_str)

    assert reconstructed.id == project.id
    assert reconstructed.name == project.name
    assert reconstructed.duration_us == project.duration_us
    assert len(reconstructed.assets) == 1
    assert reconstructed.assets[asset.id].path == asset.path
    assert len(reconstructed.tracks) == 1
    assert reconstructed.tracks[0].clips[0].id == clip.id

    validate_project_integrity(reconstructed)
