"""Structured FFmpeg FilterGraph Abstraction and Deterministic Stream Label Allocator."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class LabelAllocator:
    """Deterministic stream label generator (v0, v1, a0, a1, outv, outa)."""

    def __init__(self) -> None:
        self._video_counter = 0
        self._audio_counter = 0

    def allocate_video(self, prefix: str = "v") -> str:
        label = f"{prefix}{self._video_counter}"
        self._video_counter += 1
        return label

    def allocate_audio(self, prefix: str = "a") -> str:
        label = f"{prefix}{self._audio_counter}"
        self._audio_counter += 1
        return label


class FilterNode(BaseModel):
    """Single node in an FFmpeg filtergraph."""

    model_config = ConfigDict(extra="ignore")

    inputs: List[str] = Field(default_factory=list, description="Input stream label tags e.g. ['0:v']")
    filter_name: str = Field(..., description="FFmpeg filter name e.g. trim, scale, concat")
    params: List[str] = Field(default_factory=list, description="Filter parameter list e.g. ['start=0', 'end=5']")
    outputs: List[str] = Field(default_factory=list, description="Output stream label tags e.g. ['v0']")

    def to_filter_spec(self) -> str:
        """Format node as an FFmpeg filter chain element string.

        Example: [0:v] trim=start=0:end=5, setpts=PTS-STARTPTS [v0]
        """
        in_str = "".join([f"[{i}]" for i in self.inputs])
        out_str = "".join([f"[{o}]" for i in self.outputs for o in (i if isinstance(i, list) else [i])])

        param_str = ":".join(self.params)
        filter_body = f"{self.filter_name}={param_str}" if param_str else self.filter_name

        return f"{in_str} {filter_body} {out_str}".strip()


class FilterGraph(BaseModel):
    """Container representing a complete multi-stream FFmpeg filter_complex graph."""

    model_config = ConfigDict(extra="ignore")

    nodes: List[FilterNode] = Field(default_factory=list)

    def add_node(
        self,
        inputs: List[str],
        filter_name: str,
        params: Optional[List[str]] = None,
        outputs: Optional[List[str]] = None,
    ) -> FilterNode:
        """Construct and append a FilterNode to graph."""
        node = FilterNode(
            inputs=inputs,
            filter_name=filter_name,
            params=params or [],
            outputs=outputs or [],
        )
        self.nodes.append(node)
        return node

    def to_filter_complex_string(self) -> str:
        """Build deterministic filter_complex argument string joining nodes with semicolons."""
        return ";\n".join([node.to_filter_spec() for node in self.nodes])
