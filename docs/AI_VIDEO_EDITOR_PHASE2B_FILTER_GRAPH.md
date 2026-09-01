# AI Video Editor — Structured FFmpeg FilterGraph Specification

## Executive Summary
This document specifies the structured filtergraph nodes, label allocation rules, and `filter_complex` string formatting implemented in `video_editor.compiler.filter_graph`.

---

## 1. FilterGraph Abstraction
Rather than concatenating unstructured string fragments, FFmpeg filter graphs are constructed via strongly typed `FilterNode` instances:

```python
node = FilterNode(
    inputs=["0:v"],
    filter_name="trim",
    params=["start=0.000000", "end=5.000000"],
    outputs=["v_trim0"]
)
# Formats to: [0:v] trim=start=0.000000:end=5.000000 [v_trim0]
```

---

## 2. Deterministic Label Allocation
`LabelAllocator` maintains sequential counter states for video and audio stream tags:
* Video Stream Labels: `v_trim0`, `v_norm0`, `v_sc0`, `v_seg0`, `outv`.
* Audio Stream Labels: `a_trim0`, `a_norm0`, `a_seg0`, `outa`.

Re-compiling identical `RenderPlan` structures produces 100% deterministic stream label strings.

---

## 3. Concat Node Construction
To concatenate $N$ visual or audio segments, the `concat` node links the outputs of surrounding segment nodes:

```text
[v_seg0][v_gap1][v_seg2] concat=n=3:v=1:a=0 [outv]
[a_seg0][a_gap1][a_seg2] concat=n=3:v=0:a=1 [outa]
```

The resulting `filter_complex` string is passed directly to FFmpeg via `-filter_complex "<string>" -map "[outv]" -map "[outa]"`.