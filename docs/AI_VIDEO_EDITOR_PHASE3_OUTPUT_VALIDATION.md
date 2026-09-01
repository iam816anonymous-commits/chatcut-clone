# Phase 3 Output Validation Specification

This document defines the post-render `ffprobe` verification rules.

---

## 1. Post-Render Verification Criteria

1. File existence on disk.
2. File size > 0 bytes.
3. `ffprobe` JSON parsing succeeds without error.
4. Video stream present (if project contains visual tracks).
5. Audio stream present (if project contains audio tracks).
6. Rendered duration matches project duration within 1.5s tolerance.
