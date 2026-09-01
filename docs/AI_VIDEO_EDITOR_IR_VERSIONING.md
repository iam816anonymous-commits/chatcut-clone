# AI Video Editor — Universal IR Versioning & Migration Strategy

## Executive Summary
This document establishes the Semantic Versioning (SemVer) policy, forward/backward compatibility guarantees, and schema migration pipeline for the Universal Video Editing Intermediate Representation (IR).

---

## 1. Semantic Versioning Specification
The IR includes an explicit string field: `version` (e.g., `"1.0.0"`).
* **MAJOR (1.x.x $\rightarrow$ 2.0.0)**: Breaking schema changes (e.g., field renames, type changes, structural restructuring) that require automated migration scripts.
* **MINOR (1.0.0 $\rightarrow$ 1.1.0)**: Backward-compatible additions (e.g., new optional fields, new effect types, new asset metadata keys).
* **PATCH (1.0.0 $\rightarrow$ 1.0.1)**: Backward-compatible bug fixes or docstring annotations in schema validation logic.

---

## 2. Backward & Forward Compatibility Rules
1. **Backward Compatibility**: Any future version `1.x.y` MUST deserialize valid `1.0.0` project JSON files without throwing errors. Missing new optional fields are automatically assigned default values by Pydantic field specifications.
2. **Forward Compatibility**: Readers targeting version `1.0.0` parsing a `1.1.0` document will ignore unknown keys (Pydantic `extra = "ignore"` or default field handling).
3. **Deprecated Fields**: Deprecated fields will emit a warning during validation but remain functional for at least one major version cycle before removal.

---

## 3. Schema Migration Architecture

When loading a project file with `version < CURRENT_VERSION`, the system invokes a migration pipeline before schema validation:

```text
Loaded JSON File (version = "1.0.0")
         │
         ▼
 ┌──────────────────────┐
 │ Migration Registry   │ ◄── Identifies required migration path (1.0.0 -> 1.1.0 -> 2.0.0)
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Execute Migration    │ ◄── Transforms raw dict payload deterministically
 │ Functions            │
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ Pydantic Validation  │ ◄── Instantiates strongly-typed VideoProject
 └──────────────────────┘
```

---

## 4. Deprecation & Removal Lifecycle
* **Phase 1 (Announce)**: Field marked deprecated in `UNIVERSAL_VIDEO_EDITING_IR_SPEC_V1.md`.
* **Phase 2 (Warn)**: Runtime deprecation warnings logged on project import.
* **Phase 3 (Remove)**: Field dropped in next MAJOR version update (`2.0.0`). Migration function handles translation.