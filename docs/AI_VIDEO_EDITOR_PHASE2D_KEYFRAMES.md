# Phase 2D Keyframe & Animation Specification

This document specifies the IR model representations and compiler rules for keyframed animations on clip transform and audio properties.

---

## 1. Keyframe IR Schema

Keyframes are attached to clips via `animation_tracks: List[AnimationTrack]` in `RenderSegment`.

### Animated Properties (`AnimatedProperty`)

* `POSITION_X`
* `POSITION_Y`
* `SCALE_X`
* `SCALE_Y`
* `OPACITY`
* `VOLUME`

### Interpolation Modes (`InterpolationMode`)

* `HOLD`: Holds value constant until next keyframe.
* `LINEAR`: Linear interpolation between keyframes.

---

## 2. Mathematical Interpolation Formula

For a target clip microsecond offset $t \in [t_1, t_2]$ bounded by keyframe $K_1 = (t_1, v_1)$ and $K_2 = (t_2, v_2)$:

### LINEAR Mode

$$v(t) = v_1 + \frac{t - t_1}{t_2 - t_1} \cdot (v_2 - v_1)$$

### HOLD Mode

$$v(t) = v_1$$

---

## 3. FFmpeg Filter Expression Compilation

For animated properties compiled into FFmpeg filters (such as `opacity` or `drawtext` evaluation variables), the compiler generates nested `if()` piecewise mathematical evaluation strings using second timestamp variable `t`.

### Example

For opacity keyframes $K_1 = (0\text{s}, 0.0)$ and $K_2 = (1.0\text{s}, 1.0)$:

```
if(lte(t,0.000000),0.0,if(lte(t,1.000000),0.0+1.000000*(t-0.000000),1.0))
```
