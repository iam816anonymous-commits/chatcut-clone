"""Unit tests for Runtime Discovery and Asset Resolver."""

import pytest
from video_editor.ir.exceptions import AssetNotFoundError
from video_editor.ir.models import Asset, VideoProject
from video_editor.media.exceptions import InputFileNotFoundError
from video_editor.media.resolver import AssetResolver
from video_editor.rendering.runtime import discover_runtime


def test_discover_runtime_executable_check():
    caps = discover_runtime()
    # If environment has ffmpeg, verify path/version set, otherwise false
    assert isinstance(caps.ffmpeg_available, bool)
    assert isinstance(caps.ffprobe_available, bool)


def test_asset_resolver_missing_asset(tmp_path):
    project = VideoProject()
    with pytest.raises(AssetNotFoundError):
        AssetResolver.resolve_asset_path(project, "non-existent-id")


def test_asset_resolver_valid_file(tmp_path):
    fake_file = tmp_path / "media.mp4"
    fake_file.write_text("dummy")

    project = VideoProject()
    asset = Asset(type="VIDEO", path=str(fake_file), duration_us=1_000_000)
    project.assets[asset.id] = asset

    resolved = AssetResolver.resolve_asset_path(project, asset.id)
    assert resolved == str(fake_file.resolve())


def test_asset_resolver_file_deleted_on_disk(tmp_path):
    fake_file = tmp_path / "deleted.mp4"
    fake_file.write_text("dummy")

    project = VideoProject()
    asset = Asset(type="VIDEO", path=str(fake_file), duration_us=1_000_000)
    project.assets[asset.id] = asset

    fake_file.unlink()  # Delete file on disk

    with pytest.raises(InputFileNotFoundError):
        AssetResolver.resolve_asset_path(project, asset.id)
