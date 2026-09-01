"""Unit tests for OutputValidator and ArtifactManager."""

import os
import tempfile
import unittest
from video_editor.runtime.artifacts import ArtifactManager
from video_editor.runtime.errors import OutputValidationError
from video_editor.runtime.validator import OutputValidator


class TestOutputValidatorAndArtifactManager(unittest.TestCase):
    def test_validator_missing_file_raises(self):
        with self.assertRaises(OutputValidationError):
            OutputValidator.validate_rendered_output("/tmp/non_existent_video.mp4")

    def test_validator_empty_file_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
            tf_path = tf.name

        try:
            with self.assertRaises(OutputValidationError):
                OutputValidator.validate_rendered_output(tf_path)
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_artifact_sha256(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b"hello world video content")
            tf_path = tf.name

        try:
            checksum = ArtifactManager.calculate_sha256(tf_path)
            self.assertEqual(len(checksum), 64)
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)


if __name__ == "__main__":
    unittest.main()
