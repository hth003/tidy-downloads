# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TidyDownloads** is a macOS tool that automatically organizes the Downloads folder by categorizing files into organized subfolders. The project has completed **Phase 1** (CLI tool) and **Phase 2** (Menu bar app). Future phases will add scheduling and distribution packaging.

**Architecture:** The codebase follows a modular architecture with five core modules:
- **ConfigManager** (`config_manager.py`): Handles configuration persistence, category mappings, and validation
- **FileOrganizer** (`organizer.py`): Core file scanning, categorization, and movement logic
- **UndoManager** (`undo_manager.py`): Manifest-based undo system with history tracking
- **CLI** (`cli.py`): Command-line interface for terminal usage
- **App** (`app.py`): Menu bar application using rumps (NEW in Phase 2)

## Development Commands

### Running the Menu Bar App
```bash
# Use uv to run all commands - DO NOT use pip
uv run tidy-downloads-app             # Launch menu bar application

# The menu bar app provides:
# - 🗂️ icon in macOS menu bar
# - Real-time status showing files ready to organize
# - All CLI functions via GUI (organize, preview, undo, config, stats)
# - macOS notifications for operations
```

### Running the CLI
```bash
uv run tidy-downloads --help          # Show all available commands
uv run tidy-downloads --preview       # Preview what will be organized
uv run tidy-downloads --organize      # Organize files (with confirmation)
uv run tidy-downloads --undo          # Undo last organization
uv run tidy-downloads --config        # Show current configuration
uv run tidy-downloads --stats         # Show statistics
uv run tidy-downloads --history       # Show operation history
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/tidy_downloads

# Run specific test file
uv run pytest tests/test_config_manager.py

# Run specific test function
uv run pytest tests/test_organizer.py::test_scan_files
```

### Dependencies
```bash
# Install/sync dependencies (use uv, not pip)
uv sync

# Add a new dependency
uv add <package-name>
```

## Key Architecture Details

### File Organization Flow
1. **Scan**: `FileOrganizer.scan_files()` iterates through Downloads, filtering by age and category
2. **Categorize**: Uses `ConfigManager.CATEGORY_MAPPINGS` (70+ extensions across 8 categories)
3. **Move**: `FileOrganizer.organize()` creates category folders and moves files atomically
4. **Manifest**: `UndoManager.create_manifest()` records all moves for undo capability

### Critical Design Decisions
- **Tilde prefix (~)**: Category folders are named `~Documents`, `~Images`, etc. This sorts them to the bottom in macOS Finder (user preference)
- **Python 3.9 compatibility**: Uses `Optional[T]` type hints instead of `T | None` for broader macOS support
- **macOS-native paths**: Configuration stored in `~/Library/Application Support/TidyDownloads/`
- **Atomic operations**: Uses `shutil.move()` for safe file operations - never deletes files
- **Collision handling**: Appends `_2`, `_3`, etc. when destination file exists

### Data Storage Locations
- **Config**: `~/Library/Application Support/TidyDownloads/config.json`
- **Undo manifests**: `~/Library/Application Support/TidyDownloads/history/*.json`
- **Retention**: Max 5 undo sessions, auto-cleanup after 30 days

### File Categories
The system recognizes 8 categories (see `ConfigManager.CATEGORY_MAPPINGS`):
- **Installers**: .dmg, .pkg, .app, .mpkg
- **Documents**: .pdf, .doc, .docx, .txt, .xlsx, .csv, .ppt, etc.
- **Images**: .jpg, .png, .gif, .svg, .heic, .webp, etc.
- **Videos**: .mp4, .mov, .avi, .mkv, .webm, etc.
- **Audio**: .mp3, .m4a, .wav, .aac, .flac, etc.
- **Archives**: .zip, .rar, .7z, .tar, .gz, etc.
- **Code**: .json, .yaml, .py, .js, .swift, .md, etc.
- **Other**: Catch-all for unrecognized extensions

