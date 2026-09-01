# Universal Video Editing Intermediate Representation (IR) Specification v1.0.0

## 1. Specification Overview
This document specifies the authoritative, editor-independent JSON Schema and domain model specification for the **Universal Video Editing Intermediate Representation (IR) v1.0.0**.

The IR serves as the canonical source of truth for the AI Video Editing System. It is completely decoupled from render engines (FFmpeg, Remotion, MLT), GUI editors (CapCut, Premiere), and AI planners.

---

## 2. Terminology & Core Rules
* **Project**: The root container encapsulating settings, media asset inventory, timeline tracks, and clips.
* **TimelineTime**: Integer microseconds ($1\text{ s} = 1,000,000\ \mu\text{s}$) measuring time positions and durations without floating-point rounding drift.
* **Asset**: A registered source file (video, audio, image, font) stored on local disk.
* **Track**: A layer in the timeline stack sorted by `index` (z-order for video/text/subtitle; mixing order for audio).
* **Clip**: A placed instance of a media asset or text element residing on a specific track.
* **Source Range**: The trimmed slice inside the raw media file (`source_start` to `source_start + source_duration`).
* **Timeline Range**: The position inside the output video sequence (`timeline_start` to `timeline_start + timeline_duration`).

---

## 3. Domain Model Schemas

### A. Project Settings (`ProjectSettings`)
* `width`: Positive integer pixel width (e.g., 1080, 1920, 3840). Default: 1080.
* `height`: Positive integer pixel height (e.g., 1920, 1080, 1080). Default: 1920.
* `fps`: Floating-point frame rate (e.g., 24.0, 25.0, 29.97, 30.0, 60.0). Default: 30.0.
* `aspect_ratio`: String enum (`16:9`, `9:16`, `1:1`, `4:5`, `Custom`). Default: `9:16`.
* `timebase`: String enum (`microseconds`). Default: `microseconds`.
* `background_color`: Hex color string (e.g., `#000000`). Default: `#000000`.

### B. Media Asset (`Asset`)
* `id`: String UUID.
* `type`: AssetType enum (`VIDEO`, `AUDIO`, `IMAGE`, `FONT`).
* `path`: Local filesystem path string.
* `duration_us`: Integer microseconds duration of source media file.
* `metadata`: Optional dictionary (width, height, fps, sample_rate, channels, file_size).

### C. Track (`Track`)
* `id`: String UUID.
* `name`: User-visible track label string.
* `type`: TrackType enum (`VIDEO`, `AUDIO`, `TEXT`, `SUBTITLE`, `EFFECT`).
* `index`: Non-negative integer z-order (0 = background layer; higher indices render on top).
* `muted`: Boolean flag (default `False`).
* `locked`: Boolean flag (default `False`).
* `clips`: Array of `Clip` objects.

### D. Clip (`Clip`)
* `id`: String UUID.
* `asset_id`: String UUID referencing a registered Asset (or `None` for text elements).
* `timeline_start_us`: Integer microsecond timeline start position.
* `timeline_duration_us`: Integer microsecond duration on timeline.
* `source_start_us`: Integer microsecond offset inside raw asset file.
* `source_duration_us`: Integer microsecond duration inside raw asset file.
* `speed`: Float speed multiplier (default `1.0`, range $0.1$ to $10.0$).
* `transform`: `Transform` object.
* `audio`: `AudioConfig` object.
* `text`: Optional `TextStyle` object (for text/subtitle clips).
* `effects`: Array of `Effect` objects.
* `transitions`: Optional transition dictionary (`in_transition`, `out_transition`).

### E. Transform (`Transform`)
* `position_x`: Float pixel offset from canvas center (default `0.0`).
* `position_y`: Float pixel offset from canvas center (default `0.0`).
* `scale_x`: Float scale multiplier (default `1.0`).
* `scale_y`: Float scale multiplier (default `1.0`).
* `rotation`: Float degrees rotation (default `0.0`, range $-360.0$ to $360.0$).

### F. Audio Configuration (`AudioConfig`)
* `volume`: Float volume multiplier (default `1.0`, range $0.0$ to $2.0$).
* `muted`: Boolean flag (default `False`).
* `fade_in_us`: Integer microsecond fade-in duration (default `0`).
* `fade_out_us`: Integer microsecond fade-out duration (default `0`).

---

## 4. Derived Project Properties
* `duration_us`: Computed as $\max(\text{clip.timeline\_end\_us})$ across all tracks and clips in the project. If project contains zero clips, `duration_us = 0`.

---

## 5. Validation Invariants
1. `timeline_start_us >= 0` and `timeline_duration_us > 0`.
2. `source_start_us >= 0` and `source_duration_us > 0`.
3. If clip references `asset_id`: `source_start_us + source_duration_us <= asset.duration_us`.
4. Clip `asset_id` must reference a valid asset in `project.assets`.
5. Non-overlapping rule on single video tracks: Clips on the same `VIDEO` track must not overlap in `timeline_range`.
6. Locked tracks reject all clip mutation operations (`ADD_CLIP`, `DELETE_CLIP`, `TRIM_CLIP`, `SPLIT_CLIP`, `MOVE_CLIP`).