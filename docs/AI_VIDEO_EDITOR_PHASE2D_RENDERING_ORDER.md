# Phase 2D Deterministic Filter Pipeline Rendering Order

This document specifies the strict execution order for video and audio filter processing in the FFmpeg filtergraph compiled by `RenderPlanner`.

---

## 1. Video Filter Pipeline Order

For each video clip segment, visual processing MUST proceed through the following deterministic filter sequence:

```
[Input Stream]
      │
      ▼
1. Source Trim (`trim=start=S1:end=S2`)
      │
      ▼
2. Temporal PTS Offset (`setpts=PTS-STARTPTS+PTS_FACTOR*PTS`)
      │
      ▼
3. Visual Effects Chain (`boxblur`, `eq`, `hue`, `vignette`, etc.)
      │
      ▼
4. Spatial Scaling & Transform (`scale=W:H`)
      │
      ▼
5. Frame Rate Normalization (`fps=R`)
      │
      ▼
6. Z-Ordered Overlay Compositing (`overlay=x=X:y=Y:enable='between(t,T1,T2)'`)
      │
      ▼
7. Inbound / Outbound Video Transitions (`xfade`)
      │
      ▼
8. Text & Subtitle Overlays (`drawtext`)
      │
      ▼
[Final Canvas Stream]
```

### Rationale

1. **Trim First:** Trimming source input before applying spatial or temporal filters minimizes pixel processing overhead.
2. **Speed / PTS Adjustment Second:** Adjusting timebase scale (`setpts`) before applying spatial or temporal effects ensures temporal parameter expressions evaluate on the modified clip clock.
3. **Effects Before Scale:** Applying visual effects (e.g. blur or color adjustment) at native/trimmed resolution prevents scaling artifacts from affecting filter quality.
4. **Scale & Transform Fourth:** Spatial transforms normalize clip dimensions to canvas coordinate space prior to compositing.
5. **Frame Rate Normalization:** Standardizes frame output rates across diverse input assets before canvas overlay blending.
6. **Overlay Compositing:** Blends visual streams onto black background canvas in z-index order with timeline `enable` intervals.
7. **Text Overlays Last:** Text overlays burn in cleanly on top of composited video tracks.

---

## 2. Audio Filter Pipeline Order

For each audio clip segment, audio processing MUST proceed through the following deterministic filter sequence:

```
[Input Stream]
      │
      ▼
1. Source Trim (`atrim=start=S1:end=S2`)
      │
      ▼
2. Temporal PTS Offset (`asetpts=PTS-STARTPTS`)
      │
      ▼
3. Speed Adjustment (`atempo=FACTOR` / Chained `atempo`)
      │
      ▼
4. Sample Rate & Layout Normalization (`aformat=sample_rates=SR:channel_layouts=stereo`)
      │
      ▼
5. Volume Gain Adjustment (`volume=V`)
      │
      ▼
6. Audio Transitions (`acrossfade` / `afade`)
      │
      ▼
7. Timeline Delay Alignment (`adelay=delays=D|D`)
      │
      ▼
8. Multi-Track Audio Mixing (`amix=inputs=N`)
      │
      ▼
[Final Mixed Audio Stream]
```

---

## 3. Guiding Principles

* **Determinism:** Given identical `VideoProject` IR inputs, the compiled FFmpeg command filtergraph MUST be byte-for-byte deterministic.
* **No Re-ordering:** Filter node order must never fluctuate between compilation passes.
* **Microsecond Precision:** All start, end, and duration parameters MUST be derived from microsecond integer bounds transformed to float seconds.
