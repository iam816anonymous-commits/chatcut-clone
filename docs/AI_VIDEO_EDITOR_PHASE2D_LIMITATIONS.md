# Phase 2D Known Limitations Specification

This document details explicit technical boundaries, unsupported features, and deliberate tradeoffs in the Phase 2D compiler and state engine.

---

## 1. Speed Adjustment Limitations

1. **Clip Boundary Recalculation:** Adjusting clip speed dynamically alters timeline duration. Downstream clips on single-track layers are NOT automatically shifted; overlaps must be resolved via atomic state operations or validator gates.
2. **Extreme Speed Range Limits:** Speed multipliers $S < 0.1$ or $S > 10.0$ are rejected to prevent audio buffer overflow or extreme frame drop instability in FFmpeg rendering pipelines.

---

## 2. Transition Limitations

1. **Cross-Track Transitions:** Transitions (`xfade` / `acrossfade`) are currently compiled between adjacent clips on the same track. Multi-track cross-layer transitions require explicit layer compositing.
2. **Transition Overlaps:** Simultaneous overlapping transitions on a single clip (e.g. `transition_in` duration exceeding clip duration) are rejected by pre-compilation validation gates.

---

## 3. Keyframe Animation Limitations

1. **Non-Linear Bezier Curves:** Interpolation currently supports `HOLD` and `LINEAR` modes. Cubic Bezier or custom easing curves are deferred to future releases.
2. **3D Spatial Rotation:** Transforms and animations operate strictly in 2D Euclidean space ($X, Y$, Scale, Opacity). 3D perspective transforms are not supported.

---

## 4. Reusable Effect Limitations

1. **CPU/GPU Compute Scaling:** Heavy visual effect stacks (e.g., combining high-radius blur with complex color grading across multiple 4K tracks) increase CPU/GPU render latency. Real-time rendering is not guaranteed for multi-layer 4K output without preview downscaling.
