"""Command-line interface for TidyDownloads."""

import sys
import argparse
import logging
from pathlib import Path

from .config_manager import ConfigManager
from .organizer import FileOrganizer
from .undo_manager import UndoManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def setup_parser() -> argparse.ArgumentParser:
    """
    Set up command-line argument parser.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description='TidyDownloads - Organize your Downloads folder automatically',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tidy-downloads --preview          Preview what files will be organized
  tidy-downloads --organize         Organize files in Downloads folder
  tidy-downloads --undo             Undo the last organization
  tidy-downloads --config           Show current configuration
  tidy-downloads --stats            Show organization statistics
  tidy-downloads --history          Show organization history

Configuration is stored in:
  ~/Library/Application Support/TidyDownloads/config.json
        """
    )

    # Main actions (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=False)

    action_group.add_argument(
        '--preview',
        action='store_true',
        help='Preview files that will be organized without making changes'
    )

    action_group.add_argument(
        '--organize',
        action='store_true',
        help='Organize files in Downloads folder'
    )

    action_group.add_argument(
        '--undo',
        action='store_true',
        help='Undo the last organization operation'
    )

    action_group.add_argument(
        '--config',
        action='store_true',
        help='Show current configuration'
    )

    action_group.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics about Downloads folder'
    )

    action_group.add_argument(
        '--history',
        action='store_true',
        help='Show organization history'
    )

    # Options
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='Suppress all output except errors'
    )

    parser.add_argument(
        '--yes',
        '-y',
        action='store_true',
        help='Skip confirmation prompts'
    )

    return parser


def confirm_action(prompt: str) -> bool:
    """
    Ask user for confirmation.

    Args:
        prompt: Confirmation prompt message

    Returns:
        True if user confirms, False otherwise
    """
    while True:
        response = input(f"{prompt} (y/n): ").lower().strip()
        if response in ('y', 'yes'):
            return True
        if response in ('n', 'no'):
            return False
        print("Please enter 'y' or 'n'")


def cmd_preview(config: ConfigManager) -> int:
    """
    Preview files that will be organized.

    Args:
        config: ConfigManager instance

    Returns:
        Exit code (0 for success)
    """
    try:
        organizer = FileOrganizer(config)
        preview = organizer.get_organization_preview()
        print(preview)
        return 0
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        return 1


def cmd_organize(config: ConfigManager, skip_confirm: bool = False) -> int:
    """
    Organize files in Downloads folder.

    Args:
        config: ConfigManager instance
        skip_confirm: Skip confirmation prompt if True

    Returns:
        Exit code (0 for success)
    """
    try:
        organizer = FileOrganizer(config)

        # Show preview first
        preview = organizer.get_organization_preview()
        print(preview)

        if "No files to organize" in preview:
            print("\n✓ Nothing to do!")
            return 0

        # Confirm action
        if not skip_confirm:
            if not confirm_action("\nProceed with organization?"):
                print("Cancelled.")
                return 0

        print("\nOrganizing files...")
        moves, errors = organizer.organize(dry_run=False)

        # Create undo manifest
        undo_mgr = UndoManager()
        undo_mgr.create_manifest(moves, errors)

        # Show results
        total_files = sum(len(file_list) for file_list in moves.values())
        print(f"\n✓ Successfully organized {total_files} files!")

        if errors:
            print(f"\n⚠ {len(errors)} errors occurred:")
            for error in errors[:10]:  # Show first 10 errors
                print(f"  • {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")

        return 0

    except Exception as e:
        logger.error(f"Error during organization: {e}")
        return 1


