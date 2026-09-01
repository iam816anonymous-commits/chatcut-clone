"""RenderPlanner: Translates pure RenderPlan into executable FFmpegCommand."""

from video_editor.compiler.audio_compiler import AudioCompiler
from video_editor.compiler.compositor import VideoCompositor
from video_editor.compiler.filter_graph import FilterGraph, LabelAllocator
from video_editor.compiler.models import RenderPlan
from video_editor.compiler.text_compiler import TextCompiler
from video_editor.rendering.command import FFmpegCommand


class RenderPlanner:
    """Translates a compiled RenderPlan into an executable FFmpegCommand with a filter_complex graph."""

    def __init__(self) -> None:
        self.compositor = VideoCompositor()
        self.audio_compiler = AudioCompiler()
        self.text_compiler = TextCompiler()

    def plan_to_command(self, plan: RenderPlan, output_path: str, ffmpeg_path: str = "ffmpeg") -> FFmpegCommand:
        """Construct FFmpegCommand argument array for a RenderPlan."""
        # 1. Base input arguments
        arguments = ["-y"]
        for inp in plan.inputs:
            arguments.extend(["-i", inp.file_path])

        # 2. Construct FilterGraph
        graph = FilterGraph()
        allocator = LabelAllocator()

        # 3. Video Composition
        visual_composite_label = self.compositor.compile_visual_composition(plan, graph, allocator)

        # 4. Text & Subtitle Overlays
        final_video_label = self.text_compiler.compile_text_overlays(
            plan, graph, allocator, visual_composite_label
        )

        # 5. Audio Mixing
        final_audio_label = self.audio_compiler.compile_audio_mix(plan, graph, allocator)

        # 6. Build filter_complex argument string
        filter_complex_str = graph.to_filter_complex_string()
        arguments.extend(["-filter_complex", filter_complex_str, "-map", f"[{final_video_label}]"])

        if final_audio_label:
            arguments.extend(["-map", f"[{final_audio_label}]"])

        # Codec & Output formatting
        arguments.extend([
            "-c:v", plan.output_settings.video_codec,
            "-pix_fmt", "yuv420p",
        ])
        if final_audio_label:
            arguments.extend(["-c:a", plan.output_settings.audio_codec])

        arguments.append(output_path)

        return FFmpegCommand(executable=ffmpeg_path, arguments=arguments)
