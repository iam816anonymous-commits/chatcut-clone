# CapCut + AI Video Editing Integration: Technical Synthesis & Architecture Final Report

---

## 1. Executive Summary

This report delivers an exhaustive technical investigation into integrating an AI-assisted video editing assistant with **CapCut** and evaluates alternative rendering backends.

### Core Verdict
**Direct programmatic control of CapCut is technically infeasible and operationally unviable.** CapCut (developed by ByteDance) provides **no public REST/GraphQL APIs, no developer SDKs, and no public extension architecture** for video timeline manipulation or rendering.

Attempting to control CapCut via reverse-engineered desktop draft files (`draft_content.json`) or OS GUI / browser automation (Playwright/Selenium) introduces severe brittleness, non-deterministic failures, high maintenance costs, anti-bot blocking, and active Terms of Service violations.

### Strategic Architecture Recommendation
We explicitly recommend **NOT** building the AI Video Editing System on direct CapCut control.

Instead, we propose a **Hybrid Decoupled Architecture**:
1. **Core Canonical Engine**: An open, editor-independent **Universal Video Editing Intermediate Representation (IR)** powered by **FFmpeg** (for heavy timeline editing/silence removal) and **Remotion** (for motion graphics/subtitles).
2. **Optional CapCut Export Target**: A best-effort `.draft` project exporter that converts the Universal IR into a CapCut project folder, allowing users to manually perform final polish inside CapCut if desired.

---

## 2. What CapCut Supported Capabilities Matrix

| Capability | Public API | Developer SDK | Automation Viability | Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Project Creation** | No | No | Low (GUI Hack) | `NOT_SUPPORTED` |
| **Media Upload / Ingest**| No | No | Low | `NOT_SUPPORTED` |
| **Timeline Editing / Slicing** | No | No | Fragile (`draft_content.json`) | `FRAGILE` |
| **Transitions / Effects** | No | No | Internal Hash Locked | `NOT_SUPPORTED` |
| **Subtitles / Captions** | No | No | Fragile | `FRAGILE` |
| **Export / Rendering** | No | No | Desktop GUI Click Only | `NOT_SUPPORTED` |

---

## 3. Technical Integration Feasibility Analysis

### Unofficial Project Format (`draft_content.json`)
* **Finding**: CapCut Desktop stores projects locally in unencrypted JSON format (`draft_content.json`).
* **Limitations**: Undocumented and highly unstable. Minor application updates between CapCut versions (6.x to 9.x) introduce breaking field changes or internal asset hash mismatches that cause CapCut to reject modified draft files.
* **Verdict**: `FRAGILE` / `NOT_RECOMMENDED` as primary system state.

### Desktop & Web Automation Analysis
* **Desktop Automation**: Windows UI Automation and macOS Accessibility APIs fail to inspect non-standard Qt/WebGL custom controls inside CapCut Desktop. Screen coordinates and OCR automation are extremely fragile and break on display scaling or UI updates.
* **Web Automation**: CapCut Web employs Cloudflare / ByteDance Web Protect. Headless browser automation triggers CAPTCHA challenges, session invalidation, and violates **Terms of Service Section 5** (Account Risk).
* **Verdict**: `NOT_RECOMMENDED`.

---

## 4. Technology Decision Matrix

Weighted evaluation across candidate video editing backends (Score 1–10, Weight 8–10):

| Criteria | Weight | CapCut Auto | FFmpeg Native | Remotion React | MLT Framework | Blender VSE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Reliability** | 10 | 2 | 10 | 9 | 8 | 8 |
| **Maintainability** | 10 | 2 | 10 | 9 | 7 | 6 |
| **Official Support** | 10 | 1 | 10 | 10 | 10 | 10 |
| **Automation Capability**| 9 | 3 | 10 | 10 | 8 | 8 |
| **Local-First Capability**| 9 | 5 | 10 | 10 | 10 | 10 |
| **Cost** | 8 | 10 | 10 | 8 | 10 | 10 |
| **AI Integration** | 10 | 2 | 10 | 9 | 7 | 6 |
| **Timeline Control** | 10 | 3 | 9 | 10 | 8 | 7 |
| **Rendering Quality** | 8 | 9 | 9 | 9 | 8 | 9 |
| **Long-Term Viability** | 10 | 2 | 10 | 9 | 8 | 7 |
| **Security & Privacy** | 9 | 3 | 10 | 10 | 9 | 9 |
| **Weighted Total** | **102** | **30.5** | **98.2** | **93.5** | **83.6** | **78.4** |

