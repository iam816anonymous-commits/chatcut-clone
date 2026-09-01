# AI Video Editor — Future Keyframe Animation Model

## Executive Summary
This design document specifies the future architecture for animated keyframes inside the Universal Video Editing Intermediate Representation (IR).

While Phase 1 provides static properties (e.g., constant `Transform` or constant `AudioConfig` volume), this document ensures that current schema decisions will seamlessly accommodate dynamic parameter interpolation in future phases.

---

## 1. Keyframe Abstraction Principles

An animated property is represented as a sequence of **Keyframes** mapped to time offsets relative to clip start:

$$\text{Clip Local Time} = \text{Timeline Position} - \text{Clip Timeline Start}$$

Each keyframe contains:
* `offset_us`: Microsecond offset from clip start ($0 \le \text{offset\_us} \le \text{timeline\_duration\_us}$).
* `value`: Float value or composite parameter object (e.g., opacity, scale, position, volume).
* `easing`: Easing interpolation curve enum (`LINEAR`, `EASE_IN`, `EASE_OUT`, `EASE_IN_OUT`, `BEZIER`, `HOLD`).
* `control_points`: Optional cubic Bezier control handle coordinates $[x_1, y_1, x_2, y_2]$.

---

## 2. Proposed Future JSON Schema Extension

```json
{
  "keyframe_tracks": {
    "transform.scale_x": {
      "property": "transform.scale_x",
      "keyframes": [
        {
          "offset_us": 0,
          "value": 1.0,
          "easing": "EASE_IN"
        },
        {
          "offset_us": 1000000,
          "value": 1.2,
          "easing": "EASE_OUT"
        }
      ]
    },
    "audio.volume": {
      "property": "audio.volume",
      "keyframes": [
        {
          "offset_us": 0,
          "value": 0.0,
          "easing": "LINEAR"
        },
        {
          "offset_us": 500000,
          "value": 1.0,
          "easing": "LINEAR"
        }
      ]
    }
  }
}
```

---

## 3. Backward Compatibility Strategy
* In Phase 1, `Transform` and `AudioConfig` store fallback static fields (`scale_x = 1.0`, `volume = 1.0`).
* In Phase 2/3, when `keyframe_tracks` are populated, rendering adapters (FFmpeg `eval=frame` / Remotion `interpolate()`) will evaluate keyframe curves at specific frame times.
* If a property has no keyframe track defined, the renderer falls back to the static property value.