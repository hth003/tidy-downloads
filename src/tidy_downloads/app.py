"""macOS Menu Bar Application for TidyDownloads."""

import rumps
import logging
from datetime import datetime
from pathlib import Path

from .config_manager import ConfigManager
from .organizer import FileOrganizer
from .undo_manager import UndoManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class TidyDownloadsApp(rumps.App):
    """TidyDownloads Menu Bar Application."""

    def __init__(self):
        """Initialize the menu bar app."""
        super(TidyDownloadsApp, self).__init__(
            "TidyDownloads",  # App name
            title="🗂️",  # File cabinet emoji as menu bar title
            quit_button=None  # We'll add our own quit button
        )

        logger.info("Menu bar app initialized with title: 🗂️")

        # Initialize core components
        try:
            self.config = ConfigManager()
            self.organizer = FileOrganizer(self.config)
            self.undo_manager = UndoManager()
            logger.info("TidyDownloads components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            rumps.alert(
                title="Initialization Error",
                message=f"Failed to start TidyDownloads: {str(e)}\n\nPlease check your configuration.",
                ok="Quit"
            )
            rumps.quit_application()

        # Build the menu
        self.status_item = rumps.MenuItem("Status: Ready", callback=None)

        self.menu = [
            self.status_item,
            None,  # Separator
            "Organize Now",
            "Preview Organization",
            "Undo Last Operation",
            None,  # Separator
            "Preferences...",
            "Show Configuration",
            "Show Statistics",
            None,  # Separator
            "Quit TidyDownloads"
        ]

        logger.info("Menu structure created successfully")

        # Set up status update timer (every minute)
        self.status_timer = rumps.Timer(self.update_status, 60)
        self.status_timer.start()
        logger.info("Status update timer started")

        # Initial status update
        self.update_status(None)
        logger.info("Initial status update complete")

    @rumps.clicked("Organize Now")
    def organize_now(self, _):
        """Organize files in Downloads folder."""
        try:
            # Get preview first
            preview = self.organizer.get_organization_preview()

            if "No files to organize" in preview:
                rumps.alert(
                    title="Nothing to Organize",
                    message="All files in your Downloads folder are either recent (< 7 days old) or already organized.",
                    ok="OK"
                )
                return

            # Show preview and ask for confirmation
            response = rumps.alert(
                title="Organize Downloads?",
                message=preview,
                ok="Organize",
                cancel="Cancel"
            )

            if response == 0:  # User cancelled
                return

            # Perform organization
            logger.info("Starting organization...")
            moves, errors = self.organizer.organize(dry_run=False)

            # Create undo manifest
            self.undo_manager.create_manifest(moves, errors)

            # Show results
            total_files = sum(len(file_list) for file_list in moves.values())

            if errors:
                error_summary = f"{len(errors)} errors occurred. Check logs for details."
                rumps.notification(
                    title="Organization Complete with Errors",
                    subtitle=f"Organized {total_files} files",
                    message=error_summary
                )
            else:
                rumps.notification(
                    title="Organization Complete",
                    subtitle=f"Successfully organized {total_files} files",
                    message="Your Downloads folder is now tidy!"
                )

            # Update status
            self.update_status(None)

            logger.info(f"Organization completed: {total_files} files organized")

        except Exception as e:
            logger.error(f"Error during organization: {e}", exc_info=True)
            rumps.alert(
                title="Organization Failed",
                message=f"An error occurred: {str(e)}\n\nPlease check the logs for details.",
                ok="OK"
            )

    @rumps.clicked("Preview Organization")
    def preview_organization(self, _):
        """Show what would be organized without making changes."""
        try:
            preview = self.organizer.get_organization_preview()

            rumps.alert(
                title="Organization Preview",
                message=preview,
                ok="OK"
            )

        except Exception as e:
            logger.error(f"Error generating preview: {e}", exc_info=True)
            rumps.alert(
                title="Preview Failed",
                message=f"Could not generate preview: {str(e)}",
                ok="OK"
            )

    @rumps.clicked("Undo Last Operation")
    def undo_last_operation(self, _):
        """Undo the last organization operation."""
        try:
            # Get preview of what will be undone
            preview = self.undo_manager.get_undo_preview()

            if "No organization history" in preview or "already been undone" in preview:
                rumps.alert(
                    title="Nothing to Undo",
                    message=preview,
                    ok="OK"
                )
                return

            # Show preview and ask for confirmation
            response = rumps.alert(
                title="Undo Last Organization?",
                message=preview,
                ok="Undo",
                cancel="Cancel"
            )

            if response == 0:  # User cancelled
                return

            # Perform undo
            logger.info("Starting undo...")
            files_restored, errors = self.undo_manager.undo()

            # Show results
            if errors:
                error_summary = f"{len(errors)} errors occurred. Check logs for details."
                rumps.notification(
                    title="Undo Complete with Errors",
                    subtitle=f"Restored {files_restored} files",
                    message=error_summary
                )
            else:
                rumps.notification(
                    title="Undo Complete",
                    subtitle=f"Successfully restored {files_restored} files",
                    message="Files returned to their original locations"
                )

            # Update status
            self.update_status(None)

            logger.info(f"Undo completed: {files_restored} files restored")

        except Exception as e:
            logger.error(f"Error during undo: {e}", exc_info=True)
            rumps.alert(
                title="Undo Failed",
                message=f"An error occurred: {str(e)}\n\nPlease check the logs for details.",
                ok="OK"
            )

    @rumps.clicked("Preferences...")
    def show_preferences(self, _):
        """Open streamlined preferences dialog for editing settings."""
        try:
            # Get current settings
            current_age = self.config.get_minimum_file_age_days()
            current_categories = set(self.config.get_enabled_categories())
            current_notifications = self.config.get("send_notifications", True)

            # All available categories
            all_categories = ["Installers", "Documents", "Images", "Videos", "Audio", "Archives", "Code", "Other"]

            # Step 1: Edit minimum file age
            window = rumps.Window(
                title="Minimum File Age",
                message=f"Only organize files older than how many days?\n\nCurrent: {current_age} days\nEnter a value between 1 and 30:",
                default_text=str(current_age),
                dimensions=(280, 24)
            )
            response = window.run()

            if not response.clicked:
                return  # User cancelled

            # Validate age input
            try:
                new_age = int(response.text)
                if new_age < 1 or new_age > 30:
                    rumps.alert(
                        title="Invalid Input",
                        message="File age must be between 1 and 30 days.",
                        ok="OK"
                    )
                    return
            except ValueError:
                rumps.alert(
                    title="Invalid Input",
                    message="Please enter a valid number.",
                    ok="OK"
                )
                return

            # Step 2: Edit ALL categories in ONE dialog
            category_list = ""
            for i, cat in enumerate(all_categories, 1):
                icon = self.organizer._get_category_icon(cat)
                status = "✓" if cat in current_categories else "✗"
                category_list += f"{i}. {icon} {cat} {status}\n"

            currently_enabled = ", ".join([str(i+1) for i, cat in enumerate(all_categories) if cat in current_categories])

            window = rumps.Window(
                title="Enable Categories",
                message=f"Select which categories to organize:\n\n{category_list}\nCurrently enabled: {currently_enabled}\n\nEnter numbers (e.g., 1,2,3,5) or 'all':",
                default_text=currently_enabled,
                dimensions=(320, 24)
            )
            response = window.run()

            if not response.clicked:
                return  # User cancelled

            # Parse category selection
            try:
                new_categories = set()
                user_input = response.text.strip().lower()

                if user_input == "all":
                    new_categories = set(all_categories)
                else:
                    # Parse comma-separated numbers
                    selected_numbers = [int(n.strip()) for n in user_input.split(",") if n.strip()]
                    for num in selected_numbers:
                        if 1 <= num <= len(all_categories):
                            new_categories.add(all_categories[num - 1])
                        else:
                            rumps.alert(
                                title="Invalid Input",
                                message=f"Number {num} is out of range (1-{len(all_categories)}).",
                                ok="OK"
                            )
                            return

                # Validate at least one category is enabled
                if not new_categories:
                    rumps.alert(
                        title="No Categories Selected",
                        message="You must enable at least one category.\n\nPreferences not saved.",
                        ok="OK"
                    )
                    return

            except ValueError:
                rumps.alert(
                    title="Invalid Input",
                    message="Please enter numbers separated by commas (e.g., 1,2,3) or 'all'.",
                    ok="OK"
                )
                return

            # Step 3: Edit notifications
            notif_status = "✓ Enabled" if current_notifications else "✗ Disabled"
            response = rumps.alert(
                title="Notifications",
                message=f"Current status: {notif_status}\n\nShow notifications after organizing?",
                ok="Enable",
                cancel="Disable"
            )
            new_notifications = (response == 1)

            # Step 4: Show summary and confirm
            summary = f"""Review your changes:

Minimum File Age: {current_age} → {new_age} days

Enabled Categories: {len(new_categories)} of {len(all_categories)}
"""
            for cat in sorted(all_categories):
                was_enabled = cat in current_categories
                is_enabled = cat in new_categories
                if was_enabled == is_enabled:
                    status = "  ✓" if is_enabled else "  ✗"
                elif is_enabled:
                    status = "  ✓ (NEW)"
                else:
                    status = "  ✗ (REMOVED)"
                summary += f"{status} {cat}\n"

            summary += f"\nNotifications: "
            if current_notifications == new_notifications:
                summary += "✓ Enabled" if new_notifications else "✗ Disabled"
            elif new_notifications:
                summary += "✓ Enabled (changed)"
            else:
                summary += "✗ Disabled (changed)"

            response = rumps.alert(
                title="Save Preferences?",
                message=summary,
                ok="Save",
                cancel="Cancel"
            )

            if response == 0:  # User cancelled
                return

            # Save changes
            self.config.set("minimum_file_age_days", new_age)
            self.config.set("enabled_categories", list(new_categories))
            self.config.set("send_notifications", new_notifications)

            logger.info(f"Preferences updated: age={new_age}, categories={new_categories}, notifications={new_notifications}")

            # Show success notification
            rumps.notification(
                title="Preferences Saved",
                subtitle="Settings updated successfully",
                message=f"File age: {new_age} days | Categories: {len(new_categories)} enabled"
            )

            # Update status to reflect potential changes
            self.update_status(None)

        except Exception as e:
            logger.error(f"Error in preferences dialog: {e}", exc_info=True)
            rumps.alert(
                title="Preferences Error",
                message=f"Could not save preferences: {str(e)}",
                ok="OK"
            )

    @rumps.clicked("Show Configuration")
    def show_configuration(self, _):
        """Display current configuration (read-only)."""
        try:
            config_dict = self.config.to_dict()

            # Build configuration display
            config_text = f"""Downloads Path: {config_dict['downloads_path']}
Minimum File Age: {config_dict['minimum_file_age_days']} days
Notifications: {'✓ Enabled' if config_dict['send_notifications'] else '✗ Disabled'}

Enabled Categories ({len(config_dict['enabled_categories'])} of 8):
"""
            all_categories = ["Installers", "Documents", "Images", "Videos", "Audio", "Archives", "Code", "Other"]
            for cat in all_categories:
                icon = self.organizer._get_category_icon(cat)
                if cat in config_dict['enabled_categories']:
                    folder_name = self.config.get_destination_folder_name(cat)
                    config_text += f"  ✓ {icon} {cat} → {folder_name}/\n"
                else:
                    config_text += f"  ✗ {icon} {cat}\n"

            config_text += f"\nConfig file: {self.config.config_path}"

            rumps.alert(
                title="TidyDownloads Configuration",
                message=config_text,
                ok="OK"
            )

        except Exception as e:
            logger.error(f"Error showing configuration: {e}", exc_info=True)
            rumps.alert(
                title="Configuration Error",
                message=f"Could not load configuration: {str(e)}",
                ok="OK"
            )

    @rumps.clicked("Show Statistics")
    def show_statistics(self, _):
        """Display organization statistics."""
        try:
            stats = self.organizer.get_stats()

            # Build statistics display
            stats_text = f"""Files Ready to Organize: {stats['total_files_to_organize']}
Categories with Files: {stats['categories_with_files']}

Files per Category:
"""
            # Show per-category counts
            categories = [k.replace('category_', '') for k in stats.keys() if k.startswith('category_')]
            if categories:
                for category in sorted(categories):
                    count = stats[f'category_{category}']
                    folder_name = self.config.get_destination_folder_name(category.title())
                    stats_text += f"  • {category.title()}: {count} files → {folder_name}/\n"
            else:
                stats_text += "  (No files ready for organization)"

            rumps.alert(
                title="Downloads Folder Statistics",
                message=stats_text,
                ok="OK"
            )

        except Exception as e:
            logger.error(f"Error showing statistics: {e}", exc_info=True)
            rumps.alert(
                title="Statistics Error",
                message=f"Could not load statistics: {str(e)}",
                ok="OK"
            )

    @rumps.clicked("Quit TidyDownloads")
    def quit_application(self, _):
        """Quit the application."""
        rumps.quit_application()

    def update_status(self, _):
        """Update the status menu item with current information."""
        try:
            stats = self.organizer.get_stats()
            file_count = stats['total_files_to_organize']

            if file_count == 0:
                status_text = "Status: All tidy ✓"
            elif file_count == 1:
                status_text = "Status: 1 file ready"
            else:
                status_text = f"Status: {file_count} files ready"

            # Update the status item directly
            self.status_item.title = status_text
            logger.debug(f"Status updated: {status_text}")

        except Exception as e:
            logger.debug(f"Could not update status: {e}")
            # Don't show error to user - status update is non-critical


def main():
    """Main entry point for the menu bar application."""
    logger.info("Starting TidyDownloads menu bar app...")
    app = TidyDownloadsApp()
    app.run()


if __name__ == "__main__":
    main()
