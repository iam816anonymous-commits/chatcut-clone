# AI Video Editor — IR to FFmpeg Renderer Boundary Specification

## Executive Summary
This document specifies the strict architectural decoupling between the **Universal Video Editing Intermediate Representation (IR)** and the **FFmpeg Rendering Engine**.

---

## 1. Core Decoupling Rule
The Universal Video Editing IR is the canonical source of truth for video projects. It represents editing intent and spatial/temporal composition as pure metadata.

**Strict Decoupling Invariants**:
1. The IR (`video_editor.ir`) MUST NEVER import FFmpeg modules, command builders, or filter string generators.
2. IR models (`VideoProject`, `Clip`, `Track`, `Transform`, `AudioConfig`) contain zero FFmpeg flags (e.g., no `-vf scale=1080:1920`, no `-c:v libx264`).
3. Renderers (`FFmpegRenderer`) are strictly **read-only consumers** of the IR.
4. Renderers translation functions output executable `FFmpegCommand` argument arrays without mutating the `VideoProject` or `StateManager`.

---

## 2. Translation Pipeline

```text
               ┌─────────────────────────────┐
               │    Universal Video IR       │
               │   (VideoProject Object)     │
               └──────────────┬──────────────┘
                              │ Read-Only Access
                              ▼
               ┌─────────────────────────────┐
               │       AssetResolver         │
               │ (Resolves asset_id -> path) │
               └──────────────┬──────────────┘
                              │ Verified Disk Paths
                              ▼
               ┌─────────────────────────────┐
               │      FFmpeg Renderer        │
               │   (Converts IR intent to    │
               │    FFmpegCommand array)     │
               └──────────────┬──────────────┘
                              │ Argument List [List[str]]
                              ▼
               ┌─────────────────────────────┐
               │      ProcessExecutor        │
               │  (Executes argument array)  │
               └─────────────────────────────┘
```

---

## 3. Translation Mapping Specification

| Universal IR Field | Semantic Meaning | FFmpeg Renderer Mapping |
| :--- | :--- | :--- |
| `clip.source_start_us` | In-point offset inside raw media asset | `-ss <seconds.microseconds>` |
| `clip.source_duration_us` | Duration of source segment | `-t <seconds.microseconds>` |
| `clip.transform.scale_x/y` | Spatial scaling factor | `-vf scale=w:h` filter |
| `clip.audio.volume` | Audio volume multiplier ($0.0 - 2.0$) | `-af volume=X` filter |
| `clip.speed` | Playback speed multiplier ($0.5x - 2.0x$) | `-vf setpts=1/PTS` & `-af atempo=X` |

By preserving this boundary, alternative renderers (e.g., Remotion or WebCodecs) can consume the same Universal IR without modifying project state logic.