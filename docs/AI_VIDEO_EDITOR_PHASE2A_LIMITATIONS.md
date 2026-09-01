# AI Video Editor Phase 2A — Limitations & Non-Goals

## Executive Summary
This document explicitly lists the architectural boundaries, intentionally omitted features, and technical limitations of Phase 2A (Media Inspection & FFmpeg Render Foundation).

---

## Explicit Phase 2A Limitations

### 1. Rendering Limitations
* **NO Full Timeline Filtergraph Compiler**: Phase 2A provides atomic primitives (`render_trim`, `render_scale`, `render_transcode`). Full multi-track project composition is scheduled for Phase 2B.
* **NO Multi-Track Overlay Mixing**: Complex video compositing across Z-ordered tracks is out of scope for Phase 2A.
* **NO Transitions or Visual Effects**: Blur, opacity blending, crossfades, and motion graphics are not compiled to FFmpeg complex filtergraphs yet.
* **NO Audio Mixing or Silence Removal**: Audio ducking and RMS energy silence detection belong to future phases.

### 2. Infrastructure & Integration Limitations
* **NO AI Planner or Whisper Transcription**: Speech-to-text transcription and natural language translation are out of scope.
* **NO Preview UI or Web Frontend**: No Next.js timeline component or HTML5 canvas scrubbing player.
* **NO GPU Scheduling or Distributed Workers**: Rendering runs locally on single CPU processes via `subprocess.run`.
* **NO CapCut or Remotion Exporters**: No `.draft` project folder generation or React component compilation.