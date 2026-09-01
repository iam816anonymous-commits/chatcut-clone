# AI Video Editor Phase 1 — Module Architecture & Data Flow

## Executive Summary
This document outlines the Python package structure, class relationships, and event-driven data flow implemented in Phase 1 for the AI Video Editing System.

---

## 1. System Package Hierarchy

```text
video_editor/
├── __init__.py
├── ir/
│   ├── __init__.py
│   ├── time.py           # Canonical TimelineTime microsecond precision abstraction
│   ├── enums.py          # Domain Enums (AssetType, TrackType, OperationType, AspectRatio)
│   ├── models.py         # Pydantic v2 schemas (VideoProject, ProjectSettings, Asset, Track, Clip, etc.)
│   ├── exceptions.py     # Domain-specific exception hierarchy
│   ├── operations.py     # Typed, serializable atomic operation payloads
│   └── validation.py     # Business logic validation gate & project integrity checker
└── engine/
    ├── __init__.py
    ├── history.py        # Undo/Redo stack manager and operation history trail
    └── state_manager.py  # Transactional copy-on-write state engine
```

---

## 2. Component Class Diagram

```text
               ┌───────────────────────────────┐
               │         VideoProject          │
               │  - id: UUID                   │
               │  - name: str                  │
               │  - settings: ProjectSettings  │
               │  - assets: Dict[str, Asset]   │
               │  - tracks: List[Track]        │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │             Track             │
               │  - id: UUID                   │
               │  - name: str                  │
               │  - type: TrackType            │
               │  - index: int                 │
               │  - muted / locked: bool       │
               │  - clips: List[Clip]          │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │             Clip              │
               │  - id: UUID                   │
               │  - asset_id: Optional[str]    │
               │  - timeline_start_us: int     │
               │  - timeline_duration_us: int  │
               │  - source_start_us: int       │
               │  - source_duration_us: int    │
               │  - transform: Transform       │
               │  - audio: AudioConfig         │
               └───────────────────────────────┘
```

---

## 3. Transactional Operation Data Flow

```text
Operation Payload
   (e.g. TRIM_CLIP)
         │
         ▼
 ┌───────────────┐
 │ StateManager  │ ◄── Creates deep copy of current VideoProject
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │  Validation   │ ◄── Evaluates integrity (Time bounds, asset reference, locked tracks)
 │     Gate      │
 └───────┬───────┘
         │
  ┌──────┴──────┐
  │ Valid?      │
  └──────┬──────┘
         ├───────────────────────────────┐
      YES│                             NO│ Throws Domain Exception
         ▼                               ▼ (e.g. InvalidTimeRangeError)
 ┌───────────────┐               ┌───────────────┐
 │ Apply Edit to │               │ Revert Copy / │
 │  Copied State │               │ Keep Original │
 └───────┬───────┘               └───────────────┘
         │
         ▼
 ┌───────────────┐
 │ Commit State  │ ──► Update Current Project Reference
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │ Record Stack  │ ──► Append to HistoryManager (Clears Redo Stack)
 └───────────────┘
```

---

## 4. Key Architectural Guarantees
1. **Purity**: Domain models in `video_editor.ir.models` contain pure data structures and schema validation without side effects or disk I/O.
2. **Determinism**: Applying operation $O$ to state $S_A$ always results in state $S_B$.
3. **Immutability Safety**: State transitions occur via transactional copies (`model_copy(deep=True)`), guaranteeing that raised exceptions leave previous project state completely unpolluted.
4. **Serialization Parity**: Every `VideoProject` produces a JSON dictionary via `.model_dump_json()` and reconstructs an identical project instance via `.model_validate_json()`.