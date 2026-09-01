"""Hardened unit tests for JSON serialization, unknown fields, and invalid JSON/versions."""

import pytest
from pydantic import ValidationError
from video_editor.ir.enums import AssetType, TrackType
from video_editor.ir.models import Asset, Clip, Track, VideoProject


def test_malformed_json_rejection():
    invalid_json = '{"name": "Broken Project", "settings": "not-an-object"}'
    with pytest.raises(ValidationError):
        VideoProject.model_validate_json(invalid_json)


def test_unknown_fields_ignored_safely():
    json_with_unknown_fields = """
    {
        "name": "Forward Compatible Project",
        "version": "1.0.0",
        "future_unsupported_key": "some_value",
        "settings": {
            "width": 1080,
            "height": 1920,
            "unknown_setting": 123
        }
    }
    """
    project = VideoProject.model_validate_json(json_with_unknown_fields)
    assert project.name == "Forward Compatible Project"
    assert project.settings.width == 1080


def test_microsecond_exactness_in_serialization():
    project = VideoProject()
    asset = Asset(type=AssetType.VIDEO, path="/media.mp4", duration_us=12_345_678)
    project.assets[asset.id] = asset

    json_str = project.model_dump_json()
    reconstructed = VideoProject.model_validate_json(json_str)

    assert reconstructed.assets[asset.id].duration_us == 12_345_678
