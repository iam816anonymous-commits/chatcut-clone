# AI Video Editor — RenderPlan Schema & Domain Model Specification

## Executive Summary
This document specifies the Pydantic v2 schemas and JSON representation of the compiled `RenderPlan` model (`video_editor.compiler.models.RenderPlan`).

---

## 1. RenderPlan JSON Architecture

```json
{
  "plan_id": "8a3c8e41-0f4a-4b92-b6d3-2e45307b2211",
  "project_id": "f29d2b10-6c9a-4122-80f4-5b23114a8b00",
  "version": "1.0.0",
  "total_duration_us": 10000000,
  "output_settings": {
    "width": 1080,
    "height": 1920,
    "fps": 30.0,
    "video_codec": "libx264",
    "audio_codec": "aac",
    "audio_sample_rate": 48000,
    "audio_channels": 2
  },
  "inputs": [
    {
      "input_index": 0,
      "asset_id": "asset_video_01",
      "file_path": "/workspace/media/interview.mp4"
    }
  ],
  "tracks": [
    {
      "track_id": "track_v1",
      "track_type": "VIDEO",
      "index": 0,
      "items": [
        {
          "clip_id": "clip_v1",
          "asset_id": "asset_video_01",
          "input_index": 0,
          "timeline_start_us": 0,
          "timeline_duration_us": 5000000,
          "source_start_us": 0,
          "source_duration_us": 5000000,
          "speed": 1.0,
          "volume": 1.0
        },
        {
          "gap_id": "gap_g1",
          "timeline_start_us": 5000000,
          "timeline_duration_us": 2000000
        }
      ]
    }
  ]
}
```

---

## 2. Model Invariants
1. `inputs`: List of unique media files assigned zero-based sequential `input_index` integers.
2. `RenderSegment`: Represents trimmed media instances referencing `input_index`.
3. `RenderGap`: Represents explicit silent/black spaces between non-contiguous clips.
4. `total_duration_us`: Derived maximum microsecond timeline end position across all tracks and clips.