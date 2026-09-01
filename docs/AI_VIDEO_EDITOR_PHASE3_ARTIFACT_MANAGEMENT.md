# Phase 3 Artifact Management Specification

This document defines the atomic publication and checksum calculation workflow.

---

## 1. Atomic Publishing Workflow

1. Render output to `output.mp4.partial` in workspace.
2. Run `OutputValidator` on `output.mp4.partial`.
3. Execute atomic rename `os.replace("output.mp4.partial", "output.mp4")`.
4. Calculate SHA-256 digest of published artifact.
5. Create `RenderArtifact` record.
