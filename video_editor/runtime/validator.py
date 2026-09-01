"""Output Validator using ffprobe to verify rendered video files."""

import os
from typing import Any, Dict
from video_editor.media.inspector import MediaInspector
from video_editor.runtime.errors import OutputValidationError


class OutputValidator:
    """Validates rendered output video files post-execution using ffprobe inspection."""

    @classmethod
    def validate_rendered_output(
        cls,
        output_path: str,
        expected_duration_us: int = 0,
        tolerance_sec: float = 1.0,
    ) -> Dict[str, Any]:
        """Validate rendered file existence, non-zero file size, ffprobe readability, streams, and duration.

        Returns:
            Dict[str, Any]: Inspected metadata dictionary.

        Raises:
            OutputValidationError: If any output verification check fails.
        """
        if not os.path.exists(output_path):
            raise OutputValidationError(f"Rendered output file does not exist: {output_path}")

        file_size = os.path.getsize(output_path)
        if file_size <= 0:
            raise OutputValidationError(f"Rendered output file is empty (0 bytes): {output_path}")

        try:
            inspector = MediaInspector()
            metadata_model = inspector.inspect(output_path)
        except Exception as e:
            raise OutputValidationError(
                f"ffprobe validation failed for rendered output file {output_path}: {e}"
            ) from e

        has_video = len(metadata_model.video_streams) > 0
        has_audio = len(metadata_model.audio_streams) > 0

        if not has_video and not has_audio:
            raise OutputValidationError(
                f"Rendered output file contains neither video nor audio streams: {output_path}"
            )

        actual_duration_us = metadata_model.duration_us or 0
        if expected_duration_us > 0:
            diff_us = abs(actual_duration_us - expected_duration_us)
            tolerance_us = int(tolerance_sec * 1_000_000)
            if diff_us > tolerance_us:
                raise OutputValidationError(
                    f"Rendered output duration {actual_duration_us}us deviates from expected "
                    f"{expected_duration_us}us by more than {tolerance_sec}s tolerance"
                )

        return {
            "has_video": has_video,
            "has_audio": has_audio,
            "duration_us": actual_duration_us,
            "video_stream_count": len(metadata_model.video_streams),
            "audio_stream_count": len(metadata_model.audio_streams),
            "file_path": output_path,
        }
