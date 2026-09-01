# AI Video Editor Phase 2D — Subsystem Architecture

## Executive Summary
This document specifies the software architecture, package extensions, data flows, and component responsibilities for Phase 2D (Transitions, Speed Control, Keyframe Animation & Effects).

---

## 1. Package Structure Extensions

Phase 2D extends the `video_editor.ir` and `video_editor.compiler` packages:

```text
video_editor/
├── ir/                     # Universal Video Editing IR Core
│   ├── animation.py        # Keyframe, AnimationTrack, InterpolationType, AnimatedProperty
│   ├── transitions.py      # TransitionType (CUT, FADE, DISSOLVE, WIPE_LEFT), Transition
│   └── effects.py          # EffectType (BLUR, BRIGHTNESS, CONTRAST, GRAYSCALE, VIGNETTE), Effect
└── compiler/               # Timeline Compiler Subsystem
    ├── interpolation.py    # InterpolationEngine (HOLD & LINEAR keyframe evaluation)
    ├── animation.py        # AnimationCompiler (Compiles position, scale, opacity tracks)
    ├── speed.py            # SpeedCompiler (setpts & chained atempo filter nodes)
    ├── transitions.py      # TransitionCompiler (xfade, afade, acrossfade nodes & overlaps)
    └── effects.py          # EffectCompiler (Blur, brightness, contrast, grayscale, vignette)
```

---

## 2. Multi-Stage Pipeline Data Flow

```text
                             VideoProject IR
                                    │
                                    ▼
                         validate_project_renderability()
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
     SpeedCompiler           AnimationCompiler       EffectCompiler
   (setpts & atempo)       (HOLD / LINEAR eval)   (Temporal intervals)
            │                       │                       │
            └───────────────────────┼───────────────────────┘
                                    │
                                    ▼
                             VideoCompositor
                        (Z-Ordered Overlay Chains)
                                    │
                                    ▼
                           TransitionCompiler
                       (xfade & acrossfade blend)
                                    │
                                    ▼
                             RenderPlanner
                       (FilterGraph & FFmpegCommand)
```

---

## 3. Key Component Invariants

1. **IR Independence**: All Phase 2D animation, transition, and speed models exist in `video_editor.ir` as pure data structures without FFmpeg syntax.
2. **Speed-Time Invariant**: When speed multiplier $S > 0$ is applied, `timeline_duration_us = round(source_duration_us / S)`.
3. **Transition Overlap Invariant**: Visual transitions (`xfade`) consume overlapping tail/head segments of adjacent clips over `duration_us` without altering total project duration.