"""Unit tests for ProcessExecutor without shell=True."""

import pytest
from unittest.mock import patch, MagicMock
from video_editor.rendering.command import FFmpegCommand
from video_editor.rendering.exceptions import ExecutableNotFoundError, RenderTimeoutError
from video_editor.rendering.executor import ProcessExecutor


def test_executor_successful_run():
    executor = ProcessExecutor()
    # Execute standard python version check as safe test process
    res = executor.execute(["python3", "--version"])
    assert res.success is True
    assert res.exit_code == 0
    assert "Python" in res.stdout
    assert res.duration_ms > 0


def test_executor_executable_not_found():
    executor = ProcessExecutor()
    with pytest.raises(ExecutableNotFoundError):
        executor.execute(["non_existent_binary_xyz_12345", "--arg"])


@patch("subprocess.run")
def test_executor_timeout_expired(mock_run):
    import subprocess
    mock_run.side_effect = subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=1.0)

    executor = ProcessExecutor()
    with pytest.raises(RenderTimeoutError):
        executor.execute(["ffmpeg", "-i", "in.mp4"], timeout=1.0)
