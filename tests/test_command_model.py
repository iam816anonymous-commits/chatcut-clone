"""Unit tests for FFmpegCommand model."""

from video_editor.rendering.command import FFmpegCommand


def test_ffmpeg_command_array_generation():
    cmd = FFmpegCommand(
        executable="ffmpeg",
        arguments=["-y", "-i", "/input file.mp4", "-c:v", "libx264", "/output file.mp4"]
    )

    cmd_list = cmd.to_cmd_list()
    assert cmd_list == ["ffmpeg", "-y", "-i", "/input file.mp4", "-c:v", "libx264", "/output file.mp4"]

    display_str = cmd.to_display_string()
    assert 'ffmpeg -y -i "/input file.mp4" -c:v libx264 "/output file.mp4"' == display_str
