"""FFmpeg Render Executor: Orchestrates real local rendering, progress monitoring, and atomic publication."""

import os
import shutil
import subprocess
import time
from typing import Callable, Optional
from video_editor.compiler.models import RenderPlan
from video_editor.compiler.planner import RenderPlanner
from video_editor.runtime.artifacts import ArtifactManager
from video_editor.runtime.environment import FFmpegEnvironmentInspector
from video_editor.runtime.errors import (
    FFmpegExecutionError,
    RenderCancelledError,
    RenderTimeoutError,
)
from video_editor.runtime.models import (
    ExecutionMetrics,
    RenderExecution,
    RenderExecutionStatus,
    RenderProgress,
)
from video_editor.runtime.progress import ProgressMonitor
from video_editor.runtime.validator import OutputValidator


class FFmpegRenderExecutor:
    """Orchestrates local FFmpeg execution, workspace management, progress callbacks, timeouts, and atomic publication."""

    def __init__(
        self,
        workspace_base_dir: str = "/tmp/video_editor_workspaces",
        timeout_sec: float = 300.0,
    ) -> None:
        self.workspace_base_dir = workspace_base_dir
        self.timeout_sec = timeout_sec

    def execute_render_plan(
        self,
        plan: RenderPlan,
        target_output_path: str,
        on_progress: Optional[Callable[[RenderProgress], None]] = None,
        cancellation_check: Optional[Callable[[], bool]] = None,
    ) -> RenderExecution:
        """Executes a compiled RenderPlan to produce a real output video file.

        Args:
            plan: Source compiled RenderPlan.
            target_output_path: Canonical target output path on disk (e.g., /tmp/final_render.mp4).
            on_progress: Optional progress callback function receiving RenderProgress models.
            cancellation_check: Optional function returning True if caller requests job cancellation.

        Returns:
            RenderExecution: Complete execution state model with published RenderArtifact on success.
        """
        # 1. Environment Verification
        env_status = FFmpegEnvironmentInspector.require_environment()

        # 2. Setup Execution Record & Workspace
        exec_id = f"exec_{int(time.time() * 1000)}"
        workspace_dir = os.path.join(self.workspace_base_dir, exec_id)
        os.makedirs(workspace_dir, exist_ok=True)

        partial_output_path = os.path.join(workspace_dir, "output.mp4.partial")
        log_file_path = os.path.join(workspace_dir, "render.log")

        execution = RenderExecution(
            execution_id=exec_id,
            render_plan_id=plan.plan_id,
            project_id=plan.project_id,
            status=RenderExecutionStatus.PREPARING,
            workspace_dir=workspace_dir,
            partial_output_path=partial_output_path,
            final_output_path=target_output_path,
        )

        # 3. Generate FFmpeg Command with Progress Pipe
        planner = RenderPlanner()
        cmd = planner.plan_to_command(plan, partial_output_path, ffmpeg_path=env_status.ffmpeg_path)

        # Build executable + arguments list
        arguments = cmd.to_cmd_list()
        arguments.insert(1, "-progress")
        arguments.insert(2, "pipe:1")

        start_time = time.time()
        execution.status = RenderExecutionStatus.RUNNING

        # 4. Execute Subprocess (Strictly without shell=True)
        progress_monitor = ProgressMonitor(
            total_duration_us=plan.total_duration_us,
            on_progress_callback=on_progress,
        )

        process = None
        try:
            with open(log_file_path, "w") as log_f:
                process = subprocess.Popen(
                    arguments,
                    stdout=subprocess.PIPE,
                    stderr=log_f,
                    text=True,
                    bufsize=1,
                )

                while True:
                    # Check Cancellation
                    if cancellation_check and cancellation_check():
                        process.kill()
                        process.wait()
                        execution.status = RenderExecutionStatus.CANCELLED
                        execution.error_message = "Execution cancelled by caller"
                        self._cleanup_partial(partial_output_path)
                        return execution

                    # Check Timeout
                    elapsed = time.time() - start_time
                    if elapsed > self.timeout_sec:
                        process.kill()
                        process.wait()
                        execution.status = RenderExecutionStatus.TIMED_OUT
                        execution.error_message = f"Execution timed out after {elapsed:.1f}s"
                        self._cleanup_partial(partial_output_path)
                        return execution

                    line = process.stdout.readline() if process.stdout else ""
                    if not line and process.poll() is not None:
                        break

                    if line:
                        progress_monitor.parse_line(line)

                return_code = process.wait()
                if return_code != 0:
                    execution.status = RenderExecutionStatus.FAILED
                    execution.error_message = f"FFmpeg exited with non-zero code {return_code}"
                    self._cleanup_partial(partial_output_path)
                    return execution

        except Exception as e:
            if process:
                process.kill()
            execution.status = RenderExecutionStatus.FAILED
            execution.error_message = f"Execution exception: {e}"
            self._cleanup_partial(partial_output_path)
            return execution

        # 5. Output Validation Gate
        execution.status = RenderExecutionStatus.VALIDATING
        try:
            metadata = OutputValidator.validate_rendered_output(
                partial_output_path,
                expected_duration_us=plan.total_duration_us,
                tolerance_sec=1.5,
            )
        except Exception as e:
            execution.status = RenderExecutionStatus.FAILED
            execution.error_message = f"Post-render validation failed: {e}"
            self._cleanup_partial(partial_output_path)
            return execution

        # 6. Atomic Publishing
        try:
            artifact = ArtifactManager.publish_artifact(
                execution_id=exec_id,
                partial_path=partial_output_path,
                final_path=target_output_path,
                metadata=metadata,
            )
            execution.artifact = artifact
            execution.status = RenderExecutionStatus.COMPLETED
            execution.progress = progress_monitor.current_progress
            execution.end_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            total_duration = time.time() - start_time
            execution.metrics = ExecutionMetrics(
                execution_duration_sec=total_duration,
                encoding_speed_multiplier=progress_monitor.current_progress.speed,
            )
            return execution
        except Exception as e:
            execution.status = RenderExecutionStatus.FAILED
            execution.error_message = f"Artifact publishing failed: {e}"
            self._cleanup_partial(partial_output_path)
            return execution

    def _cleanup_partial(self, partial_path: str) -> None:
        if os.path.exists(partial_path):
            try:
                os.remove(partial_path)
            except Exception:
                pass
