"""Timeline Compiler Engine: Compiles VideoProject IR to pure RenderPlan."""

from typing import Dict, List
from video_editor.compiler.models import (
    RenderGap,
    RenderInput,
    RenderOutputSettings,
    RenderPlan,
    RenderSegment,
    RenderTrack,
)
from video_editor.compiler.validation import validate_project_renderability
from video_editor.ir.enums import TrackType
from video_editor.ir.models import VideoProject
from video_editor.media.resolver import AssetResolver


class TimelineCompiler:
    """Compiles read-only VideoProject IR into an execution-ready RenderPlan.

    The compiler is a pure transformation function:
    - Does NOT invoke FFmpeg subprocesses.
    - Does NOT mutate VideoProject IR state.
    - Resolves timeline placement, sorts clips, and inserts explicit gaps.
    """

    def compile(self, project: VideoProject) -> RenderPlan:
        """Compile VideoProject IR into a deterministic RenderPlan."""
        # 1. Pre-compilation Validation Gate
        validate_project_renderability(project)

        # 2. Build RenderInputs (Register disk paths for all used assets)
        inputs: List[RenderInput] = []
        asset_id_to_input_index: Dict[str, int] = {}

        # Collect unique assets used across all un-muted active clips
        for track in project.tracks:
            if track.muted:
                continue
            for clip in track.clips:
                if clip.asset_id and clip.asset_id not in asset_id_to_input_index:
                    resolved_path = AssetResolver.resolve_asset_path(project, clip.asset_id)
                    input_idx = len(inputs)
                    asset_id_to_input_index[clip.asset_id] = input_idx
                    inputs.append(
                        RenderInput(
                            input_index=input_idx,
                            asset_id=clip.asset_id,
                            file_path=resolved_path,
                        )
                    )

        # 3. Output Settings
        output_settings = RenderOutputSettings(
            width=project.settings.width,
            height=project.settings.height,
            fps=project.settings.fps,
        )

        # 4. Compile Tracks (Resolve ordering, sort clips, insert gaps)
        render_tracks: List[RenderTrack] = []
        project_duration_us = 0

        # Sort tracks by z-index
        sorted_tracks = sorted(project.tracks, key=lambda t: t.index)

        for track in sorted_tracks:
            if track.muted or len(track.clips) == 0:
                continue

            track_items: List[RenderSegment | RenderGap] = []
            cursor_time_us = 0

            # Sort clips sequentially by timeline_start_us
            sorted_clips = sorted(track.clips, key=lambda c: c.timeline_start_us)

            for clip in sorted_clips:
                # Detect Timeline Gap
                if clip.timeline_start_us > cursor_time_us:
                    gap_duration_us = clip.timeline_start_us - cursor_time_us
                    track_items.append(
                        RenderGap(
                            timeline_start_us=cursor_time_us,
                            timeline_duration_us=gap_duration_us,
                        )
                    )
                    cursor_time_us = clip.timeline_start_us

                input_idx = asset_id_to_input_index[clip.asset_id] if clip.asset_id else 0
                segment = RenderSegment(
                    clip_id=clip.id,
                    asset_id=clip.asset_id or "",
                    input_index=input_idx,
                    timeline_start_us=clip.timeline_start_us,
                    timeline_duration_us=clip.timeline_duration_us,
                    source_start_us=clip.source_start_us,
                    source_duration_us=clip.source_duration_us,
                    speed=clip.speed,
                    volume=clip.audio.volume if not clip.audio.muted else 0.0,
                )
                track_items.append(segment)
                cursor_time_us = segment.timeline_end_us

            if cursor_time_us > project_duration_us:
                project_duration_us = cursor_time_us

            render_tracks.append(
                RenderTrack(
                    track_id=track.id,
                    track_type=track.type,
                    index=track.index,
                    items=track_items,
                )
            )

        return RenderPlan(
            project_id=project.id,
            version=project.version,
            total_duration_us=project_duration_us,
            output_settings=output_settings,
            inputs=inputs,
            tracks=render_tracks,
        )
