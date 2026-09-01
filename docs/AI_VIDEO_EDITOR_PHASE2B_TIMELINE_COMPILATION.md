# AI Video Editor — Timeline Compilation Specification

## Executive Summary
This document specifies the timeline compilation mechanics implemented in `video_editor.compiler.compiler.TimelineCompiler`.

---

## 1. Source Time vs. Timeline Time Translation
The compiler converts clip metadata into `RenderSegment` entries while preserving the distinction between source time and timeline time:

```text
Input Clip:
  asset_id: "asset_01"
  source_start_us: 10,000,000  (10.0s in raw media file)
  source_duration_us: 5,000,000 (5.0s segment)
  timeline_start_us: 20,000,000 (20.0s on timeline)
  timeline_duration_us: 5,000,000

Compiled RenderSegment:
  input_index: 0
  source_start_us: 10,000,000
  source_duration_us: 5,000,000
  timeline_start_us: 20,000,000
  timeline_duration_us: 5,000,000
```

---

## 2. Timeline Gap Insertion Policy
When `clip.timeline_start_us > cursor_time_us`, a `RenderGap` is inserted into the track item list:

$$\text{gap\_duration\_us} = \text{clip.timeline\_start\_us} - \text{cursor\_time\_us}$$

```text
Track Timeline:
[0.0s ──── 5.0s Clip A] ─── (GAP 5.0s ──── 10.0s) ─── [10.0s ──── 15.0s Clip B]
```

---

## 3. Pre-Compilation Validation Gate
Before compiling, `validate_project_renderability` checks:
1. Standard IR structural integrity (`validate_project_integrity`).
2. Rejection of unsupported track types (`TEXT`, `SUBTITLE`).
3. Rejection of multi-layer video tracks (at most 1 active `VIDEO` track supported in Phase 2B).
4. Rejection of unrenderable empty projects.