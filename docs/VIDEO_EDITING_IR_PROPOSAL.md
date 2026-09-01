# Universal Video Editing Intermediate Representation (IR) Proposal

## Overview
The **Universal Video Editing IR** is a clean, editor-independent, JSON-based specification for describing video timeline edits, media assets, track hierarchies, keyframes, audio spatialization, and video processing operations.

By decoupling editing intent from specific software platforms (like CapCut, Premiere, or FFmpeg), the IR serves as the single source of truth for the AI Video Assistant.

---

## Complete JSON Schema Architecture

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "UniversalVideoEditingIR",
  "type": "object",
  "required": ["version", "project", "assets", "tracks"],
  "properties": {
    "version": { "type": "string", "example": "1.0.0" },
    "project": {
      "type": "object",
      "required": ["id", "name", "width", "height", "fps", "timebase"],
      "properties": {
        "id": { "type": "string", "format": "uuid" },
        "name": { "type": "string" },
        "width": { "type": "integer", "default": 1080 },
        "height": { "type": "integer", "default": 1920 },
        "fps": { "type": "number", "default": 30.0 },
        "timebase": { "type": "string", "enum": ["seconds", "microseconds", "frames"], "default": "seconds" },
        "backgroundColor": { "type": "string", "default": "#000000" }
      }
    },
    "assets": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "type", "path", "duration"],
        "properties": {
          "id": { "type": "string" },
          "type": { "type": "string", "enum": ["video", "audio", "image", "font"] },
          "path": { "type": "string" },
          "duration": { "type": "number" },
          "width": { "type": "integer" },
          "height": { "type": "integer" },
          "sampleRate": { "type": "integer" },
          "channels": { "type": "integer" }
        }
      }
    },
    "tracks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "type", "index", "clips"],
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" },
          "type": { "type": "string", "enum": ["video", "audio", "text", "subtitle", "effect"] },
          "index": { "type": "integer", "description": "Z-order / Track priority layer" },
          "muted": { "type": "boolean", "default": false },
          "locked": { "type": "boolean", "default": false },
          "clips": {
            "type": "array",
            "items": { "$ref": "#/$defs/Clip" }
          }
        }
      }
    }
  },
  "$defs": {
    "Clip": {
      "type": "object",
      "required": ["id", "assetId", "timelineStart", "timelineEnd", "sourceStart", "sourceEnd"],
      "properties": {
        "id": { "type": "string" },
        "assetId": { "type": "string" },
        "timelineStart": { "type": "number" },
        "timelineEnd": { "type": "number" },
        "sourceStart": { "type": "number" },
        "sourceEnd": { "type": "number" },
        "speed": { "type": "number", "default": 1.0 },
        "volume": { "type": "number", "default": 1.0 },
        "transform": {
          "type": "object",
          "properties": {
            "x": { "type": "number", "default": 0 },
            "y": { "type": "number", "default": 0 },
            "scaleX": { "type": "number", "default": 1.0 },
            "scaleY": { "type": "number", "default": 1.0 },
            "rotation": { "type": "number", "default": 0 }
          }
        },
        "textStyle": {
          "type": "object",
          "properties": {
            "content": { "type": "string" },
            "fontSize": { "type": "number" },
            "fontColor": { "type": "string" },
            "fontFamily": { "type": "string" },
            "alignment": { "type": "string", "enum": ["left", "center", "right"] }
          }
        },
        "effects": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["type", "params"],
            "properties": {
              "type": { "type": "string", "enum": ["blur", "brightness", "contrast", "crop", "audioFade"] },
              "params": { "type": "object" }
            }
          }
        },
        "transitions": {
          "type": "object",
          "properties": {
            "in": { "type": "object", "properties": { "type": { "type": "string" }, "duration": { "type": "number" } } },
            "out": { "type": "object", "properties": { "type": { "type": "string" }, "duration": { "type": "number" } } }
          }
        }
      }
    }
  }
}
```

---

## Detailed Feature Support

1. **Multi-Track Z-Ordering**: Tracks are indexed (`0..N`). Index $0$ represents the background layer; higher indices render on top (PIP, overlays, captions).
2. **Precision Timing**: Supports float seconds or integer microseconds to avoid rounding errors during frame cuts.
3. **Clip Source Trimming**: Explicit separation of `sourceStart`/`sourceEnd` (trim bounds inside raw asset) and `timelineStart`/`timelineEnd` (position on global timeline).
4. **Spatial Geometry**: 2D Affine transformations (Scale, Translation X/Y, Rotation in degrees) per clip.
5. **Speed Manipulation**: Dynamic speed multiplier ($0.1\times$ to $10.0\times$) recomputes clip duration automatically.
6. **Subtitles & Captions**: Text tracks support timed word-level caption blocks.

---

## Standard Atomic AI Editing Operations

When the AI Planner makes edits, it emits structured operation payloads against the IR:

* `TRIM_CLIP(clip_id, source_start, source_end)`
* `SPLIT_CLIP(clip_id, split_time)`
* `MOVE_CLIP(clip_id, target_track_id, target_timeline_start)`
* `INSERT_TEXT(track_id, content, timeline_start, duration, style)`
* `SET_CLIP_VOLUME(clip_id, volume)`
* `ADD_TRANSITION(clip_id, type, duration)`
* `REMOVE_SILENCE(threshold_db, min_silence_duration_sec)`

---

## Why Editor-Independent IR is Superior to CapCut Coupling

| Dimension | Directly Modifying CapCut Draft | Universal Video Editing IR |
| :--- | :--- | :--- |
| **Stability** | **Fragile**: App updates silent-break JSON tags | **Stable**: Versioned schema with semantic guarantees |
| **Portability** | **Locked-in**: CapCut only | **Universal**: Renderable via FFmpeg, Remotion, MLT, or exportable |
| **AI Operability** | **Complex**: Unnecessary GUI-internal state keys | **Clean**: Lean schema designed for LLM tool calling |
| **Validation** | **Hard**: CapCut fails silently on bad schema | **Deterministic**: JSON Schema validation in milliseconds |
| **Vendor Dependency**| High risk of breakage/ToS updates | Zero lock-in, open source |