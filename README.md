# TidyDownloads

A lightweight macOS tool that automatically organizes your Downloads folder.

## Overview

TidyDownloads keeps your Downloads folder clean by automatically categorizing files into organized subfolders based on file type. It's designed to be hands-off, predictable, and safe.

## Features

### Menu Bar App (Phase 2) ✨
-  **Native macOS Integration**: Clean menu bar icon (🗂️) for quick access
-  **Real-time Status**: Shows count of files ready to organize
-  **One-Click Organization**: Preview and organize with confirmation dialogs
-  **Undo Functionality**: Easily restore files to original locations
-  **Visual Notifications**: macOS native notifications for operations
-  **Statistics Dashboard**: View file counts by category
-  **Configuration Display**: Easy access to current settings

### Core Capabilities (Phase 1)
-  **Smart File Categorization**: Automatically sorts files into 8 categories (Documents, Images, Videos, Audio, Archives, Code, Installers, Other)
-  **Preview Mode**: See what will be organized before making changes
-  **Full Undo Support**: Restore files to their original locations with complete history
-  **Configurable**: Set minimum file age and enable/disable categories
-  **Safe**: Never deletes files, only moves them

## Installation (Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/tidy-downloads.git
cd tidy-downloads

# Install with uv
uv sync

# Run the menu bar app
uv run tidy-downloads-app

# Or run the CLI
uv run tidy-downloads --help
```

## Usage

### Menu Bar App (Recommended)

```bash
# Launch the menu bar application
uv run tidy-downloads-app
```

The menu bar app provides a user-friendly GUI with:
- 🗂️ Menu bar icon for quick access
- Real-time status updates showing files ready to organize
- One-click organization with preview and confirmation
- Easy undo functionality
- Configuration and statistics display
- macOS native notifications

### Command Line Interface (CLI)

```bash
# Preview what will be organized
uv run tidy-downloads --preview

# Organize files in Downloads folder
uv run tidy-downloads --organize

# Undo the last organization
uv run tidy-downloads --undo

# Show current configuration
uv run tidy-downloads --config

# Show statistics about your Downloads folder
uv run tidy-downloads --stats

# Show organization history
uv run tidy-downloads --history

# Skip confirmation prompts
uv run tidy-downloads --organize --yes
```

## Configuration

Configuration is stored in `~/Library/Application Support/TidyDownloads/config.json`.

Default settings:
- **Minimum file age**: 7 days (files newer than this are not touched)
- **Downloads path**: ~/Downloads
- **All categories enabled**
- **Tilde prefix**: Category folders named `~Documents`, `~Images`, etc. (sorts to bottom in Finder)

## File Categories

| Category | File Types | Folder Name |
|----------|------------|-------------|
| Installers | .dmg, .pkg, .app, .mpkg | ~Installers |
| Documents | .pdf, .doc, .docx, .txt, .rtf, .pages, .xlsx, .csv, .ppt | ~Documents |
| Images | .jpg, .jpeg, .png, .gif, .svg, .heic, .webp | ~Images |
| Videos | .mp4, .mov, .avi, .mkv, .webm | ~Videos |
| Audio | .mp3, .m4a, .wav, .aac, .flac | ~Audio |
| Archives | .zip, .rar, .7z, .tar, .gz | ~Archives |
| Code | .json, .yaml, .xml, .py, .js, .swift, .md | ~Code |
| Other | All other file types | ~Other |

## How It Works

1. **Scan**: TidyDownloads scans your Downloads folder for files older than the minimum age (default: 7 days)
2. **Categorize**: Files are categorized based on their extension using 70+ recognized file types
3. **Organize**: Files are moved to category folders with the `~` prefix (e.g., `~Documents`, `~Images`)
4. **Manifest**: Every operation is recorded for complete undo capability
5. **Undo**: Restore files to their exact original locations anytime

### Safety Features
- **Age Filter**: Only processes files older than configured age (default: 7 days)
- **Skip Hidden Files**: Files starting with `.` are ignored
- **Skip Directories**: User-created folders are never touched
- **Lock Detection**: Won't move files currently in use
- **Atomic Operations**: Uses safe file operations - never deletes files
- **Collision Handling**: Appends `_2`, `_3`, etc. when destination file exists
- **Full Undo**: Every operation can be reversed via manifest-based restoration

## Development

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/tidy_downloads

# Run specific test file
uv run pytest tests/test_config_manager.py

# Run specific test
uv run pytest tests/test_organizer.py::test_scan_files
```

### Test Coverage
-  **ConfigManager**: 11 tests covering load/save/validation/category mapping
-  **FileOrganizer**: 12 tests covering scan/organize/preview/collision handling
-  **UndoManager**: 10 tests covering manifest creation/restoration/cleanup

### Performance Benchmarks
-  **Scan**: < 0.1s for 100 files
-  **Organize**: < 0.2s for 100 files
-  **Memory**: ~15-20MB
-  **Test suite**: ~0.16s total execution time

## Project Status

✅ **Phase 1 - Complete**: Core organization engine with CLI
✅ **Phase 2 - Complete**: Native macOS menu bar application
📋 **Phase 3 - Planned**: Distribution packaging (py2app, launchd scheduling, code signing)

See [project_plan.md](project_plan.md) for the complete roadmap.

## Architecture

The codebase follows a modular architecture with clean separation of concerns:

-  **ConfigManager** (`config_manager.py`): Configuration persistence and validation
-  **FileOrganizer** (`organizer.py`): Core file scanning and categorization logic
-  **UndoManager** (`undo_manager.py`): Manifest-based undo system with history
-  **CLI** (`cli.py`): Command-line interface
-  **App** (`app.py`): Menu bar application using rumps

All business logic is shared between CLI and GUI - the menu bar app is a thin wrapper around core modules.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
