# Phase 3 Safe Process Runtime Specification

This document specifies the subprocess execution rules and safety policies enforced during rendering.

---

## 1. Subprocess Safety Rules

1. **Explicit Argument Lists:** All FFmpeg command invocations pass arguments directly as `List[str]`.
2. **Strict Prohibiton of `shell=True`:** Subprocess execution NEVER uses `shell=True` to prevent command injection.
3. **Pipe Progress Monitoring:** Commands include `-progress pipe:1` for realtime stdout key/value progress parsing.
4. **Log Redirection:** Subprocess stderr is redirected to `workspace/render.log` for offline debugging.
