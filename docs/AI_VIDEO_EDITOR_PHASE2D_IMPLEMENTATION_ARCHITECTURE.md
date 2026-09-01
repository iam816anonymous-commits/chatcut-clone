# Phase 2D Implementation Architecture

## 1. Architectural Pipeline

Phase 2D preserves the decoupled, vendor-independent compilation pipeline:

```
Universal Video Editing IR
          ↓
Validation Engine (`validate_project_integrity` + `validate_project_renderability`)
          ↓
Timeline Compiler (`TimelineCompiler` -> `RenderPlan`)
          ↓
Render Planner (`RenderPlanner` -> `FilterGraph` -> `FFmpegCommand`)
          ↓
Process Executor (`ProcessExecutor`)
```

---

## 2. Subsystem Mapping & Responsibilities

### 2.1 Microsecond Temporal Semantics (`video_editor/ir/time.py`)
* Stores all time bounds as 64-bit non-negative integers (`int`) representing microseconds ($1\text{s} = 1,000,000\mu\text{s}$).
* Converts microsecond values to floating-point seconds exclusively at the FFmpeg filter string formatting boundary.

### 2.2 Keyframe Animation & Interpolation (`video_editor/ir/animation.py`, `video_editor/compiler/interpolation.py`, `video_editor/compiler/animation.py`)
* Computes deterministic scalar values across clip timeline offsets using `HOLD` or `LINEAR` interpolation modes.
* Generates time-varying piecewise `if()` mathematical evaluation strings for FFmpeg filter parameters.

### 2.3 Speed Control (`video_editor/compiler/speed.py`)
* Compiles video speed factors into FFmpeg `setpts` filters ($1 / S \cdot \text{PTS}$).
* Compiles audio speed factors into chained `atempo` filters for multipliers outside $[0.5, 2.0]$.

### 2.4 Clip Transitions (`video_editor/compiler/transitions.py`)
* Compiles video transitions into `xfade` filter nodes with explicit start offset seconds.
* Compiles audio crossfades into `acrossfade` filter nodes with triangular curve weights (`c1=tri:c2=tri`).

### 2.5 Visual Effects (`video_editor/compiler/effects.py`)
* Compiles reusable effects (`BLUR`, `BRIGHTNESS`, `CONTRAST`, `GRAYSCALE`, `VIGNETTE`) into sequential FFmpeg filter graph nodes.
* Supports optional temporal interval filtering using `enable='between(t, start, end)'`.

---

## 3. Deterministic Filtergraph Rendering Order

For each clip segment, filters MUST be appended in the following strict order:

```
1. Source Trim (`trim=start=S1:end=S2`)
2. Presentation Timestamp Reset & Speed Adjustment (`setpts=PTS-STARTPTS+FACTOR*PTS`)
3. Visual Effects Chain (`boxblur`, `eq`, `hue`, `vignette`)
4. Spatial Transform & Scaling (`scale=W:H`)
5. Frame Rate Normalization (`fps=R`)
6. Z-Ordered Overlay Compositing (`overlay=x=X:y=Y:enable='between(t,T1,T2)'`)
7. Video / Audio Transitions (`xfade` / `acrossfade`)
8. Text & Subtitle Overlays (`drawtext`)
```
