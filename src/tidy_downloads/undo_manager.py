"""Undo functionality for TidyDownloads file organization."""

import json
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class UndoManager:
    """Manages undo history for file organization operations."""

    def __init__(self, history_dir: Optional[Path] = None):
        """
        Initialize undo manager.

        Args:
            history_dir: Optional custom path for history storage.
                        Defaults to ~/Library/Application Support/TidyDownloads/history/
        """
        if history_dir is None:
            app_support = Path.home() / "Library" / "Application Support" / "TidyDownloads"
            self.history_dir = app_support / "history"
        else:
            self.history_dir = Path(history_dir)

        # Create history directory if it doesn't exist
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # Maximum number of undo sessions to keep
        self.max_sessions = 5

        # Auto-cleanup old manifests (> 30 days)
        self.cleanup_threshold_days = 30

    def create_manifest(
        self,
        moves: Dict[str, List[Tuple[Path, Path]]],
        errors: List[str]
    ) -> Path:
        """
        Create an undo manifest for a file organization operation.

        Args:
            moves: Dictionary mapping category to list of (source, destination) tuples
            errors: List of error messages during organization

        Returns:
            Path to the created manifest file
        """
        timestamp = datetime.now()
        manifest_filename = timestamp.strftime("%Y-%m-%d_%H-%M-%S.json")
        manifest_path = self.history_dir / manifest_filename

        # Convert Path objects to strings for JSON serialization
        manifest_data = {
            "timestamp": timestamp.isoformat(),
            "moves": {
                category: [
                    {
                        "source": str(src),
                        "destination": str(dest)
                    }
                    for src, dest in file_list
                ]
                for category, file_list in moves.items()
            },
            "errors": errors,
            "total_files": sum(len(file_list) for file_list in moves.values()),
            "undone": False
        }

        try:
            with open(manifest_path, 'w') as f:
                json.dump(manifest_data, f, indent=2)

            logger.info(f"Created undo manifest: {manifest_path}")

            # Cleanup old manifests
            self._cleanup_old_manifests()

            return manifest_path

        except Exception as e:
            logger.error(f"Error creating undo manifest: {e}")
            raise

    def get_latest_manifest(self) -> Optional[Path]:
        """
        Get the most recent undo manifest.

        Returns:
            Path to latest manifest, or None if no manifests exist
        """
        try:
            manifests = sorted(
                self.history_dir.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            if not manifests:
                logger.info("No undo manifests found")
                return None

            return manifests[0]

        except Exception as e:
            logger.error(f"Error getting latest manifest: {e}")
            return None

    def load_manifest(self, manifest_path: Path) -> Dict:
        """
        Load an undo manifest from file.

        Args:
            manifest_path: Path to manifest file

        Returns:
            Manifest data dictionary
        """
        try:
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)

            logger.debug(f"Loaded manifest: {manifest_path}")
            return manifest_data

        except Exception as e:
            logger.error(f"Error loading manifest {manifest_path}: {e}")
            raise

    def undo(self, manifest_path: Optional[Path] = None) -> Tuple[int, List[str]]:
        """
        Undo a file organization operation.

        Args:
            manifest_path: Optional specific manifest to undo.
                          Defaults to most recent manifest.

        Returns:
            Tuple of (number of files restored, list of errors)
        """
        if manifest_path is None:
            manifest_path = self.get_latest_manifest()

        if manifest_path is None:
            logger.warning("No manifest available to undo")
            return 0, ["No organization history found to undo"]

        try:
            manifest_data = self.load_manifest(manifest_path)

            # Check if already undone
            if manifest_data.get("undone", False):
                logger.warning(f"Manifest already undone: {manifest_path}")
                return 0, ["This organization has already been undone"]

            files_restored = 0
            errors = []

            # Restore files in reverse order (destination → source)
            for category, moves in manifest_data["moves"].items():
                for move in moves:
                    source = Path(move["source"])
                    destination = Path(move["destination"])

                    try:
                        # Check if destination file still exists
                        if not destination.exists():
                            error_msg = f"File no longer exists: {destination.name}"
                            logger.warning(error_msg)
                            errors.append(error_msg)
                            continue

                        # Check if source location is available
                        if source.exists():
                            error_msg = f"Source location occupied: {source.name}"
                            logger.warning(error_msg)
                            errors.append(error_msg)
                            continue

                        # Move file back to original location
                        shutil.move(str(destination), str(source))
                        files_restored += 1
                        logger.info(f"Restored: {destination.name} → {source}")

                    except Exception as e:
                        error_msg = f"Error restoring {destination.name}: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)

            # Mark manifest as undone
            manifest_data["undone"] = True
            manifest_data["undo_timestamp"] = datetime.now().isoformat()

            with open(manifest_path, 'w') as f:
                json.dump(manifest_data, f, indent=2)

            logger.info(f"Undo completed: {files_restored} files restored")

            # Try to remove empty category folders
            self._cleanup_empty_folders(manifest_data)

            return files_restored, errors

        except Exception as e:
            logger.error(f"Error during undo operation: {e}")
            return 0, [f"Undo failed: {str(e)}"]

    def get_undo_preview(self, manifest_path: Optional[Path] = None) -> str:
        """
        Get a preview of what will be undone.

        Args:
            manifest_path: Optional specific manifest to preview.
                          Defaults to most recent manifest.

        Returns:
            Human-readable preview string
        """
        if manifest_path is None:
            manifest_path = self.get_latest_manifest()

        if manifest_path is None:
            return "No organization history found to undo"

        try:
            manifest_data = self.load_manifest(manifest_path)

            if manifest_data.get("undone", False):
                return "This organization has already been undone"

            timestamp = datetime.fromisoformat(manifest_data["timestamp"])
            total_files = manifest_data["total_files"]

            preview_lines = [
                f"\nUndo Preview",
                f"Organization Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                f"Total Files: {total_files}\n"
            ]

            for category, moves in manifest_data["moves"].items():
                if moves:
                    preview_lines.append(f"{category} ({len(moves)} files):")
                    for move in moves[:5]:  # Show first 5
                        dest_name = Path(move["destination"]).name
                        preview_lines.append(f"  • {dest_name}")

                    if len(moves) > 5:
                        preview_lines.append(f"  ... and {len(moves) - 5} more")

                    preview_lines.append("")

            return "\n".join(preview_lines)

        except Exception as e:
            logger.error(f"Error creating undo preview: {e}")
            return f"Error loading undo information: {str(e)}"

    def _cleanup_empty_folders(self, manifest_data: Dict) -> None:
        """
        Remove empty category folders after undo.

        Args:
            manifest_data: Manifest containing information about moved files
        """
        folders_to_check = set()

        # Collect all destination folders
        for moves in manifest_data["moves"].values():
            for move in moves:
                dest_path = Path(move["destination"])
                if dest_path.parent != dest_path:  # Not root
                    folders_to_check.add(dest_path.parent)

        # Try to remove each folder if empty
        for folder in folders_to_check:
            try:
                if folder.exists() and folder.is_dir():
                    # Check if folder is empty
                    if not any(folder.iterdir()):
                        folder.rmdir()
                        logger.info(f"Removed empty folder: {folder.name}")
            except Exception as e:
                logger.debug(f"Could not remove folder {folder}: {e}")

    def _cleanup_old_manifests(self) -> None:
        """Remove old undo manifests based on retention policy."""
        try:
            # Get all manifests sorted by modification time (newest first)
            all_manifests = sorted(
                self.history_dir.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            # Remove manifests beyond max_sessions
            for manifest in all_manifests[self.max_sessions:]:
                try:
                    manifest.unlink()
                    logger.debug(f"Removed old manifest (retention limit): {manifest.name}")
                except Exception as e:
                    logger.warning(f"Could not remove old manifest {manifest.name}: {e}")

            # Remove manifests older than threshold
            cutoff_date = datetime.now() - timedelta(days=self.cleanup_threshold_days)

            for manifest in all_manifests:
                try:
                    mtime = datetime.fromtimestamp(manifest.stat().st_mtime)
                    if mtime < cutoff_date:
                        manifest.unlink()
                        logger.debug(f"Removed old manifest (age threshold): {manifest.name}")
                except Exception as e:
                    logger.warning(f"Could not remove old manifest {manifest.name}: {e}")

        except Exception as e:
            logger.warning(f"Error during manifest cleanup: {e}")

    def get_history(self, limit: int = 10) -> List[Dict]:
        """
        Get history of organization operations.

        Args:
            limit: Maximum number of history entries to return

        Returns:
            List of manifest summaries
        """
        try:
            manifests = sorted(
                self.history_dir.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:limit]

            history = []

            for manifest_path in manifests:
                try:
                    manifest_data = self.load_manifest(manifest_path)

                    summary = {
                        "timestamp": manifest_data["timestamp"],
                        "total_files": manifest_data["total_files"],
                        "undone": manifest_data.get("undone", False),
                        "manifest_file": manifest_path.name
                    }

                    history.append(summary)

                except Exception as e:
                    logger.warning(f"Could not load manifest {manifest_path.name}: {e}")

            return history

        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []
