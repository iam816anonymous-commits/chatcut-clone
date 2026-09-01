# AI Video Editor Phase 2D — Technical Research & Engineering Foundations

## Executive Summary
This document establishes the technical research foundation for Phase 2D, investigating FFmpeg visual transitions (`xfade`), audio transitions (`afade`/`acrossfade`), speed control (`setpts`/`atempo`), keyframe animation interpolation (HOLD, LINEAR), temporal expressions, reusable effects, and rendering pipeline order.

---

## 1. Video & Audio Transitions

### A. FFmpeg `xfade` Filter
FFmpeg's `xfade` filter blends two video streams over a specified duration:

```text
[v0][v1] xfade=transition=fade:duration=1.0:offset=4.0 [outv]
```

* `transition`: Transition effect type (`fade`, `dissolve`, `wipeleft`, `wiperight`, `slideleft`, `slideright`).
* `duration`: Transition overlap duration in seconds ($1.0\text{s} = 1,000,000\ \mu\text{s}$).
* `offset`: Timeline timestamp in seconds where the transition blend begins ($t_{\text{offset}} = t_{\text{clip1\_end}} - t_{\text{transition\_duration}}$).

### B. Audio Crossfades (`acrossfade` & `afade`)
Audio transitions blend adjacent audio streams using `acrossfade`:

```text
[a0][a1] acrossfade=d=1.0:c1=tri:c2=tri [outa]
```

Or individual clip fade-in / fade-out curves using `afade`:

```text
[a_in] afade=t=in:st=0:d=1.0, afade=t=out:st=4.0:d=1.0 [a_out]
```

---

## 2. Speed Control (`setpts` & `atempo`)

Changing playback speed alters clip duration:

$$\text{timeline\_duration\_us} = \text{round}\left(\frac{\text{source\_duration\_us}}{\text{speed}}\right)$$

### A. Video Speed (`setpts`)
Video presentation timestamps are scaled by the inverse speed factor ($1 / \text{speed}$):

* **2.0x Speed**: `setpts=0.5*PTS`
* **0.5x Speed**: `setpts=2.0*PTS`

```text
[v_trim] setpts=0.5*PTS [v_speed]
```

### B. Audio Speed (`atempo`)
FFmpeg's `atempo` filter adjusts audio playback tempo without altering pitch. Each `atempo` instance supports speed values between $0.5$ and $2.0$. Speeds outside this range are chained sequentially:

* **0.25x Speed**: `atempo=0.5,atempo=0.5`
* **4.0x Speed**: `atempo=2.0,atempo=2.0`

---

## 3. Keyframe Animation & Interpolation

Keyframes define property values at specific clip-local time offsets ($t \in [0, \text{timeline\_duration\_us}]$):

### A. Interpolation Algorithms
Given two adjacent keyframes $K_1 = (t_1, v_1)$ and $K_2 = (t_2, v_2)$ with query time $t \in [t_1, t_2]$:

1. **HOLD**: Value remains constant until $t_2$:
   $$V(t) = v_1$$
2. **LINEAR**: Value changes linearly with time:
   $$\alpha = \frac{t - t_1}{t_2 - t_1}, \quad V(t) = v_1 + \alpha (v_2 - v_1)$$

### B. FFmpeg Expression Compilation
For spatial properties (`POSITION_X/Y`, `OPACITY`), keyframe tracks can be evaluated at compilation time or compiled into FFmpeg math expressions (e.g., `x='if(gte(t,1), 100+(t-1)*50, 0)'`).

---

## 4. Reusable & Temporal Effects

Visual effects modify stream pixel buffers:
* **BLUR**: `gblur=sigma=10`
* **BRIGHTNESS**: `eq=brightness=0.2`
* **CONTRAST**: `eq=contrast=1.5`
* **GRAYSCALE**: `colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3`
* **VIGNETTE**: `vignette=PI/4`

Temporal interval bounds ($t_{\text{start}}$ to $t_{\text{end}}$) use the `enable='between(t,start,end)'` filter option.

---

## 5. Canonical Rendering Pipeline Order

To prevent filter order ambiguities, all stream processing follows a strict canonical execution pipeline:

```text
SOURCE MEDIA
     │
     ▼
1. TRIM (source_start -> source_end)
     │
     ▼
2. SPEED CONTROL (setpts / atempo)
     │
     ▼
3. SCALE & CANVAS HARMONIZATION (scale / fps / aformat)
     │
     ▼
4. KEYFRAME ANIMATION & TRANSFORMS (scale / position / opacity)
     │
     ▼
5. REUSABLE & TEMPORAL EFFECTS (blur / brightness / contrast / vignette)
     │
     ▼
6. MULTI-TRACK COMPOSITING (overlay / amix)
     │
     ▼
7. TRANSITIONS (xfade / acrossfade)
     │
     ▼
FINAL CANVAS & OUTPUT MEDIA
```

By preserving this strict pipeline order, the IR remains completely clean and deterministic across all rendering targets.