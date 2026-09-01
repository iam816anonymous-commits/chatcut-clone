# AI Video Editor — Phase 2B Rendering Semantics Specification

## Executive Summary
This document specifies the rendering semantics, audio/video synchronization policies, and normalization rules applied during timeline compilation and command generation.

---

## 1. Stream Normalization Rules

Before entering FFmpeg `concat` filter nodes, video and audio streams are normalized to guarantee codec/container compatibility:

1. **Video Normalization**:
   * `scale=W:H`: Scales all video frames to target canvas dimensions (e.g., 1080x1920).
   * `fps=FPS`: Normalizes frame rates to target canvas FPS (e.g., 30.0).
   * `-pix_fmt yuv420p`: Sets 8-bit YUV 4:2:0 pixel formatting for maximum H.264 playback compatibility.
2. **Audio Normalization**:
   * `aformat=sample_rates=48000:channel_layouts=stereo`: Normalizes audio stream sample rates to 48kHz stereo before concatenation.

---

## 2. Audio/Video Synchronization Policy
* Video and audio streams are processed in parallel filtergraph chains (`[outv]` and `[outa]`).
* Both video and audio gap nodes (`color` and `anullsrc`) use microsecond-exact duration parameters.
* Concat nodes join corresponding streams in identical timeline sequence order, ensuring lip-sync alignment throughout rendered output videos.