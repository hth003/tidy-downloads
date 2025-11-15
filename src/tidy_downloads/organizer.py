"""Core file organization logic for TidyDownloads."""

import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


class FileOrganizer:
    """Organizes files in the Downloads folder based on configuration."""

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the file organizer.

        Args:
            config_manager: ConfigManager instance for accessing settings
        """
        self.config = config_manager
        self.downloads_path = self.config.get_downloads_path()

    def scan_files(self, dry_run: bool = False) -> Dict[str, List[Path]]:
        """
        Scan Downloads folder for files that need organization.

        Args:
            dry_run: If True, only scan without making changes

        Returns:
            Dictionary mapping category names to lists of file paths
        """
        if not self.downloads_path.exists():
            logger.error(f"Downloads path does not exist: {self.downloads_path}")
            return {}

        min_age_days = self.config.get_minimum_file_age_days()
        cutoff_time = datetime.now() - timedelta(days=min_age_days)

        categorized_files: Dict[str, List[Path]] = defaultdict(list)

        try:
            # Iterate through items in Downloads folder
            for item in self.downloads_path.iterdir():
                # Skip if it's a directory (user-created folder or organized folder)
                if item.is_dir():
                    continue

                # Skip hidden files (starting with .)
                if item.name.startswith('.'):
                    continue

                # Check file age
                try:
                    file_mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if file_mtime > cutoff_time:
                        logger.debug(f"Skipping recent file: {item.name}")
                        continue
                except Exception as e:
                    logger.warning(f"Could not check age of {item.name}: {e}")
                    continue

                # Get category for this file
                extension = item.suffix.lower()
                category = self.config.get_category_for_extension(extension)

                # Skip if category is disabled
                if not self.config.is_category_enabled(category):
                    logger.debug(f"Skipping file with disabled category: {item.name} ({category})")
                    continue

                categorized_files[category].append(item)
                logger.debug(f"Categorized {item.name} as {category}")

            logger.info(f"Scanned {self.downloads_path}: found {sum(len(files) for files in categorized_files.values())} files to organize")

        except Exception as e:
            logger.error(f"Error scanning downloads folder: {e}")
            return {}

        return dict(categorized_files)

    def organize(self, dry_run: bool = False) -> Tuple[Dict[str, List[Tuple[Path, Path]]], List[str]]:
        """
        Organize files into category folders.

        Args:
            dry_run: If True, only preview without actually moving files

        Returns:
            Tuple of:
            - Dictionary mapping category names to list of (source, destination) tuples
            - List of error messages
        """
        categorized_files = self.scan_files()

        if not categorized_files:
            logger.info("No files to organize")
            return {}, []

        moves: Dict[str, List[Tuple[Path, Path]]] = defaultdict(list)
        errors: List[str] = []

        for category, files in categorized_files.items():
            # Create destination folder
            dest_folder_name = self.config.get_destination_folder_name(category)
            dest_folder = self.downloads_path / dest_folder_name

            if not dry_run:
                try:
                    dest_folder.mkdir(exist_ok=True)
                    logger.debug(f"Created/verified folder: {dest_folder}")
                except Exception as e:
                    error_msg = f"Could not create folder {dest_folder_name}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

            # Move files to destination
            for file_path in files:
                try:
                    dest_path = self._get_unique_destination(dest_folder, file_path.name)

                    if not dry_run:
                        # Check if file is in use or locked
                        if self._is_file_locked(file_path):
                            error_msg = f"File is locked or in use: {file_path.name}"
                            logger.warning(error_msg)
                            errors.append(error_msg)
                            continue

                        # Move the file
                        shutil.move(str(file_path), str(dest_path))
                        logger.info(f"Moved: {file_path.name} → {dest_folder_name}/{dest_path.name}")

                    moves[category].append((file_path, dest_path))

                except Exception as e:
                    error_msg = f"Error moving {file_path.name}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

        if dry_run:
            logger.info(f"DRY RUN: Would organize {sum(len(m) for m in moves.values())} files")
        else:
            logger.info(f"Successfully organized {sum(len(m) for m in moves.values())} files")

        return dict(moves), errors

    def _get_unique_destination(self, dest_folder: Path, filename: str) -> Path:
        """
        Get a unique destination path, adding _2, _3, etc. if file exists.

        Args:
            dest_folder: Destination folder path
            filename: Original filename

        Returns:
            Unique destination path
        """
        dest_path = dest_folder / filename

        if not dest_path.exists():
            return dest_path

        # File exists, find unique name
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        counter = 2

        while True:
            new_name = f"{stem}_{counter}{suffix}"
            dest_path = dest_folder / new_name

            if not dest_path.exists():
                logger.debug(f"Collision detected, using: {new_name}")
                return dest_path

            counter += 1

            # Safety check to prevent infinite loop
            if counter > 1000:
                raise ValueError(f"Could not find unique name for {filename}")

    def _is_file_locked(self, file_path: Path) -> bool:
        """
        Check if a file is locked or in use.

        Args:
            file_path: Path to check

        Returns:
            True if file is locked, False otherwise
        """
        try:
            # Try to open the file in exclusive mode
            with open(file_path, 'r+b') as f:
                pass
            return False
        except (IOError, OSError, PermissionError):
            return True

    def get_organization_preview(self) -> str:
        """
        Get a human-readable preview of what will be organized.

        Returns:
            Formatted string showing files grouped by category
        """
        categorized_files = self.scan_files(dry_run=True)

        if not categorized_files:
            return "No files to organize (all files are recent or in disabled categories)"

        total_files = sum(len(files) for files in categorized_files.values())
        preview_lines = [f"\nPreview: {total_files} files will be organized\n"]

        for category in sorted(categorized_files.keys()):
            files = categorized_files[category]
            folder_name = self.config.get_destination_folder_name(category)

            preview_lines.append(f"{category} ({len(files)} files):")
            preview_lines.append(f"  → {folder_name}/")

            # Show first 5 files, then "..." if more
            for file_path in files[:5]:
                file_size = file_path.stat().st_size
                size_str = self._format_file_size(file_size) if file_size > 1024 * 1024 else ""

                if size_str:
                    preview_lines.append(f"    • {file_path.name} ({size_str})")
                else:
                    preview_lines.append(f"    • {file_path.name}")

            if len(files) > 5:
                preview_lines.append(f"    ... and {len(files) - 5} more")

            preview_lines.append("")  # Blank line between categories

        return "\n".join(preview_lines)

    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted string (e.g., "152 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.0f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.0f} TB"

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about current Downloads folder state.

        Returns:
            Dictionary with statistics
        """
        categorized_files = self.scan_files(dry_run=True)

        stats = {
            "total_files_to_organize": sum(len(files) for files in categorized_files.values()),
            "categories_with_files": len(categorized_files),
        }

        # Add per-category counts
        for category, files in categorized_files.items():
            stats[f"category_{category.lower()}"] = len(files)

        return stats
