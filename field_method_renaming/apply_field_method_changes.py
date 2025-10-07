#!/usr/bin/env python3
"""
Odoo Field/Method Renaming Tool - Enhanced CSV Version
=======================================================

Aplica automáticamente cambios de nombres de campos y métodos usando CSV enhanced
con rollback automático en caso de error.

Usage:
    python apply_field_method_changes.py --csv-file changes.csv --repo-path /path/to/odoo [options]

Example:
    # Aplicar cambios aprobados desde CSV enhanced
    python apply_field_method_changes.py --csv-file enhanced_changes.csv --repo-path /home/user/odoo

    # Modo dry-run para simular cambios
    python apply_field_method_changes.py --csv-file changes.csv --repo-path /home/user/odoo --dry-run
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from processors.base_processor import ProcessingStatus, ProcessResult
from processors.python_processor import PythonProcessor
from processors.xml_processor import XMLProcessor
from utils.backup_manager import BackupManager
from utils.csv_reader import CSVReader, CSVValidationError
from utils.file_finder import FileFinder
from utils.change_grouper import ChangeGroup, group_changes_hierarchically


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("field_method_renaming.log"),
        ],
    )

    # Reduce noise from some modules
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Apply field and method name changes from enhanced CSV to Odoo repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --csv-file enhanced_changes.csv --repo-path /path/to/odoo
  %(prog)s --csv-file changes.csv --repo-path /path/to/odoo --dry-run --verbose
        """,
    )

    # Required arguments
    parser.add_argument(
        "--csv-file",
        required=True,
        help="Path to enhanced CSV file with approved changes"
    )

    parser.add_argument(
        "--repo-path",
        required=True,
        help="Path to Odoo repository root"
    )

    # Processing options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without applying changes",
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Disable backup creation (NOT RECOMMENDED - disables rollback capability)",
    )

    # Output options
    parser.add_argument(
        "--backup-dir",
        help="Custom backup directory (default: .backups)"
    )

    # Logging options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    return parser.parse_args()


