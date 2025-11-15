"""Configuration management for TidyDownloads."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration with sensible defaults."""

    # Default configuration values
    DEFAULT_CONFIG = {
        "minimum_file_age_days": 7,
        "downloads_path": str(Path.home() / "Downloads"),
        "enabled_categories": [
            "Installers",
            "Documents",
            "Images",
            "Videos",
            "Audio",
            "Archives",
            "Code",
            "Other"
        ],
        "send_notifications": True,
    }

    # File type mappings - organized by category
    CATEGORY_MAPPINGS = {
        "Installers": (
            ".dmg", ".pkg", ".app", ".mpkg"
        ),
        "Documents": (
            ".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt",
            ".xls", ".xlsx", ".csv", ".numbers",
            ".ppt", ".pptx", ".keynote", ".pages"
        ),
        "Images": (
            ".jpg", ".jpeg", ".png", ".gif", ".svg", ".heic",
            ".webp", ".bmp", ".tiff", ".ico"
        ),
        "Videos": (
            ".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv",
            ".wmv", ".m4v", ".mpg", ".mpeg"
        ),
        "Audio": (
            ".mp3", ".m4a", ".wav", ".aac", ".flac", ".ogg",
            ".wma", ".opus"
        ),
        "Archives": (
            ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2",
            ".xz", ".tgz"
        ),
        "Code": (
            ".json", ".yaml", ".yml", ".xml", ".toml",
            ".py", ".js", ".ts", ".tsx", ".jsx", ".swift", ".java", ".cpp",
            ".c", ".h", ".go", ".rs", ".rb", ".php",
            ".md", ".rst", ".sh", ".bash"
        ),
        "Other": ()  # Catch-all for unrecognized types
    }

    # Folder name prefix - tilde (~) sorts to bottom in Finder
    FOLDER_PREFIX = "~"

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Optional custom path to config file.
                        Defaults to ~/Library/Application Support/TidyDownloads/config.json
        """
        if config_path is None:
            app_support = Path.home() / "Library" / "Application Support" / "TidyDownloads"
            self.config_path = app_support / "config.json"
        else:
            self.config_path = Path(config_path)

        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file, creating with defaults if not exists."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)

                # Merge with defaults (in case new keys were added)
                self.config = {**self.DEFAULT_CONFIG, **loaded_config}
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.info("No configuration file found, using defaults")
                self.config = self.DEFAULT_CONFIG.copy()
                self.save()  # Create default config file

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            logger.info("Falling back to default configuration")
            self.config = self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config = self.DEFAULT_CONFIG.copy()

    def save(self) -> None:
        """Save current configuration to file."""
        try:
            # Create parent directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)

            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value and save to file.

        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value
        self.save()

    def get_downloads_path(self) -> Path:
        """Get the Downloads folder path as a Path object."""
        return Path(self.config["downloads_path"]).expanduser()

    def get_minimum_file_age_days(self) -> int:
        """Get the minimum file age in days."""
        return self.config["minimum_file_age_days"]

    def get_enabled_categories(self) -> List[str]:
        """Get list of enabled categories."""
        return self.config["enabled_categories"]

    def is_category_enabled(self, category: str) -> bool:
        """Check if a category is enabled."""
        return category in self.config["enabled_categories"]

    def get_category_for_extension(self, extension: str) -> Optional[str]:
        """
        Get the category for a given file extension.

        Args:
            extension: File extension (e.g., '.pdf', '.jpg')

        Returns:
            Category name or None if not found in any category
        """
        extension = extension.lower()

        for category, extensions in self.CATEGORY_MAPPINGS.items():
            if extension in extensions:
                return category

        # Default to "Other" for unknown extensions
        return "Other"

    def get_destination_folder_name(self, category: str) -> str:
        """
        Get the destination folder name for a category.

        Args:
            category: Category name

        Returns:
            Folder name with prefix (e.g., '~Documents')
        """
        return f"{self.FOLDER_PREFIX}{category}"

    def validate(self) -> bool:
        """
        Validate the current configuration.

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check minimum file age is positive
            if self.config["minimum_file_age_days"] < 1:
                logger.warning("minimum_file_age_days must be >= 1, resetting to default")
                self.config["minimum_file_age_days"] = self.DEFAULT_CONFIG["minimum_file_age_days"]

            # Check downloads path exists
            downloads_path = self.get_downloads_path()
            if not downloads_path.exists():
                logger.warning(f"Downloads path does not exist: {downloads_path}")
                return False

            # Check enabled categories are valid
            valid_categories = set(self.CATEGORY_MAPPINGS.keys())
            enabled = set(self.config["enabled_categories"])

            invalid_categories = enabled - valid_categories
            if invalid_categories:
                logger.warning(f"Invalid categories removed: {invalid_categories}")
                self.config["enabled_categories"] = list(enabled & valid_categories)

            return True

        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
        logger.info("Configuration reset to defaults")

    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"ConfigManager(config_path={self.config_path})"

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self.config.copy()
