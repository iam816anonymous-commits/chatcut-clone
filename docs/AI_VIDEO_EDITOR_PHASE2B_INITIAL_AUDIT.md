# AI Video Editor Phase 2B — Initial Repository Audit

## Executive Summary
This document provides a comprehensive audit of the repository following Phase 2A, analyzing existing package structures, model relationships, renderer boundaries, compiler integration points, existing limitations, risks, and compatibility constraints prior to Phase 2B implementation.

---

## 1. Existing Package Hierarchy & Capabilities

The `video_editor` Python package currently consists of three subsystems (`ir`, `engine`, `media`, `rendering`):

```text
video_editor/
├── __init__.py
├── ir/                     # Universal Video Editing IR Core (v1.0.0)
│   ├── time.py           # TimelineTime microsecond class (1s = 1,000,000us)
│   ├── enums.py          # AssetType, TrackType, OperationType, ActorType, AspectRatio
│   ├── models.py         # VideoProject, ProjectSettings, Asset, Track, Clip, Transform, AudioConfig
│   ├── exceptions.py     # Domain exceptions (AssetNotFoundError, TrackLockedError, etc.)
│   ├── operations.py     # Atomic operation payloads (AddTrackOperation, SplitClipOperation, etc.)
│   └── validation.py     # validate_project_integrity, clip time bounds, track overlap checks
├── engine/                 # Transactional State Engine
│   ├── history.py        # HistoryManager (linear past_states, current_state, future_states)
│   └── state_manager.py  # StateManager (copy-on-write apply_operation, undo, redo)
├── media/                  # Media Inspection & Resolution
│   ├── models.py         # MediaMetadata, VideoStreamMetadata, AudioStreamMetadata, ContainerMetadata
│   ├── inspector.py        # MediaInspector (ffprobe JSON inspection with rational FPS parsing)
│   ├── resolver.py         # AssetResolver (Resolves asset_id to verified local disk path)
│   └── exceptions.py     # MediaInspectionError, InputFileNotFoundError, InvalidMediaError
└── rendering/              # FFmpeg Binary Execution Subsystem
    ├── base.py             # Abstract BaseRenderer interface
    ├── runtime.py          # discover_runtime (detects ffmpeg/ffprobe executables)
    ├── command.py          # FFmpegCommand argument array model
    ├── executor.py         # ProcessExecutor & ProcessResult (subprocess execution without shell=True)
    ├── ffmpeg.py           # FFmpegRenderer primitives (transcode, trim, scale)
    └── exceptions.py       # RenderExecutionError, InputOverwriteError, OutputValidationError
```

Existing test suite in `tests/`: 51 passing unit tests across 10 modules.

---

## 2. Model & Boundary Relationships

```text
               ┌───────────────────────────────┐
               │         VideoProject          │
               │        (Universal IR)         │
               └───────────────┬───────────────┘
                               │ Read-Only Input
                               ▼
               ┌───────────────────────────────┐
               │       TimelineCompiler        │  ◄── (Phase 2B Integration Point)
               │ (Compiles IR to RenderPlan)   │
               └───────────────┬───────────────┘
                               │ Produces RenderPlan
                               ▼
               ┌───────────────────────────────┐
               │          RenderPlan           │  ◄── Pure, serializable, inspectable
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │        RenderPlanner          │
               │ (Builds FFmpegFilterGraph &   │
               │  FFmpegCommand array)         │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │        FFmpegRenderer         │
               │  (Executes via ProcessExecutor)│
               └───────────────────────────────┘
```

---

## 3. Key Invariants & Compatibility Constraints

1. **Microsecond Precision**: All timeline offsets, source ranges, gap spans, and segment durations must strictly use integer microseconds (`int`).
2. **IR Immutability**: Neither `TimelineCompiler` nor `FFmpegRenderer` may mutate `VideoProject`, `StateManager`, or `HistoryManager`.
3. **No `shell=True`**: FFmpeg commands must be built as argument lists (`List[str]`).
4. **Deterministic Labels & Graphs**: Label allocation ($v0, v1, a0, a1$) and filtergraph output strings must be 100% deterministic for identical `RenderPlan` inputs.

---

## 4. Risks & Mitigations

* **Risk 1: Filtergraph Concatenation Mismatch**: Streams with mismatched resolutions, frame rates, or audio sample rates cause FFmpeg `concat` filter failures.
  * *Mitigation*: The compiler inserts explicit `scale` and `fps` normalization nodes for video segments and `aformat=sample_rates=48000:channel_layouts=stereo` for audio segments prior to `concat`.
* **Risk 2: Timeline Gap Corruption**: Unhandled timeline gaps cause audio/video drift or silent clip collapse.
  * *Mitigation*: The compiler explicitly models `RenderGap` instances, emitting `color=c=black:s=WxH` for video gaps and `anullsrc=r=48000:cl=stereo` for audio gaps.
* **Risk 3: Unrenderable Track Types**: Text/subtitle overlays or unsupported track compositing can produce cryptic FFmpeg crashes.
  * *Mitigation*: `CompilerValidator` inspects the project upfront, raising structured `UnsupportedTrackTypeError` or `UnsupportedTimelineStructureError` with clear error details.