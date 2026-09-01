# AI Video Editor Phase 1 — Research & Engineering Foundations

## Executive Summary
This document establishes the engineering foundations for designing a resilient, deterministic Universal Video Editing Intermediate Representation (IR) and state engine. It analyzes non-linear editing (NLE) data structures, time representation strategies, non-destructive editing paradigms, state mutation patterns, and operation-based editing mechanics.

---

## 1. Non-Linear Editing Data Models

### A. Source Time vs. Timeline Time
A critical requirement in NLE architectures is distinguishing between **Source Time** and **Timeline Time**:

* **Source Time**: Represents time offsets within the original raw media asset on disk (e.g., seconds 00:10 to 00:30 of `interview.mp4`).
* **Timeline Time**: Represents global time positions on the sequence timeline where the clip is scheduled to play (e.g., seconds 00:45 to 01:05 of the output video).

```text
Raw Source Media Asset (video.mp4):
0s ────────────────────────────── 60s
           │ Source Range │
           10s ────────── 30s (source_duration = 20s)
                 │
                 ▼ Placed onto Timeline
Output Sequence Timeline:
0s ──────────────────────────────────────── 100s
                       │ Timeline Position │
                       45s ────────────── 65s (timeline_duration = 20s)
```

### B. Derived vs. Stored Bounds
To eliminate redundant or inconsistent state (where `start + duration != end`), the IR stores primary primitive fields:
* `timeline_start`: Microseconds from sequence start.
* `timeline_duration`: Microseconds span on timeline.
* `source_start`: Microseconds offset inside raw asset file.
* `source_duration`: Microseconds span inside raw asset file.

Derived properties (`timeline_end` and `source_end`) are computed dynamically:
$$\text{timeline\_end} = \text{timeline\_start} + \text{timeline\_duration}$$
$$\text{source\_end} = \text{source\_start} + \text{source\_duration}$$

---

## 2. Canonical Time Representation

### Evaluation of Time Types

| Representation Type | Precision | Drift Risk | Frame Accuracy | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Floating-Point Seconds** | Inexact IEEE 754 float | **High** (Accumulates drift on repeated edits) | Poor ($0.1 + 0.2 \neq 0.3$) | Rejected |
| **Integer Milliseconds** | $1\text{ ms} = 1,000\ \mu\text{s}$ | Low | Sub-optimal for 23.976/29.97/59.94 FPS | Rejected |
| **Integer Microseconds ($\mu\text{s}$)** | $1\text{ second} = 1,000,000\ \mu\text{s}$ | **Zero Integer Drift** | High (Exact representation down to $1\ \mu\text{s}$) | **Selected Canonical Format** |
| **Rational Time (Numerator/Denominator)**| Exact fraction | Zero | High | Complex for simple operations |

### Microsecond Conversion & Frame Rules
1. **Canonical Storage**: All internal timeline offsets, source ranges, asset durations, and operation parameters are stored as 64-bit integer microseconds (`int`).
2. **Standard Frame Rates**:
   * $30.0\text{ FPS} \rightarrow 33,333\ \mu\text{s per frame}$ ($1,000,000 / 30$).
   * $60.0\text{ FPS} \rightarrow 16,666\ \mu\text{s per frame}$ ($1,000,000 / 60$).
   * $24.0\text{ FPS} \rightarrow 41,666\ \mu\text{s per frame}$ ($1,000,000 / 24$).
3. **Conversion Helpers**: `TimelineTime.from_seconds(float_sec)` and `TimelineTime.to_seconds()` provide clean serialization interfaces while keeping internal calculations strictly integral.

---

## 3. Non-Destructive Editing Architecture

All video editing operations in the system are strictly **non-destructive metadata operations**:
* Original source video/audio files on disk (`/workspace/media/video.mp4`) are marked **read-only**.
* Trimming, cutting, splitting, cropping, and audio adjustments create or update metadata references in the project IR.
* Media files are never altered, moved, or overwritten during state operations.

---

## 4. State Management: Copy-on-Write Transactional Engine

To guarantee system stability, support infinite Undo/Redo, and prevent partial state corruption, the State Engine uses a **Copy-on-Write Transactional Pattern**:

1. **Transaction Isolation**: When an atomic operation is executed, the engine creates a deep copy of the `VideoProject` state.
2. **Validation Gate**: The candidate state is evaluated against domain integrity rules (e.g., asset existence, time bounds, clip overlaps, track locking).
3. **Atomic Commit**: If validation succeeds, the new state replaces the current state, and the operation is recorded in `HistoryManager`.
4. **Rollback**: If validation fails, domain exceptions are raised (`InvalidTimeRangeError`, `TrackLockedError`), and the original project state remains 100% untouched.

---

## 5. Command-Based Operation Semantics

All state modifications are represented as strongly-typed, serializable atomic operations:
* `ADD_TRACK`: Creates a new video, audio, text, subtitle, or effect track layer.
* `DELETE_TRACK`: Removes a track and its contained clips.
* `ADD_CLIP`: Inserts a clip referencing a media asset.
* `DELETE_CLIP`: Removes a clip from a track.
* `TRIM_CLIP`: Modifies a clip's source range and timeline duration.
* `SPLIT_CLIP`: Splits a single clip into two adjacent clips at a specific split timestamp.
* `MOVE_CLIP`: Repositions a clip on the timeline or moves it between compatible tracks.
* `SET_CLIP_VOLUME`: Updates clip audio volume and mute status.
* `SET_CLIP_TRANSFORM`: Sets spatial position, scale, and rotation.

Every operation carries a unique `operation_id`, `operation_type`, `timestamp`, `actor` (`USER`, `AI`, `SYSTEM`), and payload dictionary, providing a complete audit trail for replay and AI debugging.