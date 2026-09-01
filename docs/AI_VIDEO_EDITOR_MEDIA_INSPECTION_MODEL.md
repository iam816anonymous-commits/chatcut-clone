# AI Video Editor — Media Inspection & Metadata Model

## Executive Summary
This document specifies the media inspection architecture, FFprobe JSON extraction pipeline, duration resolution hierarchy, and rational frame rate parsing rules.

---

## 1. Media Inspection Architecture

The `MediaInspector` class executes `ffprobe` in JSON mode (`-of json -show_format -show_streams -v error`) via `ProcessExecutor`:

```text
Local Media File Path
          │
          ▼
   MediaInspector
          │
          ▼
   Execute FFprobe (Argument Array)
          │
          ▼
 Parse FFprobe Output JSON
          │
          ▼
Construct Typed MediaMetadata
```

---

## 2. Duration Resolution Hierarchy

To handle differences between container formats, video streams, and audio streams:

1. **Primary**: Container format duration (`format.duration`).
2. **Secondary**: Primary video stream duration (`stream.duration`).
3. **Tertiary**: Primary audio stream duration (`stream.duration`).
4. **Fallback**: `None` (for static image containers like PNG, JPEG, WebP).

Microseconds conversion formula:
$$\text{duration\_us} = \text{round}(\text{float(duration\_sec)} \times 1,000,000)$$

---

## 3. Rational Frame Rate Parsing

FFprobe returns frame rates as fractional strings (e.g., `"30000/1001"`).
`parse_rational_fps` converts fractional strings to floating point FPS without crashing on `"0/0"` or malformed values:

$$\text{FPS} = \frac{\text{Numerator}}{\text{Denominator}}$$

Example: `"30000/1001"` $\rightarrow 29.97002997...$ FPS.