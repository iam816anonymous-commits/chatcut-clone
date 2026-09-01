# AI Video Editing System Architecture

## Overview & Core Paradigm

Modern AI-assisted video editing systems must separate **intent understanding** from **pixel rendering**. AI models excel at reasoning, narrative structuring, time-range calculation, and media organization, but are unsuitable for direct frame-by-frame raster manipulation.

Therefore, the system follows a **decoupled, event-driven, pipeline-based architecture** where natural language commands are converted into a deterministic **Universal Video Editing Intermediate Representation (IR)**, validated, and executed by dedicated video processing engines.

---

## Conceptual Pipeline Architecture

```text
User Natural Language Request
             │
             ▼
   ┌───────────────────┐
   │    AI Planner     │ ◄── Inspects Media Metadata (Durations, Audio Tracks, Transcripts)
   └─────────┬─────────┘
             │ Produces Proposed Editing Operations
             ▼
   ┌───────────────────┐
   │ Editing Validator │ ◄── Verifies Timestamps, Assets, Overlaps, Resource Bounds
   └─────────┬─────────┘
             │ Validated IR State
             ▼
   ┌───────────────────┐
   │ Execution Engine  │ ◄── Applies Operations to IR Project State
   └─────────┬─────────┘
             │ Updated Timeline IR
             ▼
   ┌───────────────────┐
   │ Preview Renderer  │ ◄── Generates Fast, Low-Resolution Draft Preview
   └─────────┬─────────┘
             │
             ▼
   ┌───────────────────┐
   │ User Review &     │ ── (Rejections loop back to AI Planner with feedback)
   │ Approval Layer    │
   └─────────┬─────────┘
             │ Approved
             ▼
   ┌───────────────────┐
   │   Final Render    │ ◄── Full-Resolution Multi-Threaded Video Export
   └───────────────────┘
```

---

## Component Roles & Responsibilities

### 1. AI Planner (Intent Translation Engine)
* **Role**: Translates user intent (e.g., *"Cut silent parts, create a 30s vertical TikTok clip, and add auto-captions"*) into structured IR operations.
* **Inputs**:
  * User prompt / instruction.
  * Media metadata (file formats, resolutions, frame rates, audio waveform analysis, auto-whisper transcriptions with word-level timestamps).
  * Current project IR state.
* **Outputs**: Structured JSON array of candidate operations (e.g., `TRIM_CLIP`, `ADD_TEXT`, `SPLIT_CLIP`).
* **Implementation Strategy**: LLM structured outputs (JSON schema / tool calls) enforced by system prompts and function definitions.

### 2. Editing Validator (Deterministic Quality & Safety Gate)
* **Role**: Ensures LLM-generated operations are logically consistent, non-destructive, and within valid boundaries before execution.
* **Validation Checks**:
  * **Asset Existence**: All referenced `asset_id`s exist in project inventory.
  * **Time Range Sanity**: Start time < End time; start time $\ge 0$; end time $\le$ source asset duration.
  * **Track Constraints**: Prevents overlap on single-media tracks where prohibited.
  * **Resource Limits**: Restricts memory/CPU allocation bounds and frame dimensions.
  * **Safety / Policy**: Flags prohibited filters or unsafe operation sequences.

### 3. Execution Engine (State Machine)
* **Role**: Manages in-memory state transitions of the Video Editing IR.
* **Responsibilities**:
  * Applies atomic operations (`ADD_TRACK`, `INSERT_CLIP`, `DELETE_CLIP`, `SPLIT_CLIP`, `APPLY_EFFECT`).
  * Maintains undo/redo state history trees.
  * Computes overall project duration, track z-indexes, and stream compositions.

### 4. Preview Renderer (Real-time Feedback Engine)
* **Role**: Provides fast visual feedback to the user without triggering long full-resolution renders.
* **Strategies**:
  * **Proxy Rendering**: Generates 360p / 480p preview clips using ultrafast FFmpeg presets (`-preset ultrafast`).
  * **In-Browser Web Canvas**: Renders timeline sequences in real-time via HTML5 `<canvas>` / WebCodecs using client-side frame scrubbing.

### 5. Human-in-the-Loop Approval Layer
* **Role**: Gives users full control over AI actions prior to final rendering.
* **Workflow**:
  1. AI proposes changes & preview.
  2. User inspects visual preview & operation list.
  3. User accepts, modifies, or rejects changes.
  4. On approval, system executes final render or proceeds to next editing step.

### 6. Final Rendering Engine
* **Role**: Compiles the validated, approved Universal IR into high-quality output media (MP4/H.264, MOV/ProRes, WebM).
* **Backends**: Programmatic rendering backends including **FFmpeg**, **Remotion**, or **MLT Framework**.

---

## Architecture Architectural Evaluation (Options Comparison)

| Option | Architecture Pattern | Viability | Technical Assessment |
| :--- | :--- | :--- | :--- |
| **Option A** | Direct CapCut API Integration | **Impossible** | CapCut does not provide a public REST/GraphQL API. |
| **Option B** | AI Planner + CapCut GUI Automation | **Brittle & Not Recommended** | High failure rate, UI/resolution dependence, non-deterministic, violates TOS. |
| **Option C** | Universal IR + Native FFmpeg Engine | **Highly Viable (Recommended for Core Stack)** | Fully deterministic, local-first, zero cost, cross-platform, extremely performant. |
| **Option D** | Universal IR + Remotion (React Rendering) | **Highly Viable (Recommended for Web/Templates)** | React component-based rendering, ideal for motion graphics, captions, and dynamic overlays. |
| **Option E** | Hybrid Architecture (Universal IR $\rightarrow$ FFmpeg Core + Optional CapCut Draft Exporter) | **Best Strategic Architecture** | Complete autonomy via FFmpeg/Remotion, with best-effort `.draft` export for users who wish to do final polish in CapCut manually. |

---

## Hybrid Architecture Deep Dive (Recommended Approach)

```text
               ┌────────────────────────┐
               │   AI Video Assistant   │
               └───────────┬────────────┘
                           │
                           ▼
               ┌────────────────────────┐
               │ Universal Video Editing│
               │   IR (Canonical State) │
               └───────────┬────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
  ┌─────────────────────┐    ┌────────────────────────┐
  │ Primary Native      │    │ Optional Exporter      │
  │ Renderer (FFmpeg /  │    │ Module                 │
  │ Remotion)           │    │ (CapCut Draft Exporter)│
  └──────────┬──────────┘    └───────────┬────────────┘
             │                           │
             ▼                           ▼
  ┌─────────────────────┐    ┌────────────────────────┐
  │ Final Video Output  │    │ Unofficial CapCut      │
  │ (MP4/WebM/ProRes)   │    │ Draft Project Folder   │
  └─────────────────────┘    └────────────────────────┘
```

By maintaining the canonical project state inside our open **Universal Video Editing IR**, the system remains resilient, scalable, and vendor-independent. Users gain complete AI video editing capability without relying on fragile CapCut automation.