### Safety Features
- **Age filter**: Only processes files older than `minimum_file_age_days` (default: 7 days)
- **Skip hidden files**: Files starting with `.` are ignored
- **Skip directories**: User-created folders are never touched
- **Lock detection**: `_is_file_locked()` prevents moving files in use
- **Preview mode**: `--preview` shows what would happen without making changes
- **Full undo**: Every operation is reversible via manifest-based restoration

## Testing Guidelines

### Test Structure
- **ConfigManager**: 11 tests covering load/save/validation/category mapping
- **FileOrganizer**: 12 tests covering scan/organize/preview/collision handling
- **UndoManager**: 10 tests covering manifest creation/restoration/cleanup

### Test Patterns
- Uses `tempfile.TemporaryDirectory()` for isolated file system testing
- Mock file creation with controlled timestamps for age testing
- Comprehensive edge case coverage (locked files, collisions, empty folders)

### Performance Benchmarks
- **Scan**: < 0.1s for 100 files
- **Organize**: < 0.2s for 100 files
- **Memory**: ~15-20MB (target: < 50MB)
- **Test suite**: ~0.16s total execution time

## Code Patterns & Conventions

### Error Handling
All operations use defensive error handling:
```python
try:
    # Operation
except Exception as e:
    logger.error(f"Context: {e}")
    errors.append(error_msg)  # Collect for user display
```

### Type Hints
Use Python 3.9 compatible type hints throughout:
```python
from typing import Optional, Dict, List, Tuple
def function(param: str) -> Optional[Path]:  # NOT Path | None
```

### Logging
Follow established logging patterns:
- `logger.debug()`: Detailed operation info (file-level actions)
- `logger.info()`: High-level operation summaries
- `logger.warning()`: Recoverable issues (locked files, missing files)
- `logger.error()`: Operation failures

### Path Handling
Always use `pathlib.Path`:
- Convert to string only when necessary (e.g., `shutil.move(str(path), ...)`)
- Use `.expanduser()` for tilde expansion in user paths
- Use `Path.home()` for cross-platform home directory access

## Menu Bar App Architecture (Phase 2 - COMPLETE)

### Design Philosophy
The menu bar app (`app.py`) is a **thin GUI wrapper** around the existing CLI functionality:
- **Zero duplication**: All business logic remains in core modules (organizer, config_manager, undo_manager)
- **Reusable functions**: Calls the same functions used by CLI
- **Separation of concerns**: UI code is isolated in app.py

### Key Components
- **rumps.App**: Provides macOS menu bar integration
- **Menu structure**: Simple list-based menu with separators
- **Dialogs**: Uses `rumps.alert()` for confirmations and information display
- **Notifications**: Uses `rumps.notification()` for operation results
- **Status updates**: `@rumps.timer(60)` decorator for automatic status refresh every minute

### Menu Items
All menu items use the `@rumps.clicked("Menu Item")` decorator pattern:
- **Organize Now**: Shows preview → confirmation → executes organization → creates undo manifest
- **Preview Organization**: Displays dry-run preview in alert dialog
- **Undo Last Operation**: Shows undo preview → confirmation → restores files
- **Show Configuration**: Displays current config in alert
- **Show Statistics**: Shows file counts by category

### rumps Patterns
```python
# Menu item callback
@rumps.clicked("Item Name")
def callback(self, sender):
    # sender is the menu item that was clicked
    pass

# Timer for periodic updates
@rumps.timer(seconds)
def update_function(self, sender):
    # Runs every N seconds
    pass

# Show alert dialog
rumps.alert(title="Title", message="Message", ok="OK", cancel="Cancel")

# Send notification
rumps.notification(title="Title", subtitle="Subtitle", message="Message")
```

## Future Development (Phase 3)

### Phase 3: Distribution (Planned)
- py2app packaging for standalone .app bundle
- launchd integration for weekly scheduling (default: Sunday 2:00 AM)
- Code signing for distribution

### Extension Guidelines
When adding new features:
1. Maintain CLI functionality for testing
2. Keep business logic in core modules, UI logic separate
3. Update tests for any new functionality
4. Preserve backwards compatibility with existing configs
5. Follow the established tilde-prefix folder naming convention
