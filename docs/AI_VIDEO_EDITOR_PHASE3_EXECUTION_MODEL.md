# Phase 3 Execution Domain Model Specification

This document specifies the execution lifecycle models and state transitions for real video rendering jobs.

---

## 1. Execution Lifecycle States (`RenderExecutionStatus`)

* `PENDING`: Initial state before execution starts.
* `PREPARING`: Workspace creation and FFmpeg binary/argument preparation.
* `RUNNING`: Subprocess active; stdout `-progress` streaming realtime progress.
* `VALIDATING`: Subprocess completed; `ffprobe` validating `.partial` output.
* `COMPLETED`: Output validated and atomically published to target path.
* `FAILED`: Execution or validation failed; partial output cleaned up.
* `CANCELLED`: Execution cancelled by caller; process killed.
* `TIMED_OUT`: Execution exceeded configurable timeout limit; process killed.
