"""Asset Resolver module for resolving IR asset IDs to verified local media disk paths."""

import os
from video_editor.ir.exceptions import AssetNotFoundError
from video_editor.ir.models import Asset, VideoProject
from video_editor.media.exceptions import InputFileNotFoundError


class AssetResolver:
    """Resolves IR asset_id references against project inventory and verifies local disk paths."""

    @staticmethod
    def resolve_asset_path(project: VideoProject, asset_id: str) -> str:
        """Resolve asset_id inside project and return canonical absolute disk path.

        Raises:
            AssetNotFoundError: If asset_id is not in project.assets.
            InputFileNotFoundError: If asset file path does not exist on disk or is a directory.
        """
        if asset_id not in project.assets:
            raise AssetNotFoundError(
                f"Asset ID '{asset_id}' not registered in project inventory",
                {"asset_id": asset_id, "registered_assets": list(project.assets.keys())},
            )

        asset: Asset = project.assets[asset_id]
        abs_path = os.path.abspath(os.path.realpath(asset.path))

        if not os.path.exists(abs_path):
            raise InputFileNotFoundError(
                f"Resolved disk file path for asset '{asset_id}' does not exist: {abs_path}",
                {"asset_id": asset_id, "path": abs_path},
            )

        if os.path.isdir(abs_path):
            raise InputFileNotFoundError(
                f"Resolved path for asset '{asset_id}' is a directory, not a file: {abs_path}",
                {"asset_id": asset_id, "path": abs_path},
            )

        return abs_path
