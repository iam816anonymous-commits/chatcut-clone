# AI Video Editor Phase 2B — Research & Technical Foundations

## Executive Summary
This document establishes the research and engineering foundations for Phase 2B (Timeline Compilation & Real Project Rendering). It analyzes non-linear editing timeline translation mechanics, FFmpeg filtergraph construction, gap fill strategies, audio normalization, filtergraph label allocation, and concat policies.

---

## 1. Non-Linear Editing Timeline Translation Mechanics

A fundamental responsibility of the `TimelineCompiler` is accurately translating clips from **Source Time** to **Timeline Time** without loss of precision:

```text
Source Asset (video.mp4):
0s ────────────────────────────── 60s
           │ Source Range │
           10s ────────── 15s (source_duration = 5s)
                 │
                 ▼ Placed on Timeline Track
Output Timeline Sequence:
0s ──────────────────────────────────────── 100s
                       │ Timeline Position │
                       20s ────────────── 25s (timeline_duration = 5s)
```

### Translation Mapping
* `trim`: Cut source file between `source_start_us` and `source_end_us` (`-ss 10.0 -t 5.0`).
* `setpts=PTS-STARTPTS`: Reset presentation timestamps so the trimmed segment starts at zero before entering `concat` filter chains.

---

## 2. FFmpeg Filtergraph Construction & Concat Policy

To join multiple clips sequentially on a track, FFmpeg's `filter_complex` engine requires explicit trimming, timestamp resetting, spatial/temporal normalization, and concatenation:

### Video Segment Pipeline
```text
[0:v] trim=start=10.0:end=15.0, setpts=PTS-STARTPTS, scale=1080:1920, fps=30 [v0];
[1:v] trim=start=20.0:end=25.0, setpts=PTS-STARTPTS, scale=1080:1920, fps=30 [v1];
[v0][v1] concat=n=2:v=1:a=0 [outv]
```

### Audio Segment Pipeline
```text
[0:a] atrim=start=10.0:end=15.0, asetpts=PTS-STARTPTS, aformat=sample_rates=48000:channel_layouts=stereo [a0];
[1:a] atrim=start=20.0:end=25.0, asetpts=PTS-STARTPTS, aformat=sample_rates=48000:channel_layouts=stereo [a1];
[a0][a1] concat=n=2:v=0:a=1 [outa]
```

---

## 3. Timeline Gap Modeling & Generation

When gaps exist between clips on a timeline track (e.g. Clip A ends at 5.0s, Clip B starts at 10.0s), the compiler must **never silently collapse gaps**. Unhandled gaps cause video and audio tracks to lose synchronization.

### Phase 2B Gap Strategy
1. **Video Gap Generation**: Emits an FFmpeg `color` filter source:
   `color=c=black:s=1080x1920:r=30:d=5.0 [gap_v0]`
2. **Audio Gap Generation**: Emits an FFmpeg `anullsrc` filter source:
   `anullsrc=r=48000:cl=stereo:d=5.0 [gap_a0]`
3. The generated gap node is inserted into the track's segment array and concatenated seamlessly with surrounding media clips.

---

## 4. Multi-Track & Overlap Scope (Phase 2B Policy)

* **Single Active VIDEO Track**: Phase 2B supports compiling one primary visual track. If multiple video tracks exist, the compiler validates whether they can be composited or raises an explicit `UnsupportedTimelineStructureError`.
* **AUDIO Track Concat**: Sequentially concatenates clips on audio tracks, filling gaps with silence.
* **TEXT / SUBTITLE Tracks**: Marked explicitly unsupported in renderer for Phase 2B, raising `UnsupportedTrackTypeError` to prevent cryptic FFmpeg crashes.

---

## 5. Microsecond Precision & Label Allocator

* **Microseconds to Seconds Conversion**: At the filtergraph generation boundary, microsecond integer values are formatted as exact decimal floating-point strings (`5_000_000 us` $\rightarrow$ `"5.000000"`).
* **Deterministic Label Allocation**: `LabelAllocator` manages stream label counters (`v0`, `v1`, `a0`, `a1`, `outv`, `outa`). Re-compiling the same project always yields identical label strings.