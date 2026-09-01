"""Unit tests verifying boundary decoupling between IR and Rendering subsystems."""

from video_editor.ir.models import VideoProject
from video_editor.rendering.base import BaseRenderer


def test_ir_contains_no_rendering_imports():
    import video_editor.ir.models as ir_models
    import video_editor.ir.validation as ir_val

    # Assert ir modules do not import rendering or ffmpeg
    for module in [ir_models, ir_val]:
        for attr in dir(module):
            val = getattr(module, attr)
            if hasattr(val, "__module__") and val.__module__:
                assert "rendering" not in val.__module__
                assert "ffmpeg" not in val.__module__


def test_base_renderer_subclassing():
    class DummyRenderer(BaseRenderer):
        def render(self, project, output_path, progress_callback=None):
            return None

    renderer = DummyRenderer()
    assert isinstance(renderer, BaseRenderer)
