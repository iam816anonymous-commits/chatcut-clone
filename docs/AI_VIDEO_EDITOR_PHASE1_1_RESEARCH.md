# AI Video Editor Phase 1.1 — Research & Engineering Foundations

## Executive Summary
This document investigates the engineering concepts required to achieve deterministic reliability in Phase 1.1, focusing on transactional copy-on-write state updates, linear history branching, deep-copy immutability, microsecond timing rules, and serialization version enforcement.

---

## 1. Transactional State Updates & Rollback Semantics

To guarantee that invalid editing operations never leave the system in a partially mutated state, the engine relies on **Copy-on-Write Isolation**:

```text
       Current State (Project S_A)
                  │
                  ▼
         Create Deep Copy (Draft S_Draft)
                  │
                  ▼
         Apply Operation Mutations
                  │
                  ▼
       Validate Project Integrity
                  │
       ┌──────────┴──────────┐
       ▼                     ▼
[VALIDATION PASSED]   [VALIDATION FAILED]
       │                     │
  Commit S_Draft        Discard S_Draft
  as New State S_B      Raise Domain Exception
  Record in History     State & History Unchanged
```

### Key Invariant
If `StateManager.apply_operation(op)` raises any domain exception (`InvalidTimeRangeError`, `TrackLockedError`, `ClipOverlapError`), the operation is discarded, `project` remains at $S_A$, and `HistoryManager` records zero new states or operation log entries.

---

## 2. Linear Undo/Redo History & Redo Invalidation

A linear history stack model is selected over a complex DAG (Directed Acyclic Graph) tree:
* `past_states`: List of previous project state snapshots.
* `current_state`: Current active project state snapshot.
* `future_states`: List of undone states available for Redo.

### Redo Invalidation Rule
When a user performs a **new operation** after one or more `undo()` actions, `future_states` MUST be cleared immediately.

```text
Initial Stack:      A -> B -> C
Undo twice:         A  (Current) | Redo Stack: [B, C]
Apply Operation D:  A -> D       | Redo Stack: [] (B and C discarded)
```

Attempting to call `redo()` when `future_states` is empty raises a `HistoryError` without modifying `current_state`.

---

## 3. Immutability & Deep-Copy Isolation

Pydantic v2's `.model_copy(deep=True)` performs a recursive deep copy of all fields, including nested dictionaries (`assets`), lists (`tracks`, `clips`, `effects`), and child model objects (`Transform`, `AudioConfig`, `TextStyle`).

### Verification Strategy
1. Obtain state snapshot $S_A$.
2. Apply operation to produce $S_B$.
3. Mutate nested clip or transform in $S_B$.
4. Assert that $S_A$'s corresponding nested objects remain strictly equal to their original values.

---

## 4. Canonical Microsecond Time & Invariants

* All canonical time offsets and durations are integer microseconds (`int`).
* **Conversion Boundary**: Floating-point seconds (e.g., `1.5s`) are converted at the API boundary via `round(seconds * 1_000_000)` into integer microseconds (`1_500_000 us`).
* **Invariants**:
  * `timeline_start_us >= 0`
  * `timeline_duration_us > 0`
  * `source_start_us >= 0`
  * `source_duration_us > 0`
  * `source_start_us + source_duration_us <= asset.duration_us` (if `asset_id` referenced).

---

## 5. Serialization & IR Schema Version Invariants

* **Canonical Version**: `"1.0.0"`.
* **Version Policy**: Major version mismatches (e.g., `"2.0.0"`) are rejected during validation with `ProjectIntegrityError` to prevent silent corruption from un-migrated schemas.
* **Roundtrip Invariant**: `VideoProject.model_validate_json(project.model_dump_json()) == project`.