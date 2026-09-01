# Phase 2D Transition Specification

This document specifies the IR model representations and compiler rules for video (`xfade`) and audio (`acrossfade` / `afade`) clip transitions.

---

## 1. Supported Transition Types

| Type Identifier | Category | Video FFmpeg Equivalent | Audio FFmpeg Equivalent |
| :--- | :--- | :--- | :--- |
| `CROSSFADE` | DISSOLVE | `xfade=transition=fade` | `acrossfade=d=D:c1=tri:c2=tri` |
| `FADE` | FADE | `xfade=transition=fade` | `acrossfade=d=D` / `afade` |
| `FADE_BLACK` | FADE | `xfade=transition=fadeblack` | `afade=t=out:st=T1:d=D` |
| `FADE_WHITE` | FADE | `xfade=transition=fadewhite` | `afade=t=out:st=T1:d=D` |
| `WIPE_LEFT` | WIPE | `xfade=transition=wipeleft` | N/A (Video only) |
| `WIPE_RIGHT` | WIPE | `xfade=transition=wiperight` | N/A (Video only) |
| `WIPE_UP` | WIPE | `xfade=transition=wipeup` | N/A (Video only) |
| `WIPE_DOWN` | WIPE | `xfade=transition=wipedown` | N/A (Video only) |
| `SLIDE_LEFT` | SLIDE | `xfade=transition=slideleft` | N/A (Video only) |
| `SLIDE_RIGHT` | SLIDE | `xfade=transition=slideright` | N/A (Video only) |
| `DISSOLVE` | DISSOLVE | `xfade=transition=dissolve` | `acrossfade=d=D` |

---

## 2. Temporal & Boundary Rules

1. **Duration Bounds:** Transition duration MUST be strictly greater than 0 microseconds (`duration_us > 0`).
2. **Clip Duration Constraint:** Transition duration cannot exceed the duration of either participating clip segment (`duration_us <= clip.timeline_duration_us`).
3. **Offset Calculation:** For adjacent clips $C_1$ and $C_2$ on a track where transition occurs at time $T_{boundary}$, the transition offset in seconds is:
   $$\text{offset} = \frac{T_{boundary} - \text{duration\_us}}{1,000,000}$$
4. **Deterministic Synthesis:** The compiler outputs pure `xfade` and `acrossfade` filter node specifications without mutating input clip boundaries.
