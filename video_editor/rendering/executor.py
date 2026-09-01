"""Subprocess Process Executor without shell=True."""

import time
import subprocess
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

from video_editor.rendering.command import FFmpegCommand
from video_editor.rendering.exceptions import (
    ExecutableNotFoundError,
    RenderExecutionError,
    RenderTimeoutError,
)


class ProcessResult(BaseModel):
    """Structured result of process execution."""

    model_config = ConfigDict(extra="ignore")

    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    command: List[str] = Field(default_factory=list)


class ProcessExecutor:
    """Safe execution engine for process argument arrays."""

    def __init__(self, default_timeout: float = 60.0) -> None:
        self.default_timeout = default_timeout

    def execute(
        self, command: FFmpegCommand | List[str], timeout: Optional[float] = None
    ) -> ProcessResult:
        """Execute command argument array without shell=True."""
        cmd_list = command.to_cmd_list() if isinstance(command, FFmpegCommand) else list(command)
        if not cmd_list:
            raise ValueError("Cannot execute empty command list")

        effective_timeout = timeout if timeout is not None else self.default_timeout
        start_time = time.perf_counter()

        try:
            res = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                check=False,
            )
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            return ProcessResult(
                success=(res.returncode == 0),
                exit_code=res.returncode,
                stdout=res.stdout or "",
                stderr=res.stderr or "",
                duration_ms=duration_ms,
                timed_out=False,
                command=cmd_list,
            )
        except FileNotFoundError as e:
            raise ExecutableNotFoundError(
                f"Executable binary '{cmd_list[0]}' not found in system PATH",
                {"executable": cmd_list[0], "command": cmd_list},
            ) from e
        except subprocess.TimeoutExpired as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            stdout_str = e.stdout.decode("utf-8") if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr_str = e.stderr.decode("utf-8") if isinstance(e.stderr, bytes) else (e.stderr or "")
            raise RenderTimeoutError(
                f"Process execution timed out after {effective_timeout} seconds",
                {
                    "command": cmd_list,
                    "timeout_sec": effective_timeout,
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                },
            ) from e
