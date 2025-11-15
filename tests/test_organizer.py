"""Tests for FileOrganizer."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

from tidy_downloads.config_manager import ConfigManager
from tidy_downloads.organizer import FileOrganizer


class TestFileOrganizer:
    """Test cases for FileOrganizer class."""

    @pytest.fixture
    def setup_test_downloads(self, tmp_path):
        """Create a temporary Downloads folder with test files."""
        downloads_path = tmp_path / "Downloads"
        downloads_path.mkdir()

        # Create test files with different ages
        recent_file = downloads_path / "recent.pdf"
        recent_file.write_text("recent content")

        old_pdf = downloads_path / "old_document.pdf"
        old_pdf.write_text("old pdf content")

        old_jpg = downloads_path / "old_image.jpg"
        old_jpg.write_bytes(b"fake jpg data")

        old_dmg = downloads_path / "installer.dmg"
        old_dmg.write_bytes(b"fake dmg data")

        # Make some files old (8 days ago)
        eight_days_ago = datetime.now() - timedelta(days=8)
        old_timestamp = eight_days_ago.timestamp()

        import os
        os.utime(old_pdf, (old_timestamp, old_timestamp))
        os.utime(old_jpg, (old_timestamp, old_timestamp))
        os.utime(old_dmg, (old_timestamp, old_timestamp))

        # Create a user folder (should be ignored)
        user_folder = downloads_path / "MyFolder"
        user_folder.mkdir()

        # Create hidden file (should be ignored)
        hidden_file = downloads_path / ".hidden"
        hidden_file.write_text("hidden content")

        return downloads_path

    @pytest.fixture
    def setup_config(self, tmp_path, setup_test_downloads):
        """Create a ConfigManager with test downloads path."""
        config_path = tmp_path / "config.json"
        config = ConfigManager(config_path=config_path)
        config.set("downloads_path", str(setup_test_downloads))
        return config

    def test_scan_files_with_age_filter(self, setup_config):
        """Test that scan_files only returns old files."""
        organizer = FileOrganizer(setup_config)
        categorized = organizer.scan_files()

        # Should find 3 old files (old_document.pdf, old_image.jpg, installer.dmg)
        total_files = sum(len(files) for files in categorized.values())
        assert total_files == 3

        # Check categories
        assert "Documents" in categorized
        assert "Images" in categorized
        assert "Installers" in categorized

    def test_scan_files_ignores_folders(self, setup_config):
        """Test that scan ignores user-created folders."""
        organizer = FileOrganizer(setup_config)
        categorized = organizer.scan_files()

        # No folder should be in the results
        for files in categorized.values():
            for file_path in files:
                assert file_path.is_file()

    def test_scan_files_ignores_hidden_files(self, setup_config):
        """Test that scan ignores hidden files."""
        organizer = FileOrganizer(setup_config)
        categorized = organizer.scan_files()

        # Hidden file should not be in results
        for files in categorized.values():
            for file_path in files:
                assert not file_path.name.startswith('.')

    def test_organize_dry_run(self, setup_config):
        """Test organize in dry-run mode doesn't move files."""
        organizer = FileOrganizer(setup_config)
        downloads_path = setup_config.get_downloads_path()

        # Count files before
        files_before = list(downloads_path.glob("*.pdf")) + list(downloads_path.glob("*.jpg"))

        # Dry run
        moves, errors = organizer.organize(dry_run=True)

        # Files should still be in Downloads
        files_after = list(downloads_path.glob("*.pdf")) + list(downloads_path.glob("*.jpg"))
        assert len(files_before) == len(files_after)

        # Should have move information
        assert len(moves) > 0

    def test_organize_creates_folders(self, setup_config):
        """Test that organize creates category folders."""
        organizer = FileOrganizer(setup_config)
        downloads_path = setup_config.get_downloads_path()

        organizer.organize(dry_run=False)

        # Check that folders were created
        assert (downloads_path / "~Documents").exists()
        assert (downloads_path / "~Images").exists()
        assert (downloads_path / "~Installers").exists()

    def test_organize_moves_files(self, setup_config):
        """Test that organize actually moves files."""
        organizer = FileOrganizer(setup_config)
        downloads_path = setup_config.get_downloads_path()

        moves, errors = organizer.organize(dry_run=False)

        # Check files were moved
        assert (downloads_path / "~Documents" / "old_document.pdf").exists()
        assert (downloads_path / "~Images" / "old_image.jpg").exists()
        assert (downloads_path / "~Installers" / "installer.dmg").exists()

        # Original files should no longer exist in Downloads
        assert not (downloads_path / "old_document.pdf").exists()
        assert not (downloads_path / "old_image.jpg").exists()

    def test_collision_handling(self, setup_config):
        """Test that file name collisions are handled."""
        organizer = FileOrganizer(setup_config)
        downloads_path = setup_config.get_downloads_path()

        # Create category folder with existing file
        docs_folder = downloads_path / "~Documents"
        docs_folder.mkdir()
        (docs_folder / "old_document.pdf").write_text("existing file")

        # Organize (should create old_document_2.pdf)
        moves, errors = organizer.organize(dry_run=False)

        # Check that both files exist
        assert (docs_folder / "old_document.pdf").exists()
        assert (docs_folder / "old_document_2.pdf").exists()

    def test_get_organization_preview(self, setup_config):
        """Test preview generation with enhanced formatting."""
        organizer = FileOrganizer(setup_config)
        preview = organizer.get_organization_preview()

        # Check for enhanced preview header with summary
        assert "📊 Ready to organize" in preview
        assert "files" in preview

        # Check for visual separators
        assert "──" in preview

        # Check for category icons and names
        assert "📄 DOCUMENTS" in preview
        assert "🖼️ IMAGES" in preview
        assert "📦 INSTALLERS" in preview

        # Check for file listing
        assert "old_document.pdf" in preview

        # Check for footer with file age info
        assert "⏱️" in preview
        assert "days old" in preview

    def test_get_stats(self, setup_config):
        """Test statistics generation."""
        organizer = FileOrganizer(setup_config)
        stats = organizer.get_stats()

        assert "total_files_to_organize" in stats
        assert stats["total_files_to_organize"] == 3
        assert "categories_with_files" in stats

    def test_disabled_categories_are_skipped(self, setup_config, tmp_path):
        """Test that disabled categories are not organized."""
        # Disable Images category
        setup_config.set("enabled_categories", ["Documents", "Installers"])

        organizer = FileOrganizer(setup_config)
        categorized = organizer.scan_files()

        # Should not have Images category
        assert "Images" not in categorized
        assert "Documents" in categorized

    def test_organize_with_no_files(self, tmp_path):
        """Test organize when there are no files to organize."""
        downloads_path = tmp_path / "Downloads"
        downloads_path.mkdir()

        config_path = tmp_path / "config.json"
        config = ConfigManager(config_path=config_path)
        config.set("downloads_path", str(downloads_path))

        organizer = FileOrganizer(config)
        moves, errors = organizer.organize()

        assert len(moves) == 0
        assert len(errors) == 0

    def test_format_file_size(self, setup_config):
        """Test file size formatting."""
        organizer = FileOrganizer(setup_config)

        assert organizer._format_file_size(500) == "500 B"
        assert organizer._format_file_size(1500) == "1 KB"
        assert organizer._format_file_size(1500000) == "1 MB"
        assert organizer._format_file_size(1500000000) == "1 GB"

    def test_get_category_icon(self, setup_config):
        """Test category icon mapping."""
        organizer = FileOrganizer(setup_config)

        # Test all known categories have icons
        assert organizer._get_category_icon('Installers') == '📦'
        assert organizer._get_category_icon('Documents') == '📄'
        assert organizer._get_category_icon('Images') == '🖼️'
        assert organizer._get_category_icon('Videos') == '🎥'
        assert organizer._get_category_icon('Audio') == '🎵'
        assert organizer._get_category_icon('Archives') == '📦'
        assert organizer._get_category_icon('Code') == '💻'
        assert organizer._get_category_icon('Other') == '📎'

        # Test unknown category returns default
        assert organizer._get_category_icon('Unknown') == '📎'

    def test_calculate_total_size(self, setup_config, tmp_path):
        """Test total size calculation across categories."""
        # Create test files with known sizes
        downloads_path = tmp_path / "Downloads"
        downloads_path.mkdir(exist_ok=True)  # May already exist from fixture

        # Create files with specific content sizes
        file1 = downloads_path / "test1.pdf"
        file1.write_text("a" * 1000)  # 1000 bytes

        file2 = downloads_path / "test2.jpg"
        file2.write_text("b" * 2000)  # 2000 bytes

        file3 = downloads_path / "test3.dmg"
        file3.write_text("c" * 500)  # 500 bytes

        # Make files old enough to organize
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        import os
        os.utime(file1, (old_time, old_time))
        os.utime(file2, (old_time, old_time))
        os.utime(file3, (old_time, old_time))

        organizer = FileOrganizer(setup_config)
        categorized_files = organizer.scan_files(dry_run=True)

        total_size = organizer._calculate_total_size(categorized_files)

        # Should include at least our 3 files (3500 bytes)
        # May include fixture files too, so check it's at least what we expect
        assert total_size >= 3500

        # Verify it's calculating correctly by checking individual file sizes
        all_files = [f for files in categorized_files.values() for f in files]
        manual_total = sum(f.stat().st_size for f in all_files)
        assert total_size == manual_total  # Should match manual calculation