class FieldMethodRenamer:
    """Aplicador de cambios con rollback automático"""

    def __init__(self, csv_file: str, repo_path: str, dry_run: bool = False,
                 create_backups: bool = True, backup_dir: str = None, verbose: bool = False):
        """
        Initialize the renaming tool.

        Args:
            csv_file: Path to enhanced CSV file
            repo_path: Path to Odoo repository
            dry_run: If True, only simulate changes
            create_backups: If True, create backups (required for rollback)
            backup_dir: Custom backup directory
            verbose: Enable verbose logging
        """
        self.csv_file = Path(csv_file)
        self.repo_path = Path(repo_path)
        self.dry_run = dry_run
        self.create_backups = create_backups
        self.backup_dir = backup_dir
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.csv_reader = None
        self.file_finder = None
        self.backup_manager = None
        self.processors = {}

        # Statistics
        self.stats = {
            "total_groups": 0,
            "total_changes": 0,
            "applied_changes": 0,
            "failed_changes": 0,
            "rollback_files": 0
        }

    def initialize(self):
        """Initialize all components"""
        self.logger.info("Initializing Field/Method Renaming Tool...")

        # Validate paths
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path not found: {self.repo_path}")

        # Initialize CSV reader
        self.csv_reader = CSVReader(str(self.csv_file))

        # Initialize file finder
        self.file_finder = FileFinder(str(self.repo_path))

        # Initialize backup manager
        if self.create_backups:
            backup_base_dir = self.backup_dir if self.backup_dir else str(self.repo_path / ".backups")
            self.backup_manager = BackupManager(backup_base_dir=backup_base_dir)

        # Initialize processors
        self.processors = {
            ".py": PythonProcessor(
                create_backups=self.create_backups,
                validate_syntax=True
            ),
            ".xml": XMLProcessor(
                create_backups=self.create_backups,
                validate_syntax=True
            ),
        }

        # Set backup manager for processors
        if self.backup_manager:
            for processor in self.processors.values():
                processor.set_backup_manager(self.backup_manager)

        self.logger.info("Initialization completed successfully")

    def run(self) -> int:
        """
        Run the main processing workflow with hierarchical change grouping.

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # 1. Load approved changes
            self.logger.info("Loading approved changes from CSV...")
            all_changes = self.csv_reader.load_changes()

            if not all_changes:
                print("ℹ️  No approved changes found in CSV")
                return 0

            # 2. Group by hierarchy
            change_groups = group_changes_hierarchically(all_changes)

            self.stats["total_groups"] = len(change_groups)
            self.stats["total_changes"] = len(all_changes)

            print(f"\n📊 Processing {len(change_groups)} change groups "
                  f"with {len(all_changes)} total changes...")

            # Display dry-run info if applicable
            if self.dry_run:
                print("\n🔍 DRY-RUN MODE - No changes will be applied\n")
                self._display_dry_run_summary(change_groups)
                return 0

            # 3. Start backup session
            if self.backup_manager:
                session_dir = self.backup_manager.start_backup_session()
                self.logger.info(f"Started backup session: {session_dir}")

            # 4. Process each group
            all_results = []
            for group_id, change_group in change_groups.items():
                print(f"\n🔄 Processing group {group_id}: "
                      f"{change_group.primary.old_name} → {change_group.primary.new_name}")

                group_results = self._process_change_group(change_group)
                all_results.extend(group_results)

            # 5. Finalize backup session
            if self.backup_manager:
                self.backup_manager.finalize_session()

            # 6. Display summary
            self._display_summary(all_results)

            # Return exit code
            return 0 if self.stats["failed_changes"] == 0 else 1

        except KeyboardInterrupt:
            print("\n⚠️  Process interrupted by user")
            return 130
        except CSVValidationError as e:
            self.logger.error(f"CSV validation error: {e}")
            print(f"❌ CSV validation error: {e}")
            return 2
        except Exception as e:
            self.logger.exception("Fatal error during processing")
            print(f"\n❌ Fatal error: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 1

    def _display_dry_run_summary(self, change_groups: dict[str, ChangeGroup]):
        """Display summary for dry-run mode"""
        for group_id, group in change_groups.items():
            print(f"\nGroup {group_id}:")
            print(f"  Primary: {group.primary}")
            if group.extension_declarations:
                print(f"  Extensions: {len(group.extension_declarations)}")
                for ext in group.extension_declarations:
                    print(f"    - {ext}")
            if group.references:
                print(f"  References: {len(group.references)}")

    def _process_change_group(self, change_group: ChangeGroup) -> list[ProcessResult]:
        """
        Process a change group with rollback if any file fails.

        Args:
            change_group: Group of related changes

        Returns:
            List of ProcessResult objects
        """
        # Find affected files ordered by priority
        affected_files = self._find_affected_files_ordered(change_group)
        results = []
        group_has_error = False

        for file_path in affected_files:
            # Get changes for this file
            file_changes = change_group.get_changes_for_file(file_path)
            if not file_changes:
                continue

            # Log extension declarations
            for change in file_changes:
                if change.is_extension_declaration():
                    self.logger.info(f"Processing extension declaration in {change.module}: "
                                   f"{change.old_name} → {change.new_name}")

            # Process file
            processor = self._get_processor_for_file(file_path)
            if processor:
                result = processor.process_file(file_path, file_changes)
                results.append(result)

                # Check for errors
                if result.status == ProcessingStatus.ERROR:
                    group_has_error = True
                    self.logger.error(f"Error in group {change_group.primary.change_id}: "
                                   f"{result.error_message}")

                    # Rollback was already done in BaseProcessor
                    if result.rollback_performed:
                        self.stats["rollback_files"] += 1

                    # If base or extension fails, skip remaining files
                    if change_group.primary in file_changes or \
                       any(c.is_extension_declaration() for c in file_changes):
                        self.logger.warning("Skipping remaining files due to base/extension failure")
                        break

                # Update stats if successful
                elif result.is_success:
                    self.stats["applied_changes"] += result.changes_applied
                    # Track applied changes in the group
                    for change in file_changes:
                        if change.applied:
                            change_group.track_applied(file_path, change)

        # If group had error, increment counter
        if group_has_error:
            self.stats["failed_changes"] += 1

        return results

    def _find_affected_files_ordered(self, change_group: ChangeGroup) -> list[Path]:
        """
        Find all affected files in correct processing order.

        Returns files in this order:
        1. Primary module files (base)
        2. Extension module files
        3. Reference files
        """
        affected = []

        # Get primary model info
        module = change_group.primary.module
        model = change_group.primary.model

        # 1. Find primary module files
        file_set = self.file_finder.find_files_for_model(module, model)
        if not file_set.is_empty():
            affected.extend(file_set.python_files)
            affected.extend(file_set.view_files)
            affected.extend(file_set.data_files)

        # 2. Find extension module files
        for ext_decl in change_group.extension_declarations:
            ext_module = ext_decl.module
            file_set = self.file_finder.find_files_for_model(ext_module, model)
            if not file_set.is_empty():
                affected.extend(file_set.python_files)
                affected.extend(file_set.view_files)

        # 3. Find reference files (cross-module)
        for ref in change_group.references:
            if ref.impact_type == 'cross_module':
                ref_module = ref.module
                file_set = self.file_finder.find_files_for_model(ref_module, ref.model)
                if not file_set.is_empty():
                    affected.extend(file_set.python_files)
                    affected.extend(file_set.view_files)

        # Remove duplicates while preserving order
        seen = set()
        ordered = []
        for path in affected:
            if path not in seen:
                seen.add(path)
                ordered.append(path)

        return ordered

    def _get_processor_for_file(self, file_path: Path) -> Optional:
        """Get appropriate processor for a file"""
        extension = file_path.suffix.lower()
        return self.processors.get(extension)

    def _display_summary(self, results: list[ProcessResult]):
        """Display final processing summary"""
        successful = len([r for r in results if r.is_success])
        failed = len([r for r in results if r.status == ProcessingStatus.ERROR])
        rollbacks = len([r for r in results if r.rollback_performed])

        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                      Processing Summary                          ║
╚══════════════════════════════════════════════════════════════════╝

📊 Results:
   ✅ Successful files: {successful}
   ❌ Failed files: {failed}
   🔄 Files rolled back: {rollbacks}

   📝 Total changes applied: {self.stats['applied_changes']}
   📝 Total changes failed: {self.stats['failed_changes']}
        """)

        # If there were errors, show details
        if failed > 0:
            print("\n⚠️  Errors occurred during processing:")
            for result in results:
                if result.status == ProcessingStatus.ERROR:
                    print(f"   ❌ {result.file_path}: {result.error_message}")
                    if result.rollback_performed:
                        print(f"      ↩️  Changes rolled back successfully")
                    else:
                        print(f"      ⚠️  ROLLBACK FAILED - manual intervention required!")


def main():
    """Main entry point"""
    args = parse_arguments()

    # Setup logging
    setup_logging(args.verbose)

    # Create and run tool
    tool = FieldMethodRenamer(
        csv_file=args.csv_file,
        repo_path=args.repo_path,
        dry_run=args.dry_run,
        create_backups=not args.no_backup,
        backup_dir=args.backup_dir,
        verbose=args.verbose
    )

    tool.initialize()
    return tool.run()


if __name__ == "__main__":
    sys.exit(main())
