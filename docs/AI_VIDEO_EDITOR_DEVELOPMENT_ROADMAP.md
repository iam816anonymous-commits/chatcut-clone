# AI Video Editor Phased Development Roadmap

## Overview
This roadmap details the sequential execution plan for building the AI-assisted video editing platform. Development is structured across seven distinct phases, progressing from core architectural research to advanced multimodal capabilities.

---

## Phase Execution Plan

```text
Phase 0: Architecture Validation (Research & Benchmarks)
   │
   ▼
Phase 1: Universal Video Editing IR Core State Engine
   │
   ▼
Phase 2: FFmpeg Execution Engine & Render Pipeline
   │
   ▼
Phase 3: Fast Preview & Media Scrubbing System
   │
   ▼
Phase 4: AI Planner & Structured Instruction Engine
   │
   ▼
Phase 5: Agent Tool Integration & Validation Layer
   │
   ▼
Phase 6: Advanced Features (Optional CapCut Draft Exporter & Remotion Motion Graphics)
```

---

## Phase Details & Deliverables

### Phase 0: Architecture Validation (COMPLETED)
* **Goal**: Technical feasibility research on CapCut, APIs, TOS, and rendering backends.
* **Deliverables**:
  * `CAPCUT_INTEGRATION_RESEARCH.md`
  * `AI_VIDEO_EDITING_ARCHITECTURE.md`
  * `VIDEO_EDITING_IR_PROPOSAL.md`
  * `VIDEO_EDITOR_TECHNOLOGY_COMPARISON.md`
  * `AI_VIDEO_EDITOR_THREAT_MODEL.md`
  * `AI_VIDEO_EDITOR_MVP_PLAN.md`
  * `AI_VIDEO_EDITOR_DEVELOPMENT_ROADMAP.md`
  * `VIDEO_EDITOR_RESEARCH_FINAL_REPORT.md`

### Phase 1: Video Editing IR State Engine
* **Goal**: Build the core data structures and state management for projects, assets, tracks, and clips.
* **Deliverables**:
  * Pydantic schemas for Video IR JSON format.
  * In-memory project state manager with undo/redo stack.
  * Unit tests validating JSON import/export and track z-ordering.

### Phase 2: FFmpeg Execution Engine
* **Goal**: Implement deterministic rendering functions that convert IR track states into FFmpeg filtergraph strings.
* **Deliverables**:
  * `FFmpegBuilder` module (`trim`, `concat`, `overlay`, `volume`, `crop`, `speed`).
  * Audio normalization and silence removal algorithm (`ffmpeg silencedetect`).
  * Subtitle renderer utilizing ASS/SRT subtitles with custom styling.
  * Integration tests verifying pixel accuracy and audio sync across sample renders.

### Phase 3: Preview & Media Scrubbing System
* **Goal**: Provide real-time UI scrubbing and ultra-fast draft previews.
* **Deliverables**:
  * Fast proxy generator (360p @ 15fps, `-preset ultrafast`).
  * Next.js frontend timeline player with frame-accurate HTML5 video scrubbing.
  * API endpoint `POST /api/v1/preview` returning low-res preview video URLs in <3 seconds.

### Phase 4: AI Planner Engine
* **Goal**: Integrate LLMs to parse natural language instructions and construct valid IR operation JSONs.
* **Deliverables**:
  * System prompt suite enforcing Pydantic schema outputs.
  * Whisper transcription integration (`faster-whisper`) generating word-level time codes.
  * NL-to-IR translation tests covering trimming, subtitle generation, and reframing commands.

### Phase 5: Agent Tools & Validation Layer
* **Goal**: Wrap IR operations in agent tool definitions with deterministic safety gates.
* **Deliverables**:
  * Safety validator checking asset paths, time collisions, and resource bounds.
  * Tool calling suite (`inspect_media`, `trim_clip`, `remove_silence`, `add_subtitles`).
  * Human-in-the-loop review interface showing proposed changes prior to execution.

### Phase 6: Advanced Features & Secondary Exporters
* **Goal**: Expand visual capabilities and optional third-party interoperability.
* **Deliverables**:
  * **Experimental CapCut Exporter**: Generator for `.draft` project folders containing `draft_content.json` for users who want manual CapCut polishing.
  * **Remotion Template Engine**: React-based motion graphics for animated title cards and dynamic overlays.
  * Auto B-roll generator matching transcript keywords to local stock media libraries.