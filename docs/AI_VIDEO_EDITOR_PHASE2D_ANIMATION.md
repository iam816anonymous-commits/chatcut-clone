# Phase 2D Temporal Transform & Motion Animation Specification

This document specifies the IR model representations and compilation rules for continuous spatial and temporal motion animations across video tracks.

---

## 1. Supported Spatial Motion Animations

1. **Ken Burns Effect (Pan & Zoom):**
   * Driven by keyframes on `SCALE_X`, `SCALE_Y`, `POSITION_X`, and `POSITION_Y`.
   * Compiled via time-varying `scale` and `overlay` expression evaluations or `zoompan` filter nodes.

2. **Fade In / Fade Out (Opacity Motion):**
   * Driven by keyframes on `OPACITY` (from `0.0` to `1.0` or `1.0` to `0.0`).
   * Compiled via piecewise `colorchannelmixer` / `format` / `drawtext` evaluation strings.

3. **Audio Fade In / Fade Out (Volume Motion):**
   * Driven by keyframes on `VOLUME` or compiled via `afade` filter nodes.

---

## 2. Determinism & Bounds Validation

* All animation time bounds are validated against clip microsecond boundaries (`0 <= time_us <= clip.source_duration_us`).
* Keyframes are sorted deterministically by `time_us` prior to evaluation expression generation.
* Zero-duration or out-of-order keyframes are caught by validation gates before compilation.
