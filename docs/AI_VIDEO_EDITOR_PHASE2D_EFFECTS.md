# Phase 2D Reusable & Temporal Effects Specification

This document specifies the IR model representations, supported filter parameters, and compilation rules for reusable visual effects.

---

## 1. Supported Effect Types & Filter Specifications

| EffectType | FFmpeg Filter | Parameters & Defaults | Example Output |
| :--- | :--- | :--- | :--- |
| `BLUR` | `boxblur` | `radius: int = 5` | `boxblur=luma_radius=5:luma_power=1` |
| `BRIGHTNESS` | `eq` | `brightness: float = 0.0` | `eq=brightness=0.2000` |
| `CONTRAST` | `eq` | `contrast: float = 1.0` | `eq=contrast=1.5000` |
| `GRAYSCALE` | `hue` | N/A (`s=0`) | `hue=s=0` |
| `VIGNETTE` | `vignette` | `angle: str = "PI/5"` | `vignette=angle=PI/5` |

---

## 2. Temporal Interval Filtering (`enable`)

Effects support optional clip-local temporal interval bounds (`start_time_us` and `duration_us`).

When specified, the compiler appends an FFmpeg `enable` evaluation string to restrict filter execution to the specified interval:

$$\text{enable='between(t, } T_{\text{start}}, T_{\text{end}} \text{)'}$$

### Example

For a blur effect active between 1.0s and 3.0s into a clip:

```
boxblur=luma_radius=10:luma_power=1:enable='between(t,1.000000,3.000000)'
```

---

## 3. Chaining Multiple Effects

Multiple effects attached to a clip's `effects: List[Effect]` field are compiled sequentially into dedicated filter nodes in the `FilterGraph`, following the deterministic execution order defined in `docs/AI_VIDEO_EDITOR_PHASE2D_RENDERING_ORDER.md`.
