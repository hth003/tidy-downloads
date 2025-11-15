"""Tests for ConfigManager."""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from tidy_downloads.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def test_default_config_creation(self, tmp_path):
        """Test that default configuration is created if no config file exists."""
        config_path = tmp_path / "config.json"
        config = ConfigManager(config_path=config_path)

        assert config_path.exists()
        assert config.get("minimum_file_age_days") == 7
        assert config.get("downloads_path") == str(Path.home() / "Downloads")
        assert len(config.get("enabled_categories")) == 8

    def test_load_existing_config(self, tmp_path):
        """Test loading an existing configuration file."""
        config_path = tmp_path / "config.json"

        # Create a custom config
        custom_config = {
            "minimum_file_age_days": 14,
            "downloads_path": "/custom/path",
            "enabled_categories": ["Documents", "Images"],
            "send_notifications": False
        }

        with open(config_path, 'w') as f:
            json.dump(custom_config, f)

        config = ConfigManager(config_path=config_path)

        assert config.get("minimum_file_age_days") == 14
        assert config.get("downloads_path") == "/custom/path"
        assert len(config.get("enabled_categories")) == 2
        assert config.get("send_notifications") is False

    def test_invalid_json_fallback_to_defaults(self, tmp_path):
        """Test that invalid JSON falls back to defaults."""
        config_path = tmp_path / "config.json"

        # Write invalid JSON
        with open(config_path, 'w') as f:
            f.write("{invalid json content")

        config = ConfigManager(config_path=config_path)

        # Should fall back to defaults
        assert config.get("minimum_file_age_days") == 7

    def test_get_category_for_extension(self, tmp_path):
        """Test file extension categorization."""
        config = ConfigManager(config_path=tmp_path / "config.json")

        assert config.get_category_for_extension(".pdf") == "Documents"
        assert config.get_category_for_extension(".PDF") == "Documents"  # Case insensitive
        assert config.get_category_for_extension(".jpg") == "Images"
        assert config.get_category_for_extension(".mp4") == "Videos"
        assert config.get_category_for_extension(".zip") == "Archives"
        assert config.get_category_for_extension(".py") == "Code"
        assert config.get_category_for_extension(".dmg") == "Installers"
        assert config.get_category_for_extension(".mp3") == "Audio"
        assert config.get_category_for_extension(".unknown") == "Other"

    def test_get_destination_folder_name(self, tmp_path):
        """Test destination folder name generation."""
        config = ConfigManager(config_path=tmp_path / "config.json")

        assert config.get_destination_folder_name("Documents") == "~Documents"
        assert config.get_destination_folder_name("Images") == "~Images"

    def test_is_category_enabled(self, tmp_path):
        """Test category enabled check."""
        config_path = tmp_path / "config.json"
        config = ConfigManager(config_path=config_path)

        # Disable some categories
        config.set("enabled_categories", ["Documents", "Images"])

        assert config.is_category_enabled("Documents") is True
        assert config.is_category_enabled("Images") is True
        assert config.is_category_enabled("Videos") is False

    def test_validate_minimum_file_age(self, tmp_path):
        """Test validation of minimum file age."""
        config_path = tmp_path / "config.json"
        config = ConfigManager(config_path=config_path)

        # Set invalid value
        config.config["minimum_file_age_days"] = -1
        config.validate()

        # Should be reset to default
        assert config.get("minimum_file_age_days") == 7

    def test_validate_invalid_categories(self, tmp_path):
        """Test validation removes invalid categories."""
        config_path = tmp_path / "config.json"
        config = ConfigManager(config_path=config_path)

        # Add invalid categories
        config.config["enabled_categories"] = ["Documents", "InvalidCategory", "Images"]
        config.validate()

        # Invalid category should be removed
        enabled = config.get("enabled_categories")
        assert "Documents" in enabled
        assert "Images" in enabled
        assert "InvalidCategory" not in enabled

    def test_reset_to_defaults(self, tmp_path):
        """Test resetting configuration to defaults."""
        config_path = tmp_path / "config.json"
        config = ConfigManager(config_path=config_path)

        # Modify config
        config.set("minimum_file_age_days", 30)

        # Reset
        config.reset_to_defaults()

        assert config.get("minimum_file_age_days") == 7

    def test_set_and_get(self, tmp_path):
        """Test setting and getting configuration values."""
        config_path = tmp_path / "config.json"
        config = ConfigManager(config_path=config_path)

        config.set("minimum_file_age_days", 10)

        assert config.get("minimum_file_age_days") == 10

        # Reload from file to ensure persistence
        config2 = ConfigManager(config_path=config_path)
        assert config2.get("minimum_file_age_days") == 10

    def test_to_dict(self, tmp_path):
        """Test converting config to dictionary."""
        config = ConfigManager(config_path=tmp_path / "config.json")

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "minimum_file_age_days" in config_dict
        assert "enabled_categories" in config_dict
