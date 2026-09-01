# AI Video Editor Phase 2A — Technical Research & Engineering Foundations

## Executive Summary
This document establishes the technical research foundation for Phase 2A, investigating FFprobe metadata extraction, safe subprocess process execution without `shell=True`, error classification, rational frame rate parsing, duration reliability, path security, determinism, and renderer boundaries.

---

## 1. FFprobe Metadata Extraction & Command Structure
To safely extract media container and stream metadata without shell interpretation, FFprobe is executed via argument arrays requesting JSON output:

```python
cmd = [
    "ffprobe",
    "-v", "error",
    "-show_format",
    "-show_streams",
    "-of", "json",
    input_path
]
```

### Parsing Policy
* `-v error`: Suppresses verbose banner text so stdout contains strictly valid JSON.
* `-show_format`: Returns container-level details (`format_name`, `duration`, `size`, `bit_rate`).
* `-show_streams`: Returns stream-level details (`codec_type`, `codec_name`, `width`, `height`, `r_frame_rate`, `avg_frame_rate`, `sample_rate`, `channels`, `pix_fmt`).

---

## 2. Process Execution & Security Rules
All subprocess invocations (`ffmpeg` and `ffprobe`) strictly observe these security rules:

1. **NO `shell=True`**: Commands must always be executed as argument arrays (`List[str]`), e.g., `["ffmpeg", "-i", input_path, ...]`.
2. **NO String Interpolation**: Commands are never constructed via string formatting or shell string concatenations (`f"ffmpeg -i {path}"` is strictly forbidden).
3. **Controlled Arguments**: Executable names and input/output path strings are validated before process invocation.
4. **Timeout Enforcement**: Process execution includes an explicit timeout parameter (e.g., `timeout=30.0` seconds) to prevent infinite hangs.
5. **Output Capture**: `stdout` and `stderr` are captured in memory as decoded UTF-8 strings.

---

## 3. Structured Error Classification

Rather than relying on brittle regex matching on `stderr`, failures are categorized into explicit domain exceptions:

| Error Category | Domain Exception | Primary Trigger Condition |
| :--- | :--- | :--- |
| **FFmpeg/FFprobe Missing** | `ExecutableNotFoundError` | Binary executable not found in system `PATH`. |
| **Input File Missing/Invalid** | `InputFileNotFoundError` | Source media file path does not exist or is a directory. |
| **Invalid/Corrupted Media** | `InvalidMediaError` | FFprobe returns non-zero exit code or malformed JSON. |
| **Render Execution Error** | `RenderExecutionError` | FFmpeg exits with non-zero exit code. |
| **Render Timeout** | `RenderTimeoutError` | Process execution exceeds specified timeout threshold. |
| **Output Path Failure** | `OutputValidationError` | Output path attempts to overwrite input, or output missing after successful exit code. |

---

## 4. Rational Frame Rate Parsing

FFprobe reports frame rates as fractional strings, e.g.:
* `"30000/1001"` $\rightarrow 29.97002997...$ FPS ($33,366,666 / 1,000 = 33,366.666\ \mu\text{s per frame}$).
* `"60000/1001"` $\rightarrow 59.94005994...$ FPS.
* `"24/1"` $\rightarrow 24.0$ FPS.
* `"25/1"` $\rightarrow 25.0$ FPS.

### Parser Function (`parse_rational_fps`)
```python
def parse_rational_fps(fps_str: str) -> float:
    if not fps_str or fps_str == "0/0":
        return 30.0  # Fallback
    if "/" in fps_str:
        num, den = fps_str.split("/")
        n, d = float(num), float(den)
        if d == 0:
            return 30.0
        return n / d
    return float(fps_str)
```

---

## 5. Duration Reliability Hierarchy

Container duration vs stream duration vs missing duration:
1. **Primary**: Container `format.duration` (in seconds). Convert to microseconds via `round(float(sec) * 1_000_000)`.
2. **Secondary**: First video/audio stream `stream.duration`.
3. **Fallback**: `None` (for static image files or un-timed raw streams).

---

## 6. Path Security & Output Policy
* **Canonicalization**: Source and target paths are resolved via `os.path.abspath(os.path.realpath(path))`.
* **Overwrite Prevention**: `output_path` must never equal `input_path` (`InputOverwriteError`).
* **Directory Check**: `output_path` cannot be an existing directory. Parent directory must exist or be created automatically.
* **Output Existence Gate**: After FFmpeg process completion, the executor verifies that `output_path` exists on disk and has `size > 0`.

---

## 7. Command Determinism & Renderer Boundary

* **Stable Argument Ordering**: Options are appended in fixed sequence: `["ffmpeg", "-y", "-ss", start, "-i", input, "-t", duration, "-vf", filter, "-c:v", codec, output]`.
* **Renderer Boundary**: The `VideoProject` Universal IR remains 100% pure and independent of FFmpeg commands. Rendering adapters translate IR clips or assets into `FFmpegCommand` objects without mutating project state.