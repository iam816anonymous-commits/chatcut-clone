# AI Video Editor — Renderer Subsystem Architecture

## Executive Summary
This document outlines the architecture, base interface abstractions, process execution pipeline, and primitive rendering capabilities implemented in Phase 2A.

---

## 1. Renderer Subsystem Hierarchy

```text
video_editor/rendering/
├── __init__.py
├── base.py             # Abstract BaseRenderer interface
├── runtime.py          # RuntimeCapabilities discovery (ffmpeg & ffprobe)
├── command.py          # FFmpegCommand argument array model
├── executor.py         # ProcessExecutor & ProcessResult
├── ffmpeg.py           # FFmpegRenderer primitives (transcode, trim, scale)
└── exceptions.py       # Rendering exceptions (RenderExecutionError, InputOverwriteError, etc.)
```

---

## 2. Base Renderer Interface

All rendering engines inherit from `BaseRenderer`:

```python
class BaseRenderer(ABC):
    @abstractmethod
    def render(
        self,
        project: VideoProject,
        output_path: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> ProcessResult:
        pass
```

---

## 3. Phase 2A Primitive Capabilities
1. **Transcode (`render_transcode`)**: Copies or re-encodes source media files to target container formats.
2. **Trim (`render_trim`)**: Performs microsecond-accurate slicing using `-ss` and `-t` flags.
3. **Scale (`render_scale`)**: Performs spatial scaling using the `-vf scale=w:h` filter.