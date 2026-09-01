"""Typed Pydantic v2 Media Metadata Domain Models."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class MediaType(str, Enum):
    """Media container type classification."""

    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    IMAGE = "IMAGE"
    UNKNOWN = "UNKNOWN"


class VideoStreamMetadata(BaseModel):
    """Inspected video stream metadata."""

    model_config = ConfigDict(extra="ignore")

    index: int = Field(..., ge=0, description="Stream index in container")
    codec_name: str = Field(..., description="Video codec name (e.g. h264, hevc, vp9)")
    codec_long_name: Optional[str] = Field(default=None)
    width: int = Field(..., ge=1, description="Frame width in pixels")
    height: int = Field(..., ge=1, description="Frame height in pixels")
    fps: float = Field(..., gt=0.0, description="Parsed frame rate")
    r_frame_rate: str = Field(..., description="Raw rational frame rate string (e.g. 30000/1001)")
    avg_frame_rate: str = Field(..., description="Raw average frame rate string")
    pix_fmt: Optional[str] = Field(default=None, description="Pixel format (e.g. yuv420p)")
    duration_us: Optional[int] = Field(default=None, ge=0, description="Stream duration in microseconds")
    bit_rate: Optional[int] = Field(default=None, ge=0, description="Stream bit rate in bps")


class AudioStreamMetadata(BaseModel):
    """Inspected audio stream metadata."""

    model_config = ConfigDict(extra="ignore")

    index: int = Field(..., ge=0, description="Stream index in container")
    codec_name: str = Field(..., description="Audio codec name (e.g. aac, mp3, flac)")
    codec_long_name: Optional[str] = Field(default=None)
    sample_rate: int = Field(..., ge=1, description="Audio sample rate in Hz (e.g. 44100, 48000)")
    channels: int = Field(..., ge=1, description="Number of audio channels")
    channel_layout: Optional[str] = Field(default=None, description="Layout label (e.g. stereo, 5.1)")
    duration_us: Optional[int] = Field(default=None, ge=0, description="Stream duration in microseconds")
    bit_rate: Optional[int] = Field(default=None, ge=0, description="Stream bit rate in bps")


class ContainerMetadata(BaseModel):
    """Container format metadata."""

    model_config = ConfigDict(extra="ignore")

    format_name: str = Field(..., description="Container format string (e.g. mov,mp4,m4a,3gp,3g2,mj2)")
    format_long_name: Optional[str] = Field(default=None)
    duration_us: Optional[int] = Field(default=None, ge=0, description="Container duration in microseconds")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    bit_rate: Optional[int] = Field(default=None, ge=0, description="Total container bit rate in bps")


class MediaMetadata(BaseModel):
    """Root aggregated inspected media file metadata."""

    model_config = ConfigDict(extra="ignore")

    file_path: str = Field(..., description="Absolute canonical file path")
    media_type: MediaType = Field(..., description="Derived media type classification")
    container: ContainerMetadata = Field(..., description="Container format metadata")
    video_streams: List[VideoStreamMetadata] = Field(default_factory=list)
    audio_streams: List[AudioStreamMetadata] = Field(default_factory=list)
    raw_probe: Dict[str, Any] = Field(default_factory=dict, description="Raw FFprobe JSON dictionary")

    @property
    def primary_video_stream(self) -> Optional[VideoStreamMetadata]:
        """Get primary (first) video stream if present."""
        return self.video_streams[0] if self.video_streams else None

    @property
    def primary_audio_stream(self) -> Optional[AudioStreamMetadata]:
        """Get primary (first) audio stream if present."""
        return self.audio_streams[0] if self.audio_streams else None

    @property
    def duration_us(self) -> Optional[int]:
        """Get reliable media duration in microseconds with container/stream fallbacks."""
        if self.container.duration_us is not None:
            return self.container.duration_us
        if self.primary_video_stream and self.primary_video_stream.duration_us is not None:
            return self.primary_video_stream.duration_us
        if self.primary_audio_stream and self.primary_audio_stream.duration_us is not None:
            return self.primary_audio_stream.duration_us
        return None
