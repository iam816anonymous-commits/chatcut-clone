"""Structured Executable Command Model."""

from typing import List
from pydantic import BaseModel, Field, ConfigDict


class FFmpegCommand(BaseModel):
    """Structured representation of an argument-array FFmpeg command."""

    model_config = ConfigDict(extra="ignore")

    executable: str = Field(default="ffmpeg", description="Executable binary path or name")
    arguments: List[str] = Field(default_factory=list, description="Array of command argument strings")

    def to_cmd_list(self) -> List[str]:
        """Return complete argument array for safe subprocess execution without shell=True."""
        return [self.executable] + list(self.arguments)

    def to_display_string(self) -> str:
        """Return safe display string representation for debugging logs."""
        quoted_args = [f'"{a}"' if " " in a else a for a in self.to_cmd_list()]
        return " ".join(quoted_args)
