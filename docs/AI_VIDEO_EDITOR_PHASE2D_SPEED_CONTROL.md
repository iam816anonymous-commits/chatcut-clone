# Phase 2D Speed Control Specification

This document specifies the IR representation and compilation rules for variable playback speed multipliers on video and audio clips.

---

## 1. Overview & Bounds

Clip speed is specified by a positive floating-point multiplier field `speed: float` on the clip model (where default speed is `1.0`).

* **Valid Speed Range:** $0.1 \le \text{speed} \le 10.0$ (values $\le 0.0$ are rejected by validation gates).
* **Slow Motion:** $\text{speed} < 1.0$ (e.g., $0.5$ for half speed).
* **Fast Forward:** $\text{speed} > 1.0$ (e.g., $2.0$ for double speed).

---

## 2. Video Speed Compilation (`setpts`)

For video streams, speed modification is achieved by adjusting Presentation Timestamps (PTS) using the FFmpeg `setpts` filter.

### Formula

$$\text{PTS\_FACTOR} = \frac{1.0}{\text{speed}}$$

$$\text{Filter String} = \text{"setpts="} + \text{PTS\_FACTOR} + \text{"*PTS"}$$

### Examples

* **Speed = 2.0 (Fast):** `setpts=0.500000*PTS`
* **Speed = 0.5 (Slow):** `setpts=2.000000*PTS`

---

## 3. Audio Speed Compilation (`atempo`)

FFmpeg's `atempo` filter modifies audio playback tempo without altering pitch, but restricts input multipliers to the interval $[0.5, 2.0]$.

To support speeds outside $[0.5, 2.0]$, the compiler automatically chains multiple `atempo` filter nodes.

### Chaining Rules

1. **For $\text{speed} > 2.0$:** Insert multiple `atempo=2.0` nodes until remaining factor $\le 2.0$.
2. **For $\text{speed} < 0.5$:** Insert multiple `atempo=0.5` nodes until remaining factor $\ge 0.5$.

### Examples

* **Speed = 4.0:** `["atempo=2.0", "atempo=2.0"]`
* **Speed = 0.25:** `["atempo=0.5", "atempo=0.5"]`
* **Speed = 1.5:** `["atempo=1.500000"]`

---

## 4. Effect on Clip Timeline Duration

When speed factor $S$ is applied to source clip segment duration $D_{\text{source}}$, the resulting effective timeline duration $D_{\text{timeline}}$ is:

$$D_{\text{timeline}} = \left\lfloor \frac{D_{\text{source}}}{S} \right\rfloor$$

All microsecond temporal calculations reflect this transformed duration.
