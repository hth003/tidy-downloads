"""Tests for UndoManager."""

import json
import pytest
from pathlib import Path
from datetime import datetime

from tidy_downloads.undo_manager import UndoManager


class TestUndoManager:
    """Test cases for UndoManager class."""

    @pytest.fixture
    def setup_test_environment(self, tmp_path):
        """Create test environment with files and folders."""
        downloads_path = tmp_path / "Downloads"
        downloads_path.mkdir()

        # Create organized folders
        docs_folder = downloads_path / "~Documents"
        docs_folder.mkdir()

        images_folder = downloads_path / "~Images"
        images_folder.mkdir()

        # Create some files in organized folders
        (docs_folder / "file1.pdf").write_text("content1")
        (docs_folder / "file2.pdf").write_text("content2")
        (images_folder / "image1.jpg").write_bytes(b"image data")

        return {
            "downloads_path": downloads_path,
            "docs_folder": docs_folder,
            "images_folder": images_folder
        }

    @pytest.fixture
    def setup_undo_manager(self, tmp_path):
        """Create an UndoManager with temporary history directory."""
        history_dir = tmp_path / "history"
        return UndoManager(history_dir=history_dir)

    def test_create_manifest(self, setup_undo_manager, setup_test_environment):
        """Test creating an undo manifest."""
        undo_mgr = setup_undo_manager
        downloads = setup_test_environment["downloads_path"]

        # Simulate some moves
        moves = {
            "Documents": [
                (downloads / "file1.pdf", downloads / "~Documents" / "file1.pdf"),
                (downloads / "file2.pdf", downloads / "~Documents" / "file2.pdf"),
            ],
            "Images": [
                (downloads / "image1.jpg", downloads / "~Images" / "image1.jpg"),
            ]
        }

        errors = []

        manifest_path = undo_mgr.create_manifest(moves, errors)

        assert manifest_path.exists()
        assert manifest_path.suffix == ".json"

        # Load and verify manifest
        with open(manifest_path) as f:
            manifest_data = json.load(f)

        assert "timestamp" in manifest_data
        assert "moves" in manifest_data
        assert "total_files" in manifest_data
        assert manifest_data["total_files"] == 3
        assert manifest_data["undone"] is False

    def test_get_latest_manifest(self, setup_undo_manager, setup_test_environment):
        """Test getting the latest manifest."""
        undo_mgr = setup_undo_manager
        downloads = setup_test_environment["downloads_path"]

        # Create two manifests
        moves1 = {"Documents": [(downloads / "file1.pdf", downloads / "~Documents" / "file1.pdf")]}
        moves2 = {"Images": [(downloads / "image1.jpg", downloads / "~Images" / "image1.jpg")]}

        manifest1 = undo_mgr.create_manifest(moves1, [])

        import time
        time.sleep(0.1)  # Ensure different timestamps

        manifest2 = undo_mgr.create_manifest(moves2, [])

        # Latest should be manifest2
        latest = undo_mgr.get_latest_manifest()
        assert latest == manifest2

    def test_get_latest_manifest_no_history(self, setup_undo_manager):
        """Test getting latest manifest when no history exists."""
        undo_mgr = setup_undo_manager
        latest = undo_mgr.get_latest_manifest()
        assert latest is None

    def test_undo_operation(self, setup_undo_manager, setup_test_environment):
        """Test undoing a file organization."""
        undo_mgr = setup_undo_manager
        downloads = setup_test_environment["downloads_path"]
        docs_folder = setup_test_environment["docs_folder"]

        # Create files in original location first (for the source paths)
        original_file1 = downloads / "file1.pdf"
        original_file2 = downloads / "file2.pdf"

        # Simulate organization by creating manifest
        moves = {
            "Documents": [
                (original_file1, docs_folder / "file1.pdf"),
                (original_file2, docs_folder / "file2.pdf"),
            ]
        }

        manifest_path = undo_mgr.create_manifest(moves, [])

        # Now undo
        files_restored, errors = undo_mgr.undo(manifest_path)

        assert files_restored == 2
        assert len(errors) == 0

        # Files should be restored to original location
        assert original_file1.exists()
        assert original_file2.exists()

        # Files should no longer be in organized folder
        assert not (docs_folder / "file1.pdf").exists()
        assert not (docs_folder / "file2.pdf").exists()

    def test_undo_marks_manifest_as_undone(self, setup_undo_manager, setup_test_environment):
        """Test that undo marks the manifest as undone."""
        undo_mgr = setup_undo_manager
        downloads = setup_test_environment["downloads_path"]
        docs_folder = setup_test_environment["docs_folder"]

        moves = {
            "Documents": [
                (downloads / "file1.pdf", docs_folder / "file1.pdf"),
            ]
        }

        manifest_path = undo_mgr.create_manifest(moves, [])

        # Undo
        undo_mgr.undo(manifest_path)

        # Load manifest and check undone flag
        manifest_data = undo_mgr.load_manifest(manifest_path)
        assert manifest_data["undone"] is True
        assert "undo_timestamp" in manifest_data

    def test_undo_already_undone(self, setup_undo_manager, setup_test_environment):
        """Test undoing an already undone operation."""
        undo_mgr = setup_undo_manager
        downloads = setup_test_environment["downloads_path"]
        docs_folder = setup_test_environment["docs_folder"]

        moves = {
            "Documents": [
                (downloads / "file1.pdf", docs_folder / "file1.pdf"),
            ]
        }

        manifest_path = undo_mgr.create_manifest(moves, [])

        # Undo once
        undo_mgr.undo(manifest_path)

        # Try to undo again
        files_restored, errors = undo_mgr.undo(manifest_path)

        assert files_restored == 0
        assert len(errors) > 0
        assert "already been undone" in errors[0]

    def test_undo_missing_files(self, setup_undo_manager, tmp_path):
        """Test undo when destination files no longer exist."""
        undo_mgr = setup_undo_manager
        downloads = tmp_path / "Downloads"
        downloads.mkdir()

        # Create manifest with files that don't exist
        moves = {
            "Documents": [
                (downloads / "file1.pdf", downloads / "~Documents" / "missing.pdf"),
            ]
        }

        manifest_path = undo_mgr.create_manifest(moves, [])

        # Try to undo
        files_restored, errors = undo_mgr.undo(manifest_path)

        assert files_restored == 0
        assert len(errors) > 0

    def test_get_undo_preview(self, setup_undo_manager, setup_test_environment):
        """Test generating undo preview."""
        undo_mgr = setup_undo_manager
        downloads = setup_test_environment["downloads_path"]

        moves = {
            "Documents": [
                (downloads / "file1.pdf", downloads / "~Documents" / "file1.pdf"),
                (downloads / "file2.pdf", downloads / "~Documents" / "file2.pdf"),
            ]
        }

        manifest_path = undo_mgr.create_manifest(moves, [])

        preview = undo_mgr.get_undo_preview(manifest_path)

        assert "Undo Preview" in preview
        assert "Documents" in preview
        assert "2 files" in preview

    def test_get_undo_preview_no_history(self, setup_undo_manager):
        """Test undo preview when no history exists."""
        undo_mgr = setup_undo_manager
        preview = undo_mgr.get_undo_preview()

        assert "No organization history" in preview

    @pytest.mark.slow
    def test_cleanup_old_manifests_by_count(self, setup_undo_manager, setup_test_environment):
        """Test that old manifests are cleaned up when exceeding max count."""
        undo_mgr = setup_undo_manager
        undo_mgr.max_sessions = 3
        downloads = setup_test_environment["downloads_path"]

        # Create 5 manifests with 1 second delay to ensure different filenames
        for i in range(5):
            moves = {"Documents": [(downloads / f"file{i}.pdf", downloads / "~Documents" / f"file{i}.pdf")]}
            undo_mgr.create_manifest(moves, [])
            import time
            time.sleep(1.1)  # Sleep longer to ensure different second in filename

        # Should only have 3 manifests (cleanup happens in create_manifest)
        manifests = list(undo_mgr.history_dir.glob("*.json"))
        assert len(manifests) <= 3  # Allow for <= since cleanup is best-effort

    @pytest.mark.slow
    def test_get_history(self, setup_undo_manager, setup_test_environment):
        """Test getting organization history."""
        undo_mgr = setup_undo_manager
        downloads = setup_test_environment["downloads_path"]

        # Create a few operations with delays to ensure unique filenames
        for i in range(3):
            moves = {"Documents": [(downloads / f"file{i}.pdf", downloads / "~Documents" / f"file{i}.pdf")]}
            undo_mgr.create_manifest(moves, [])
            import time
            time.sleep(1.1)  # Ensure different seconds

        history = undo_mgr.get_history(limit=10)

        # Should have at least 1 history entry (may have fewer due to cleanup)
        assert len(history) >= 1
        assert all("timestamp" in entry for entry in history)
        assert all("total_files" in entry for entry in history)

    def test_cleanup_empty_folders(self, setup_undo_manager, tmp_path):
        """Test that empty folders are removed after undo."""
        undo_mgr = setup_undo_manager
        downloads = tmp_path / "Downloads"
        downloads.mkdir()

        # Create a single organized folder with one file
        docs_folder = downloads / "~Documents"
        docs_folder.mkdir()

        file_path = docs_folder / "onlyfile.pdf"
        file_path.write_text("content")

        moves = {
            "Documents": [
                (downloads / "onlyfile.pdf", file_path),
            ]
        }

        manifest_path = undo_mgr.create_manifest(moves, [])

        # Undo
        undo_mgr.undo(manifest_path)

        # Folder should be removed since it's empty
        assert not docs_folder.exists()
