"""Artifact Manager for atomic publication and SHA-256 checksum calculation."""

import hashlib
import os
from typing import Dict, Any
from video_editor.runtime.errors import ArtifactPublishingError
from video_editor.runtime.models import RenderArtifact


class ArtifactManager:
    """Handles atomic publishing from partial output paths to final targets and calculates checksums."""

    @classmethod
    def calculate_sha256(cls, file_path: str, chunk_size: int = 65536) -> str:
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            raise ArtifactPublishingError(f"Failed to calculate SHA-256 for {file_path}: {e}") from e

    @classmethod
    def publish_artifact(
        cls,
        execution_id: str,
        partial_path: str,
        final_path: str,
        metadata: Dict[str, Any],
    ) -> RenderArtifact:
        """Atomically rename partial file to final target path and construct RenderArtifact.

        Args:
            execution_id: Unique render execution ID.
            partial_path: Source temporary partial output path (e.g., output.mp4.partial).
            final_path: Final target output path (e.g., output.mp4).
            metadata: Verified ffprobe metadata dictionary from OutputValidator.

        Returns:
            RenderArtifact: Construct published artifact model.
        """
        if not os.path.exists(partial_path):
            raise ArtifactPublishingError(f"Partial output file does not exist for publishing: {partial_path}")

        try:
            # Ensure target parent directory exists
            os.makedirs(os.path.dirname(os.path.abspath(final_path)), exist_ok=True)

            # Atomic publish via os.replace
            os.replace(partial_path, final_path)
        except Exception as e:
            raise ArtifactPublishingError(
                f"Failed atomic publish from {partial_path} to {final_path}: {e}"
            ) from e

        file_size = os.path.getsize(final_path)
        checksum = cls.calculate_sha256(final_path)

        return RenderArtifact(
            execution_id=execution_id,
            path=final_path,
            file_size_bytes=file_size,
            duration_us=metadata.get("duration_us", 0),
            video_streams=metadata.get("video_stream_count", 1 if metadata.get("has_video") else 0),
            audio_streams=metadata.get("audio_stream_count", 1 if metadata.get("has_audio") else 0),
            sha256_checksum=checksum,
        )
