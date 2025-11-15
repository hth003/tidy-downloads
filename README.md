# TidyDownloads

A lightweight macOS tool that automatically organizes your Downloads folder.

## Overview

TidyDownloads keeps your Downloads folder clean by automatically categorizing files into organized subfolders based on file type. It's designed to be hands-off, predictable, and safe.

## Features (Phase 1 - CLI MVP)

-  **Smart File Categorization**: Automatically sorts files into 8 categories (Documents, Images, Videos, Audio, Archives, Code, Installers, Other)
-  **Preview Mode**: See what will be organized before making changes
-  **Undo Support**: Restore files to their original locations
-  **Configurable**: Set minimum file age and enable/disable categories
-  **Safe**: Never deletes files, only moves them

## Installation (Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/tidy-downloads.git
cd tidy-downloads

# Install with uv
uv sync

# Run the CLI
uv run tidy-downloads --help
```

## Usage

```bash
# Preview what will be organized
uv run tidy-downloads --preview

# Organize files in Downloads folder
uv run tidy-downloads --organize

# Undo the last organization
uv run tidy-downloads --undo

# Show current configuration
uv run tidy-downloads --config
```

## Configuration

Configuration is stored in `~/Library/Application Support/TidyDownloads/config.json`.

Default settings:
- **Minimum file age**: 7 days (files newer than this are not touched)
- **Downloads path**: ~/Downloads
- **All categories enabled**

## File Categories

| Category | File Types |
|----------|------------|
| Installers | .dmg, .pkg, .app |
| Documents | .pdf, .doc, .docx, .txt, .rtf, .pages, .xlsx, .csv, .ppt |
| Images | .jpg, .jpeg, .png, .gif, .svg, .heic, .webp |
| Videos | .mp4, .mov, .avi, .mkv, .webm |
| Audio | .mp3, .m4a, .wav, .aac, .flac |
| Archives | .zip, .rar, .7z, .tar, .gz |
| Code | .json, .yaml, .xml, .py, .js, .swift |
| Other | All other file types |

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/tidy_downloads

# Run specific test
uv run pytest tests/test_config_manager.py
```

## Project Status

=á **Phase 1 - In Progress**: Core organization engine (CLI)

See [project_plan.md](project_plan.md) for the complete roadmap.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

This project is currently in early development. Contributions welcome after Phase 1 is complete!