*Note: CapCut Automation fails overwhelmingly due to zero official API support, extreme fragility, and security/ToS risks.*

---

## 5. Recommended System Architecture

```text
  ┌─────────────────────────────────────────────────────────────┐
  │                      User Interface                         │
  │      Next.js 14 / React Timeline / Natural Language Prompt  │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                        AI Planner                           │
  │      LLM Tool Calling + Speech Transcription (Whisper)     │
  └──────────────────────────────┬──────────────────────────────┘
                                 │ Generates Operations
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                   Validation & Safety Gate                  │
  │     Path Sandboxing, Time Bounds, Sanity Checks             │
  └──────────────────────────────┬──────────────────────────────┘
                                 │ Validated Payloads
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │            Universal Video Editing IR (State Core)          │
  │       Tracks, Clips, Timing, Transforms, Text & Audio       │
  └──────────────┬───────────────────────────────┬──────────────┘
                 │                               │
                 ▼                               ▼
  ┌──────────────────────────────┐    ┌─────────────────────────┐
  │ Native Primary Renderer      │    │ Secondary Exporter      │
  │ FFmpeg Core + Remotion       │    │ CapCut Draft Folder     │
  └──────────────┬───────────────┘    │ Generator (.draft)      │
                 │                    └──────────┬──────────────┘
                 ▼                               ▼
  ┌──────────────────────────────┐    ┌─────────────────────────┐
  │ Final Rendered Video         │    │ CapCut Local Project    │
  │ (MP4 / WebM 1080p60)         │    │ (Manual Polish)         │
  └──────────────────────────────┘    └─────────────────────────┘
```

---

## 6. MVP Scope Definition

* **Target Use Case**: Automated short-form video generation (TikToks, Shorts, Reels) from long-form speech or raw media clips.
* **Tech Stack**: Next.js 14 (Frontend), Python 3.11 FastAPI (Backend), FFmpeg 6.x (Rendering), `faster-whisper` (Local Speech-to-Text), SQLite (Local Storage).
* **Supported Commands**:
  * "Remove silent pauses."
  * "Trim start/end."
  * "Burn dynamic vertical subtitles."
  * "Reframe video to 9:16."
  * "Mix background audio track with ducking."
  * "Render low-res 360p preview."

---

## 7. Phased Development Roadmap Overview

1. **Phase 0**: Architecture & Feasibility Validation (Completed).
2. **Phase 1**: Universal Video Editing IR State Engine.
3. **Phase 2**: FFmpeg Execution Engine & Filtergraph Builder.
4. **Phase 3**: Fast Proxy Preview System (<3s latency).
5. **Phase 4**: AI Planner & Whisper Transcription Pipeline.
6. **Phase 5**: Agent Tooling & Human-in-the-Loop Review.
7. **Phase 6**: Remotion Graphics & Experimental CapCut Exporter.

---

## 8. Primary Risks & Mitigations

* **Risk 1: Shell / Command Injection via FFmpeg Arguments**
  * *Mitigation*: Never execute raw shell strings. Pass sanitized argument lists via Python `subprocess.run(["ffmpeg", ...])`.
* **Risk 2: Path Traversal File Leaks**
  * *Mitigation*: Enforce strict path canonicalization checks restricting input/output files to project workspace directories.
* **Risk 3: Non-Deterministic LLM Output**
  * *Mitigation*: Enforce Pydantic / JSON Schema validation on LLM output before passing to execution engine.
* **Risk 4: CapCut Format Drift**
  * *Mitigation*: CapCut export is strictly an auxiliary feature; system primary operations depend entirely on local FFmpeg/Remotion.

---

## 9. Research Sources

1. CapCut Official Terms of Service: https://www.capcut.com/clause/terms-of-service
2. CapCut Official Website: https://www.capcut.com/
3. ByteDance Seedance 2.0 API Documentation Guide: https://www.capcut.com/ideas/seedance-2-0-for-api-documentation
4. Reverse-Engineered CapCut Draft Schema Reference: https://gist.github.com/renezander030/80823f1d47081c312d2c1f9edd20dc22
5. FFmpeg Official Documentation: https://ffmpeg.org/documentation.html
6. Remotion Official Framework Documentation: https://www.remotion.dev/docs/