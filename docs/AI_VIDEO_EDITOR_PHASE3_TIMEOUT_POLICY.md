# Phase 3 Timeout, Cancellation & Failure Model Specifications

## Timeout Policy
FFmpeg processes exceeding configurable timeouts (default 300s) are forcefully terminated via SIGKILL, setting execution status to `TIMED_OUT` and cleaning partial output files.

## Cancellation Policy
Callers pass `cancellation_check` callbacks. When `cancellation_check()` returns `True`, process terminates immediately, setting status to `CANCELLED` and removing partial files.

## Failure Model
All subprocess and validation errors raise structured domain exceptions (`FFmpegNotAvailableError`, `FFmpegExecutionError`, `OutputValidationError`, `ArtifactPublishingError`). Raw subprocess exceptions are never exposed to callers.

## Testing Strategy
Synthetic test assets generated using lavfi sources enable unit and end-to-end integration tests without committing binary files. Integration tests skip cleanly if FFmpeg binaries are missing.

## Limitations
Realtime performance and GPU hardware acceleration depend on host system capabilities. Local execution is single-node.

## Execution Metrics
Captures total execution duration in seconds, average encoding FPS, and encoding speed multipliers.
