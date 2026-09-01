# AI Video Editor Practical MVP Plan

## Executive Summary
The MVP (Minimum Viable Product) is designed as a lean, local-first, highly reliable AI-assisted video editing application. It avoids complex NLE GUI development and fragile third-party automation in favor of automated short-form video creation (TikToks, Shorts, Reels) driven by natural language instructions.

---

## Technical Stack Selection

| Component | Technology Choice | Architectural Justification |
| :--- | :--- | :--- |
| **Frontend UI** | Next.js 14 / React / TypeScript / Tailwind CSS | Fast component development, interactive timeline UI, HTML5 video scrubbing. |
| **Backend API** | Python 3.11 / FastAPI | Native integration with AI/ML tools (Whisper, PyTorch, OpenCV) and async job queues. |
| **Video Engine** | FFmpeg 6.x (via `ffmpeg-python`) | High performance, cross-platform, zero licensing cost, completely offline. |
| **Speech & Audio** | `faster-whisper` (CTranslate2) | Extremely fast local speech-to-text with word-level timestamping. |
| **AI Agent Logic** | Pydantic / OpenAI / Ollama Structured Outputs | Guarantees 100% deterministic JSON operation payloads matching the IR schema. |
| **Database / State** | SQLite + Prisma ORM | Zero-config, single-file local database for media assets, projects, and render logs. |
| **Task Queue** | Python `asyncio` / Celery (Redis) | Handles non-blocking background video processing and encoding workers. |

---

## Core Capabilities (MVP Scope)

### Supported Inputs
* **Video Formats**: MP4, MOV, WebM (H.264 / AAC).
* **Audio Formats**: MP3, WAV, M4A.
* **Image Formats**: PNG, JPG, WebP.

### Core Atomic Editing Operations
1. **Trim / Cut**: In-point and out-point slicing.
2. **Split**: Slicing single clips into multiple segments.
3. **Merge / Concatenate**: Joining clips seamlessly.
4. **Remove Silence**: Automated silence detection and cut out using audio RMS energy analysis.
5. **Text & Captions**: Burning vertical auto-subtitles with custom fonts, colors, and word highlights.
6. **Audio Mixing**: Background music ducking and volume adjustment ($0–200\%$).
7. **Speed Adjustment**: Time-stretching video/audio ($0.5\times$ to $2.0\times$).
8. **Crop & Aspect Ratio**: 16:9 to 9:16 vertical re-framing.
9. **Low-Res Fast Preview**: Fast 360p draft rendering (<3 seconds generation time).
10. **Final Export**: Full-resolution 1080p60 H.264 rendering.

---

## Agent Tool Definitions

The AI Assistant interacts with the video engine through defined, typed functions:

```python
# 1. Inspect Media Asset Metadata
inspect_media(asset_id: str) -> MediaMetadata

# 2. Extract Speech Transcript with Word Timestamps
get_transcript(asset_id: str) -> TranscriptResult

# 3. Apply Silence Trimming
remove_silence(track_id: str, threshold_db: float = -30.0, min_duration: float = 0.4) -> IRState

# 4. Trim Clip Bounds
trim_clip(clip_id: str, source_start: float, source_end: float) -> IRState

# 5. Add Auto-Captions
add_subtitles(track_id: str, font_name: str, font_size: int, font_color: str) -> IRState

# 6. Add Background Audio Track
add_audio_track(asset_id: str, volume: float = 0.2, loop: bool = True) -> IRState

# 7. Render Low-Res Preview Clip
render_preview(project_id: str, start_time: float, end_time: float) -> PreviewURL

# 8. Export Final Video
export_video(project_id: str, resolution: str = "1080p", preset: str = "medium") -> ExportJobResult
```

---

## User Workflow Example

1. **Upload**: User uploads `interview.mp4` (2-minute talk).
2. **Natural Language Command**: User enters: *"Remove all silent pauses, add dynamic yellow subtitles, reframe to 9:16 vertical, and give me a 30-second preview."*
3. **Agent Action Sequence**:
   * Agent calls `get_transcript('interview.mp4')`.
   * Agent calls `remove_silence(...)`.
   * Agent applies 9:16 crop transform (`x_center`, `scale`).
   * Agent calls `add_subtitles(...)` with yellow font styling.
   * Agent calls `render_preview(...)`.
4. **User Review**: User watches 30s draft in the web player, approves, and clicks **Export Final Video**.
5. **Render Output**: Background worker outputs `interview_short_1080p.mp4`.