def cmd_undo(config: ConfigManager, skip_confirm: bool = False) -> int:
    """
    Undo the last organization operation.

    Args:
        config: ConfigManager instance
        skip_confirm: Skip confirmation prompt if True

    Returns:
        Exit code (0 for success)
    """
    try:
        undo_mgr = UndoManager()

        # Show preview
        preview = undo_mgr.get_undo_preview()
        print(preview)

        if "No organization history" in preview or "already been undone" in preview:
            return 0

        # Confirm action
        if not skip_confirm:
            if not confirm_action("\nProceed with undo?"):
                print("Cancelled.")
                return 0

        print("\nUndoing organization...")
        files_restored, errors = undo_mgr.undo()

        # Show results
        print(f"\n✓ Successfully restored {files_restored} files!")

        if errors:
            print(f"\n⚠ {len(errors)} errors occurred:")
            for error in errors[:10]:
                print(f"  • {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")

        return 0

    except Exception as e:
        logger.error(f"Error during undo: {e}")
        return 1


def cmd_config(config: ConfigManager) -> int:
    """
    Show current configuration.

    Args:
        config: ConfigManager instance

    Returns:
        Exit code (0 for success)
    """
    try:
        print("\nCurrent Configuration")
        print("=" * 60)
        print(f"Config file: {config.config_path}")
        print()

        config_dict = config.to_dict()

        print(f"Downloads path:        {config_dict['downloads_path']}")
        print(f"Minimum file age:      {config_dict['minimum_file_age_days']} days")
        print(f"Send notifications:    {config_dict['send_notifications']}")
        print()

        print("Enabled categories:")
        for category in config_dict['enabled_categories']:
            folder_name = config.get_destination_folder_name(category)
            print(f"  • {category:12} → {folder_name}/")

        print()
        print(f"Category folder prefix: '{config.FOLDER_PREFIX}' (sorts to bottom)")

        return 0

    except Exception as e:
        logger.error(f"Error showing configuration: {e}")
        return 1


def cmd_stats(config: ConfigManager) -> int:
    """
    Show statistics about Downloads folder.

    Args:
        config: ConfigManager instance

    Returns:
        Exit code (0 for success)
    """
    try:
        organizer = FileOrganizer(config)
        stats = organizer.get_stats()

        print("\nDownloads Folder Statistics")
        print("=" * 60)
        print(f"Files ready to organize: {stats['total_files_to_organize']}")
        print(f"Categories with files:   {stats['categories_with_files']}")
        print()

        # Show per-category counts
        categories = [k.replace('category_', '') for k in stats.keys() if k.startswith('category_')]
        if categories:
            print("Files per category:")
            for category in sorted(categories):
                count = stats[f'category_{category}']
                folder_name = config.get_destination_folder_name(category.title())
                print(f"  • {category.title():12} → {folder_name:15} ({count} files)")

        return 0

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return 1


def cmd_history(config: ConfigManager) -> int:
    """
    Show organization history.

    Args:
        config: ConfigManager instance

    Returns:
        Exit code (0 for success)
    """
    try:
        undo_mgr = UndoManager()
        history = undo_mgr.get_history(limit=10)

        if not history:
            print("\nNo organization history found.")
            return 0

        print("\nOrganization History (last 10 operations)")
        print("=" * 60)

        for entry in history:
            timestamp = entry['timestamp']
            total_files = entry['total_files']
            undone = entry['undone']
            status = "[UNDONE]" if undone else "[ACTIVE]"

            print(f"{timestamp}  {status:10}  {total_files} files")

        return 0

    except Exception as e:
        logger.error(f"Error showing history: {e}")
        return 1


def main() -> int:
    """
    Main entry point for CLI.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = setup_parser()
    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)

    # Initialize configuration
    try:
        config = ConfigManager()
        if not config.validate():
            logger.error("Configuration validation failed")
            return 1
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return 1

    # Execute requested action
    try:
        if args.preview:
            return cmd_preview(config)
        elif args.organize:
            return cmd_organize(config, skip_confirm=args.yes)
        elif args.undo:
            return cmd_undo(config, skip_confirm=args.yes)
        elif args.config:
            return cmd_config(config)
        elif args.stats:
            return cmd_stats(config)
        elif args.history:
            return cmd_history(config)
        else:
            # No action specified, show help
            parser.print_help()
            return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
