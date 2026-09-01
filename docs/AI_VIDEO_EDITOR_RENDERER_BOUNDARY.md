# AI Video Editor — Renderer Boundary & Adapter Interface Specification

## Executive Summary
This document specifies the architectural boundary between the **Universal Video Editing IR** and future video rendering backends (such as **FFmpeg** or **Remotion**).

---

## 1. Core Boundary Principles

1. **IR as Single Source of Truth**: Renderers are strictly **read-only consumers** of the `VideoProject` IR. A renderer MUST NEVER mutate project state directly.
2. **Zero Renderer Coupling in IR**: The IR contains zero FFmpeg filtergraph strings, command flags, Remotion JSX component tags, or CapCut internal IDs.
3. **Adapter Pattern**: Each video rendering backend implements a dedicated adapter class that translates IR semantic models into renderer-native execution instructions.

```text
               ┌─────────────────────────────┐
               │    Universal Video IR       │
               │   (VideoProject Object)     │
               └──────────────┬──────────────┘
                              │ Read-Only Access
               ┌──────────────┴──────────────┐
               ▼                             ▼
   ┌───────────────────────┐     ┌───────────────────────┐
   │    FFmpeg Adapter     │     │   Remotion Adapter    │
   │  Converts IR to       │     │  Converts IR to       │
   │  FFmpeg Filtergraph   │     │  React Compositions   │
   └───────────┬───────────┘     └───────────┬───────────┘
               │                             │
               ▼                             ▼
   ┌───────────────────────┐     ┌───────────────────────┐
   │    FFmpeg CLI/Lib     │     │   Headless Chromium   │
   │   (Binary Render)     │     │    (Frame Render)     │
   └───────────────────────┘     └───────────────────────┘
```

---

## 2. Abstract Renderer Interface

Future rendering engines will implement the following standardized abstract interface:

```python
from abc import ABC, abstractmethod
from typing import Callable, Optional
from video_editor.ir.models import VideoProject

class BaseRenderer(ABC):
    """Abstract Base Class for all video rendering adapters."""

    @abstractmethod
    def render(
        self,
        project: VideoProject,
        output_path: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> str:
        """Translates VideoProject IR state and renders output media file.

        Args:
            project: Validated VideoProject IR instance.
            output_path: Target media file path on local disk.
            progress_callback: Optional float callback (0.0 to 1.0).

        Returns:
            Absolute path to rendered output media file.
        """
        pass
```

---

## 3. Translation Mapping Principles

* **Trimming**: Map clip `source_start_us` and `source_duration_us` to FFmpeg `-ss` and `-t` input flags or Remotion `<Sequence from={...} durationInFrames={...}>`.
* **Transforms**: Map clip `transform.scale_x` and `position_x` to FFmpeg `scale` / `overlay` filters or Remotion CSS `transform: translate() scale()`.
* **Audio Ducking & Volume**: Map clip `audio.volume` to FFmpeg `volume=volume=X` audio filter.

By isolating all rendering execution logic inside renderer adapters, the IR remains completely clean, deterministic, and future-proof.