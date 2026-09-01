# Phase 2D Temporal Semantics Specification

This document defines the strict microsecond integer timing rules and clock transformations across the video compilation pipeline.

---

## 1. Microsecond Integer Precision Rules

1. **Canonical Time Unit:** All timeline coordinates, durations, trim boundaries, keyframe offsets, transition durations, and effect temporal intervals MUST be stored and computed as non-negative 64-bit integers (`int`) representing microseconds ($\mu\text{s}$).
   $$1 \text{ second} = 1,000,000 \mu\text{s}$$
2. **Elimination of Floating-Point Drift:** Floating-point representations (`float`) are strictly forbidden in internal IR models and state engine calculations. Conversion to floating-point seconds is permitted ONLY at the outer FFmpeg filter string generation interface:
   $$t_{\text{seconds}} = \frac{t_{\mu\text{s}}}{1,000,000.0}$$

---

## 2. Clock Domains & Transformations

The compiler manages three distinct clock domains:

1. **Source Clock ($t_{\text{src}}$):** Un-trimmed timeline position within the raw media file on disk.
2. **Clip Local Clock ($t_{\text{clip}}$):** Trimmed relative position within the clip segment ($0 \le t_{\text{clip}} \le \text{source\_duration\_us}$).
3. **Timeline Canvas Clock ($t_{\text{timeline}}$):** Absolute composite timeline offset ($t_{\text{timeline}} = \text{timeline\_start\_us} + t_{\text{clip\_effective}}$).

### Speed-Adjusted Effective Duration

When a clip speed multiplier $S > 0$ is applied:

$$t_{\text{clip\_effective}} = \left\lfloor \frac{t_{\text{clip}}}{S} \right\rfloor$$

$$\text{timeline\_duration\_us} = \left\lfloor \frac{\text{source\_duration\_us}}{S} \right\rfloor$$

---

## 3. Boundary Invariants

* **Non-Overlap:** Clips on single-track layers must satisfy:
  $$\text{Clip}_{i}.\text{timeline\_start\_us} + \text{Clip}_{i}.\text{timeline\_duration\_us} \le \text{Clip}_{i+1}.\text{timeline\_start\_us}$$
* **Non-Negative Microsecond Offsets:** Every timestamp $t_{\mu\text{s}} \ge 0$.
