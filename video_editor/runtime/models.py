"""Pydantic v2 Execution Domain Models for Phase 3 Rendering Runtime."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict


def generate_uuid() -> str:
    return str(uuid.uuid4())


class RenderExecutionStatus(str, Enum):
    """Execution status lifecycle states."""

    PENDING = "PENDING"
    PREPARING = "PREPARING"
    RUNNING = "RUNNING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class RenderProgress(BaseModel):
    """Realtime rendering progress metrics."""

    model_config = ConfigDict(extra="ignore")

    frame: int = Field(default=0, ge=0)
    fps: float = Field(default=0.0, ge=0.0)
    current_time_us: int = Field(default=0, ge=0)
    total_duration_us: int = Field(default=0, ge=0)
    speed: float = Field(default=0.0, ge=0.0)
    percent: float = Field(default=0.0, ge=0.0, le=100.0)


class RenderArtifact(BaseModel):
    """Published output video file artifact."""

    model_config = ConfigDict(extra="ignore")

    artifact_id: str = Field(default_factory=generate_uuid)
    execution_id: str = Field(...)
    path: str = Field(...)
    file_size_bytes: int = Field(..., ge=0)
    duration_us: int = Field(..., ge=0)
    video_streams: int = Field(default=1, ge=0)
    audio_streams: int = Field(default=0, ge=0)
    sha256_checksum: str = Field(...)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ExecutionMetrics(BaseModel):
    """Performance and execution metrics."""

    model_config = ConfigDict(extra="ignore")

    execution_duration_sec: float = Field(default=0.0, ge=0.0)
    peak_memory_mb: Optional[float] = Field(default=None)
    avg_fps: float = Field(default=0.0, ge=0.0)
    encoding_speed_multiplier: float = Field(default=0.0, ge=0.0)


class RenderExecution(BaseModel):
    """Complete execution record for a render job."""

    model_config = ConfigDict(extra="ignore")

    execution_id: str = Field(default_factory=generate_uuid)
    render_plan_id: str = Field(...)
    project_id: str = Field(...)
    status: RenderExecutionStatus = Field(default=RenderExecutionStatus.PENDING)
    workspace_dir: str = Field(...)
    partial_output_path: str = Field(...)
    final_output_path: str = Field(...)
    start_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = Field(default=None)
    progress: RenderProgress = Field(default_factory=RenderProgress)
    artifact: Optional[RenderArtifact] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)
