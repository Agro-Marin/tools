"""
Interactive Confirmation UI for Field/Method Renaming
====================================================

Provides interactive user interface for confirming changes before
applying them to files.
"""

import logging
import sys
from pathlib import Path

from processors.base_processor import ProcessResult
from utils.csv_reader import FieldChange

logger = logging.getLogger(__name__)


class ConfirmationUI:
    """Interactive UI for confirming changes"""

    def __init__(self, auto_approve_all: bool = False):
        """
        Initialize confirmation UI.

        Args:
            auto_approve_all: If True, automatically approve all changes
        """
        self.auto_approve_all = auto_approve_all
        self.session_choices = {}  # Cache user choices for consistency

    def confirm_file_changes(
        self,
        file_path: Path,
        changes: list[FieldChange],
        preview_content: tuple[str, str] | None = None,
    ) -> bool:
        """
        Confirm changes for a specific file.

        Args:
            file_path: Path to the file to be modified
            changes: List of changes to be applied
            preview_content: Optional tuple of (original_content, modified_content)

        Returns:
            True if user approves the changes
        """
        if self.auto_approve_all:
            return True

        # Check for cached decision
        cache_key = str(file_path)
        if cache_key in self.session_choices:
            return self.session_choices[cache_key]

        print("\n" + "=" * 80)
        print(f"📝 Proposed changes for: {file_path}")
        print("=" * 80)

        # Display file information
        self._display_file_info(file_path, changes)

        # Display changes
        self._display_changes(changes)

        # Display preview if available
        if preview_content:
            self._display_preview(preview_content[0], preview_content[1])

        # Get user decision
        choice = self._get_user_choice(
            "Apply these changes?",
            options=["y", "n", "s", "a", "q"],
            descriptions={
                "y": "Yes, apply changes",
                "n": "No, skip this file",
                "s": "Skip all remaining files",
                "a": "Apply to all remaining files",
                "q": "Quit",
            },
        )

        if choice == "y":
            self.session_choices[cache_key] = True
            return True
        elif choice == "n":
            self.session_choices[cache_key] = False
            return False
        elif choice == "s":
            # Skip all remaining
            self.auto_approve_all = False
            self.session_choices[cache_key] = False
            return False
        elif choice == "a":
            # Approve all remaining
            self.auto_approve_all = True
            self.session_choices[cache_key] = True
            return True
        elif choice == "q":
            # Quit
            print("\n🛑 User requested to quit.")
            sys.exit(0)

        return False

    def confirm_batch_changes(
        self, file_changes: dict[Path, list[FieldChange]]
    ) -> dict[Path, bool]:
        """
        Confirm changes for multiple files in batch.

        Args:
            file_changes: Dictionary mapping file paths to their changes

        Returns:
            Dictionary mapping file paths to approval status
        """
        if self.auto_approve_all:
            return {path: True for path in file_changes.keys()}

        print("\n" + "=" * 80)
        print(f"📊 Batch confirmation for {len(file_changes)} files")
        print("=" * 80)

        # Display summary
        total_changes = sum(len(changes) for changes in file_changes.values())
        print(f"Total files: {len(file_changes)}")
        print(f"Total changes: {total_changes}")

        # Group by file type
        by_type = {}
        for file_path in file_changes.keys():
            file_type = self._get_file_type(file_path)
            if file_type not in by_type:
                by_type[file_type] = []
            by_type[file_type].append(file_path)

        print("\nFiles by type:")
        for file_type, files in by_type.items():
            print(f"  {file_type}: {len(files)} files")

        # Get batch decision
        choice = self._get_user_choice(
            "How would you like to proceed?",
            options=["i", "a", "n", "q"],
            descriptions={
                "i": "Interactive - review each file individually",
                "a": "Apply all changes",
                "n": "Skip all changes",
                "q": "Quit",
            },
        )

        if choice == "i":
            # Interactive mode
            results = {}
            for file_path, changes in file_changes.items():
                results[file_path] = self.confirm_file_changes(file_path, changes)
            return results
        elif choice == "a":
            # Apply all
            return {path: True for path in file_changes.keys()}
        elif choice == "n":
            # Skip all
            return {path: False for path in file_changes.keys()}
        elif choice == "q":
            # Quit
            print("\n🛑 User requested to quit.")
            sys.exit(0)

        return {path: False for path in file_changes.keys()}

    def display_processing_results(self, results: list[ProcessResult]):
        """
        Display results of processing operations.

        Args:
            results: List of processing results
        """
        print("\n" + "=" * 80)
        print("📊 Processing Results")
        print("=" * 80)

        # Summary statistics
        total_files = len(results)
        successful = len([r for r in results if r.is_success])
        failed = len([r for r in results if r.status.value == "error"])
        skipped = len([r for r in results if r.status.value == "skipped"])
        no_changes = len([r for r in results if r.status.value == "no_changes"])

        total_changes = sum(r.changes_applied for r in results)

        print(f"📁 Total files processed: {total_files}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"ℹ️  No changes: {no_changes}")
        print(f"🔄 Total changes applied: {total_changes}")

        if total_files > 0:
            success_rate = (successful / total_files) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")

        # Show failed files
        failed_results = [r for r in results if r.status.value == "error"]
        if failed_results:
            print(f"\n❌ Failed files ({len(failed_results)}):")
            for result in failed_results:
                print(f"  {result.file_path}: {result.error_message}")

        # Show successful files with changes
        successful_with_changes = [r for r in results if r.is_success and r.has_changes]
        if successful_with_changes:
            print(f"\n✅ Successfully modified files ({len(successful_with_changes)}):")
            for result in successful_with_changes:
                print(f"  {result.file_path}: {result.changes_applied} changes")
                if result.backup_path:
                    print(f"    💾 Backup: {result.backup_path}")

    def display_dry_run_results(self, file_changes: dict[Path, list[FieldChange]]):
        """
        Display results of a dry run operation.

        Args:
            file_changes: Dictionary mapping file paths to their changes
        """
        print("\n" + "=" * 80)
        print("🔍 DRY RUN - No changes will be applied")
        print("=" * 80)

        total_files = len(file_changes)
        total_changes = sum(len(changes) for changes in file_changes.values())

        print(f"📁 Files that would be modified: {total_files}")
        print(f"🔄 Changes that would be applied: {total_changes}")

        # Group by file type and module
        by_type = {}
        by_module = {}

        for file_path, changes in file_changes.items():
            file_type = self._get_file_type(file_path)
            if file_type not in by_type:
                by_type[file_type] = {"files": 0, "changes": 0}
            by_type[file_type]["files"] += 1
            by_type[file_type]["changes"] += len(changes)

            for change in changes:
                if change.module not in by_module:
                    by_module[change.module] = {"files": set(), "changes": 0}
                by_module[change.module]["files"].add(file_path)
                by_module[change.module]["changes"] += 1

        print("\n📊 By file type:")
        for file_type, stats in by_type.items():
            print(f"  {file_type}: {stats['files']} files, {stats['changes']} changes")

        print("\n📦 By module:")
        for module, stats in by_module.items():
            print(
                f"  {module}: {len(stats['files'])} files, {stats['changes']} changes"
            )

        # Show detailed changes if not too many
        if total_files <= 10:
            print("\n📝 Detailed changes:")
            for file_path, changes in file_changes.items():
                print(f"\n  📄 {file_path}:")
                for change in changes:
                    change_type = "🏷️ " if change.is_field else "⚙️ "
                    print(f"    {change_type}{change.old_name} → {change.new_name}")
        else:
            print(
                f"\n💡 Use --verbose to see detailed changes for all {total_files} files"
            )

    def _display_file_info(self, file_path: Path, changes: list[FieldChange]):
        """Display information about the file"""
        print(f"📄 File: {file_path}")
        print(f"📂 Type: {self._get_file_type(file_path)}")
        print(f"🔄 Changes: {len(changes)}")

        # Show file size if possible
        try:
            file_size = file_path.stat().st_size
            print(f"💾 Size: {self._format_file_size(file_size)}")
        except Exception:
            pass

    def _display_changes(self, changes: list[FieldChange]):
        """Display the list of changes"""
        print(f"\n🔄 Changes to apply ({len(changes)}):")

        field_changes = [c for c in changes if c.is_field]
        method_changes = [c for c in changes if c.is_method]

        if field_changes:
            print(f"\n  🏷️  Fields ({len(field_changes)}):")
            for change in field_changes:
                print(
                    f"    {change.old_name} → {change.new_name} ({change.module}.{change.model})"
                )

        if method_changes:
            print(f"\n  ⚙️  Methods ({len(method_changes)}):")
            for change in method_changes:
                print(
                    f"    {change.old_name} → {change.new_name} ({change.module}.{change.model})"
                )

    def _display_preview(self, original_content: str, modified_content: str):
        """Display preview of changes"""
        print(f"\n👀 Preview (showing differences):")

        # Simple diff display - show first few lines that differ
        original_lines = original_content.splitlines()
        modified_lines = modified_content.splitlines()

        changes_shown = 0
        max_preview_changes = 5

        for i, (orig_line, mod_line) in enumerate(zip(original_lines, modified_lines)):
            if orig_line != mod_line and changes_shown < max_preview_changes:
                print(f"  Line {i+1}:")
                print(f"    - {orig_line}")
                print(f"    + {mod_line}")
                changes_shown += 1

        if changes_shown == max_preview_changes:
            print(f"    ... (showing first {max_preview_changes} changes)")

    def _get_user_choice(
        self,
        prompt: str,
        options: list[str],
        descriptions: dict[str, str] | None = None,
    ) -> str:
        """
        Get user choice from a list of options.

        Args:
            prompt: Question to ask the user
            options: List of valid option characters
            descriptions: Optional descriptions for each option

        Returns:
            Selected option
        """
        print(f"\n❓ {prompt}")

        if descriptions:
            for option in options:
                desc = descriptions.get(option, option)
                print(f"  {option}) {desc}")
        else:
            print(f"  Options: {'/'.join(options)}")

        while True:
            try:
                choice = (
                    input(f"\nEnter choice [{'/'.join(options)}]: ").lower().strip()
                )

                if choice in options:
                    return choice
                else:
                    print(
                        f"❌ Invalid choice. Please enter one of: {'/'.join(options)}"
                    )
            except (KeyboardInterrupt, EOFError):
                print("\n🛑 User interrupted.")
                sys.exit(0)

    def _get_file_type(self, file_path: Path) -> str:
        """Get display name for file type"""
        extension = file_path.suffix.lower()
        parent_dir = file_path.parent.name.lower()

        if extension == ".py":
            if "model" in parent_dir:
                return "Python Model"
            elif "controller" in parent_dir:
                return "Python Controller"
            elif "wizard" in parent_dir:
                return "Python Wizard"
            elif "wizard" in file_path.name.lower():
                return "Python Wizard"
            else:
                return "Python"
        elif extension == ".xml":
            if "view" in parent_dir:
                return "XML View"
            elif "data" in parent_dir:
                return "XML Data"
            elif "demo" in parent_dir:
                return "XML Demo"
            elif "template" in parent_dir:
                return "XML Template"
            elif "report" in parent_dir:
                return "XML Report"
            elif "security" in parent_dir:
                return "XML Security"
            else:
                return "XML"
        else:
            return extension.upper()

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
