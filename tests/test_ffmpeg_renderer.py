"""Unit tests for FFmpegRenderer primitives and Renderer Boundary."""

import pytest
from unittest.mock import MagicMock
from video_editor.ir.models import VideoProject
from video_editor.media.exceptions import InputFileNotFoundError
from video_editor.rendering.exceptions import InputOverwriteError, InvalidDimensionsError
from video_editor.rendering.ffmpeg import FFmpegRenderer, validate_paths
from video_editor.rendering.executor import ProcessResult


def test_validate_paths_input_not_found():
    with pytest.raises(InputFileNotFoundError):
        validate_paths("/non_existent_input.mp4", "/output.mp4")


def test_validate_paths_overwrite_prevention(tmp_path):
    input_file = tmp_path / "video.mp4"
    input_file.write_text("data")

    with pytest.raises(InputOverwriteError):
        validate_paths(str(input_file), str(input_file))


def test_ffmpeg_renderer_invalid_dimensions(tmp_path):
    input_file = tmp_path / "in.mp4"
    input_file.write_text("data")
    output_file = tmp_path / "out.mp4"

    renderer = FFmpegRenderer()
    with pytest.raises(InvalidDimensionsError):
        renderer.render_scale(str(input_file), str(output_file), width=0, height=1080)


def test_ffmpeg_renderer_trim_primitives_mock(tmp_path):
    input_file = tmp_path / "in.mp4"
    input_file.write_text("data")
    output_file = tmp_path / "out.mp4"

    renderer = FFmpegRenderer()
    mock_executor = MagicMock()

    # Simulate successful render creating output file
    def mock_exec(cmd):
        output_file.write_text("rendered output data")
        return ProcessResult(
            success=True,
            exit_code=0,
            stdout="",
            stderr="",
            duration_ms=15.0,
            command=cmd.to_cmd_list() if hasattr(cmd, "to_cmd_list") else cmd
        )

    mock_executor.execute.side_effect = mock_exec
    renderer.executor = mock_executor

    res = renderer.render_trim(str(input_file), str(output_file), start_us=1_000_000, duration_us=2_000_000)
    assert res.success is True
    assert output_file.exists()
    assert output_file.read_text() == "rendered output data"


def test_renderer_boundary_ir_unmutated():
    project = VideoProject(name="Pure IR Project")
    project_copy = project.model_copy(deep=True)

    renderer = FFmpegRenderer()
    with pytest.raises(NotImplementedError):
        renderer.render(project, "/out.mp4")

    # Verify project state remained 100% untouched
    assert project.name == project_copy.name
    assert project.tracks == project_copy.tracks
