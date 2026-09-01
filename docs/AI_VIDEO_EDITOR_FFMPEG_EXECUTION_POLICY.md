# AI Video Editor — FFmpeg Process Execution Policy

## Executive Summary
This document establishes the security, reliability, and process execution policy for invoking `ffmpeg` and `ffprobe` binaries in the AI Video Editing System.

---

## 1. Security & Process Rules

1. **Argument Arrays Only**: All binary executions must pass argument lists (`List[str]`).
2. **Strict Prohibition of `shell=True`**: Subprocess calls using `shell=True` or shell string concatenation are strictly forbidden.
3. **Executable Binary Isolation**: Executable names (`ffmpeg`, `ffprobe`) are resolved via `shutil.which` or explicit configured absolute paths.
4. **Path Canonicalization**: Input and output paths are resolved using `os.path.abspath(os.path.realpath(path))` before execution.
5. **Input-Output Overwrite Protection**: `output_path` is checked against `input_path` to prevent accidental source file destruction.

---

## 2. Process Execution Architecture

Process execution is encapsulated inside `ProcessExecutor`:

```python
class ProcessExecutor:
    def execute(self, command: FFmpegCommand | List[str], timeout: float) -> ProcessResult:
        # Executes subprocess.run(cmd_list, capture_output=True, text=True, timeout=timeout)
        ...
```

### Execution Properties
* **Timeout Gate**: Enforces process timeout limits (e.g., 60.0s) to prevent infinite process hangs.
* **Output Capture**: Stdout and stderr are captured and returned in structured `ProcessResult` objects.
* **Exit Code Handling**: Non-zero exit codes raise structured domain exceptions (`RenderExecutionError`) containing full stderr context.

---

## 3. Error Classification Matrix

| Trigger | Raised Exception | Exception Context |
| :--- | :--- | :--- |
| `ffmpeg`/`ffprobe` binary missing in PATH | `ExecutableNotFoundError` | Executable path |
| Input media file missing on disk | `InputFileNotFoundError` | Resolved input path |
| Exit code != 0 | `RenderExecutionError` | Command list, exit code, stderr |
| Timeout exceeded | `RenderTimeoutError` | Timeout duration, command list |
| Output path equals input path | `InputOverwriteError` | Input/Output paths |
| Output missing/empty post-render | `OutputValidationError` | Output path, size |