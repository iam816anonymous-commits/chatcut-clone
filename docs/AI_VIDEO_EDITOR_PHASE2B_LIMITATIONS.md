# AI Video Editor Phase 2B — Limitations & Non-Goals

## Executive Summary
This document explicitly records the scope limits, non-goals, and unsupported features for Phase 2B (Timeline Compilation & Real Project Rendering).

---

## Explicit Phase 2B Non-Goals & Limitations

1. **Unsupported Track Types**:
   * `TEXT` and `SUBTITLE` tracks are NOT compiled or rendered in Phase 2B. Attempting to compile projects containing these track types raises `UnsupportedTrackTypeError`.
2. **Single Visual Track Limit**:
   * Phase 2B supports at most 1 active `VIDEO` track. Multi-layer video compositing across overlapping visual tracks raises `UnsupportedTimelineStructureError`.
3. **No Transitions or Keyframe Animations**:
   * Dissolves, crossfades, keyframed opacity/scale motion, and visual effects are not compiled in Phase 2B.
4. **No Advanced Audio Processing**:
   * Audio ducking, loudness normalization, multi-track audio mixing, and RMS silence detection are out of scope.
5. **No AI / LLM Integration**:
   * Speech-to-text, automatic cutting, scene detection, and prompt translation belong to future phases.
6. **No GPU Acceleration or Proxy Generation**:
   * Renders execute via standard CPU H.264/AAC encoding. Proxy video creation and background queue workers are not included.