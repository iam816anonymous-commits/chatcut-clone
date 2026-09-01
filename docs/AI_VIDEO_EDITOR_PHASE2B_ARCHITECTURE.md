# AI Video Editor Phase 2B — Proposed Subsystem Architecture

## Executive Summary
This document specifies the software architecture, package layout, data flow pipelines, and component responsibilities for Phase 2B (Timeline Compilation & Real Project Rendering).

---

## 1. Compiler Subsystem Layout

Phase 2B introduces the `video_editor.compiler` sub-package:

```text
video_editor/
├── __init__.py
├── ir/                     # (Phase 1 & 1.1 Universal Video Editing IR Core)
├── engine/                 # (Phase 1 & 1.1 Transactional State & History Engines)
├── media/                  # (Phase 2A Media Inspection & Asset Resolution)
├── rendering/              # (Phase 2A Process Execution & Renderer Interfaces)
└── compiler/               # (Phase 2B Timeline Compiler Subsystem)
    ├── __init__.py
    ├── exceptions.py       # RenderValidationError, UnsupportedTrackTypeError, etc.
    ├── validation.py       # CompilerValidator (Pre-compilation project integrity checks)
    ├── models.py           # Typed Pydantic v2 RenderPlan domain schemas
    ├── filter_graph.py     # FilterNode, FilterGraph, LabelAllocator abstractions
    ├── compiler.py         # TimelineCompiler (Compiles VideoProject IR -> RenderPlan)
    └── planner.py          # RenderPlanner (Translates RenderPlan -> FFmpegCommand)
```

---

## 2. Decoupled Pipeline Architecture

```text
               ┌───────────────────────────────┐
               │         VideoProject          │
               │        (Universal IR)         │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │       CompilerValidator       │
               │   (Validates renderability)   │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │       TimelineCompiler        │
               │  (Resolves time, gaps, inputs)│
               └───────────────┬───────────────┘
                               │ Produces RenderPlan
                               ▼
               ┌───────────────────────────────┐
               │          RenderPlan           │
               │  (Pure, serializable, pure)   │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │         RenderPlanner         │
               │   (Constructs FilterGraph &   │
               │    FFmpegCommand object)      │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │        FFmpegRenderer         │
               │ (Executes via ProcessExecutor)│
               └───────────────────────────────┘
```

---

## 3. Strict Boundary Guarantees

1. **Compiler Purity**: `TimelineCompiler.compile()` is a pure function that returns a `RenderPlan`. It does not invoke subprocesses, execute disk I/O, or mutate `VideoProject` IR.
2. **RenderPlan Independence**: The `RenderPlan` is fully serializable and inspectable before execution. Developers can inspect generated filtergraphs and inputs without running FFmpeg.
3. **Execution Decoupling**: `FFmpegRenderer.render_plan(plan, output_path)` delegates process execution to `ProcessExecutor` without accessing `StateManager`.