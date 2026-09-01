# Phase 2D Initial Repository Audit

## 1. Overview & Objectives

This document performs a comprehensive technical audit of the existing `video_editor` codebase prior to implementing Phase 2D capabilities (Keyframe Animations, Speed Multipliers, Transitions, Temporal Operations, and Visual Effect Chains).

---

## 2. Existing Architecture Audit

### 2.1 Universal Video Editing IR (`video_editor/ir/`)
* **`models.py`:** Standard Pydantic v2 domain schemas (`VideoProject`, `Track`, `Clip`, `Asset`, `Transform`, `AudioConfig`, `TextStyle`). Microsecond integer precision is enforced across `timeline_start_us`, `timeline_duration_us`, `source_start_us`, and `source_duration_us`.
* **`animation.py`:** Keyframe models (`Keyframe`, `AnimationTrack`, `InterpolationMode`, `AnimatedProperty`).
* **`transitions.py`:** Transition spec models (`Transition`, `TransitionType`, `TransitionCategory`).
* **`effects.py`:** Effect spec models (`Effect`, `EffectType`).
* **`time.py`:** Microsecond timing primitives (`TimelineTime`).
* **`validation.py`:** Structural integrity checking (`validate_project_integrity`).

### 2.2 State Engine (`video_editor/engine/`)
* **`state_manager.py`:** Copy-on-write transactional mutation manager (`apply_operation`).
* **`history.py`:** Linear undo/redo stack manager (`HistoryManager`).

### 2.3 Media Inspection & Runtime (`video_editor/media/` & `video_editor/rendering/`)
* **`inspector.py`:** `ffprobe` JSON metadata extraction (`MediaInspector`).
* **`resolver.py`:** Asset file path verification (`AssetResolver`).
* **`executor.py`:** Safe subprocess execution (`ProcessExecutor`).
* **`command.py`:** Structured FFmpeg command model (`FFmpegCommand`).

### 2.4 Compiler Pipeline (`video_editor/compiler/`)
* **`compiler.py`:** `TimelineCompiler` translates `VideoProject` IR into a pure, inspectable `RenderPlan`.
* **`planner.py`:** `RenderPlanner` translates `RenderPlan` into an executable `FFmpegCommand`.
* **`filter_graph.py`:** Structured `FilterGraph` and `LabelAllocator`.
* **`compositor.py`:** `VideoCompositor` compiles Z-ordered visual overlay chains using `overlay` filters with timeline `enable` intervals.
* **`audio_compiler.py`:** `AudioCompiler` compiles multi-track audio with `adelay` alignment, `volume` gain, and `amix` mixing.
* **`text_compiler.py`:** `TextCompiler` compiles `drawtext` overlay nodes with string character escaping (`escape_drawtext_str`).
* **`canvas.py`:** `CanvasNormalizer` generates solid color background canvas and silent audio streams.
* **`validation.py`:** Pre-compilation renderability validation gate (`validate_project_renderability`).
* **`speed.py`:** Video `setpts` and chained audio `atempo` filter compilers.
* **`transitions.py`:** Video `xfade` and audio `acrossfade` compilers.
* **`effects.py`:** Reusable visual effect compiler (`BLUR`, `BRIGHTNESS`, `CONTRAST`, `GRAYSCALE`, `VIGNETTE`).
* **`interpolation.py`:** Deterministic keyframe interpolation engine.
* **`animation.py`:** Piecewise linear evaluation expression compiler for animated properties.

---

## 3. Extension Points & Compatibility Guarantees

1. **`video_editor/ir/time.py`:** Extend temporal microsecond conversion and validation functions.
2. **`video_editor/ir/models.py`:** Unify `Effect` and `Transition` domain models and ensure `Clip` exposes `animation_tracks`, `transition_in`, `transition_out`, and `effects`.
3. **`video_editor/compiler/rendering_order.py`:** Codify the explicit deterministic filter sequence rules in a dedicated compiler specification module.
4. **`video_editor/compiler/validation.py`:** Extend validation gates for transition duration overlaps, speed multiplier bounds, keyframe sequence ordering, and effect parameters.

---

## 4. Risks & Mitigations

* **Risk:** Extreme speed multipliers causing audio buffer overflow or frame loss in FFmpeg.
  * **Mitigation:** Validate speed range bounds ($0.1 \le \text{speed} \le 10.0$) in pre-compilation validation gates.
* **Risk:** Duplicate stream tag labels in complex filter graphs.
  * **Mitigation:** Use `LabelAllocator` consistently across all compiler subsystems.
* **Risk:** Inconsistent time representations.
  * **Mitigation:** Microsecond integer arithmetic (`int`) remains the single source of temporal truth.
