# AI Video Editor Phase 2A — Proposed Subsystem Architecture

## Executive Summary
This document specifies the software architecture, module layout, data flow pipelines, and component responsibilities for Phase 2A (Media Inspection & FFmpeg Render Foundation).

---

## 1. Package Structure Expansion

Phase 2A expands the `video_editor` Python package with two new sub-packages (`media` and `rendering`):

```text
video_editor/
├── __init__.py
├── ir/                     # (Phase 1 & 1.1 IR Models, Validation, Operations)
├── engine/                 # (Phase 1 & 1.1 Transactional State & History Engines)
├── media/                  # (Phase 2A Media Inspection Subsystem)
│   ├── __init__.py
│   ├── models.py           # Typed metadata schemas (MediaMetadata, VideoStream, AudioStream, Container)
│   ├── inspector.py        # MediaInspector (Executes FFprobe JSON analysis)
│   ├── resolver.py         # AssetResolver (Resolves IR asset_id to verified disk path)
│   └── exceptions.py       # Domain exceptions (MediaInspectionError, InputFileNotFoundError, etc.)
└── rendering/              # (Phase 2A FFmpeg Process & Execution Subsystem)
    ├── __init__.py
    ├── base.py             # Abstract BaseRenderer interface
    ├── runtime.py          # RuntimeCapabilities & executable discovery (ffmpeg/ffprobe)
    ├── command.py          # FFmpegCommand argument array model
    ├── executor.py         # ProcessExecutor & ProcessResult (subprocess execution without shell=True)
    ├── ffmpeg.py           # FFmpegRenderer (Primitives: render_transcode, render_trim, render_scale)
    └── exceptions.py       # Rendering exceptions (RenderExecutionError, RenderTimeoutError, OutputValidationError)
```

---

## 2. Component Collaboration Architecture

```text
               ┌───────────────────────────────┐
               │         VideoProject          │
               │        (Universal IR)         │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │         AssetResolver         │
               │ (Resolves asset_id -> path)   │
               └───────────────┬───────────────┘
                               │ Verified Path
                               ▼
               ┌───────────────────────────────┐
               │        MediaInspector         │
               │ (Invokes FFprobe JSON Engine) │
               └───────────────┬───────────────┘
                               │ Parsed MediaMetadata
                               ▼
               ┌───────────────────────────────┐
               │        FFmpegRenderer         │
               │ (Constructs FFmpegCommand)    │
               └───────────────┬───────────────┘
                               │ Argument Array [List[str]]
                               ▼
               ┌───────────────────────────────┐
               │        ProcessExecutor        │
               │ (Subprocess run without shell)│
               └───────────────┬───────────────┘
                               │ ProcessResult
                               ▼
               ┌───────────────────────────────┐
               │     Rendered Output Media     │
               └───────────────────────────────┘
```

---

## 3. Key Architectural Boundaries
1. **IR Neutrality**: Models in `video_editor.media` and `video_editor.rendering` import from `video_editor.ir`, but models in `video_editor.ir` NEVER import from `media` or `rendering`.
2. **Process Execution Isolation**: All external process execution is encapsulated inside `ProcessExecutor`. No module invokes `subprocess.run` directly outside `executor.py` or `runtime.py`.
3. **Copy/Isolation Safety**: All metadata objects returned from `MediaInspector` and render results returned from `FFmpegRenderer` are immutable/strongly typed Pydantic models.