#!/usr/bin/env python3
"""
Odoo Field/Method Renaming Tool
===============================

Script principal para aplicar automáticamente cambios de nombres de campos y métodos
en repositorios Odoo basado en archivos CSV generados por field_method_detector.

Usage:
    python apply_field_method_changes.py --csv-file changes.csv --repo-path /path/to/odoo [options]

Example:
    # Aplicar todos los cambios con respaldos automáticos
    python apply_field_method_changes.py --csv-file odoo_field_changes_detected.csv --repo-path /home/user/odoo
    
    # Modo interactivo para revisar cada cambio
    python apply_field_method_changes.py --csv-file changes.csv --repo-path /home/user/odoo --interactive
    
    # Solo simular cambios sin aplicarlos
    python apply_field_method_changes.py --csv-file changes.csv --repo-path /home/user/odoo --dry-run
"""
import sys
import os
import argparse
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import json

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from utils.csv_reader import CSVReader, FieldChange, CSVValidationError
from utils.file_finder import FileFinder, FileSet
from utils.backup_manager import BackupManager, BackupError
from processors.base_processor import ProcessResult, ProcessingStatus
from processors.python_processor import PythonProcessor
from processors.xml_processor import XMLProcessor
from interactive.confirmation_ui import ConfirmationUI
from config.renaming_settings import RenamingConfig, FILE_TYPE_CATEGORIES


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('field_method_renaming.log')
        ]
    )
    
    # Reduce noise from some modules
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Apply field and method name changes from CSV to Odoo repository',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --csv-file changes.csv --repo-path /path/to/odoo
  %(prog)s --csv-file changes.csv --repo-path /path/to/odoo --interactive
  %(prog)s --csv-file changes.csv --repo-path /path/to/odoo --dry-run --verbose
  %(prog)s --csv-file changes.csv --repo-path /path/to/odoo --module sale --file-types python views
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--csv-file',
        required=True,
        help='Path to CSV file with field/method changes'
    )
    
    parser.add_argument(
        '--repo-path',
        required=True,
        help='Path to Odoo repository root'
    )
    
    # Processing options
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Enable interactive mode to confirm each change'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without applying changes'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Disable backup creation (not recommended)'
    )
    
    parser.add_argument(
        '--no-validation',
        action='store_true',
        help='Disable syntax validation after changes'
    )
    
    # Filtering options
    parser.add_argument(
        '--module', '-m',
        help='Process only specific module'
    )
    
    parser.add_argument(
        '--modules',
        nargs='+',
        help='Process only specific modules (space-separated list)'
    )
    
    parser.add_argument(
        '--file-types',
        nargs='+',
        choices=list(FILE_TYPE_CATEGORIES.keys()),
        default=list(FILE_TYPE_CATEGORIES.keys()),
        help='File types to process'
    )
    
    # Output options
    parser.add_argument(
        '--output-report',
        help='Path to output detailed report file'
    )
    
    parser.add_argument(
        '--backup-dir',
        help='Custom backup directory (default: .backups)'
    )
    
    # Logging options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )
    
    return parser.parse_args()


class FieldMethodRenamingTool:
    """Main application class for field/method renaming"""
    
    def __init__(self, config: RenamingConfig):
        """
        Initialize the renaming tool.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.csv_reader = None
        self.file_finder = None
        self.backup_manager = None
        self.confirmation_ui = None
        self.processors = {}
        
        # Statistics
        self.stats = {
            'total_changes': 0,
            'total_files_found': 0,
            'total_files_processed': 0,
            'successful_files': 0,
            'failed_files': 0,
            'skipped_files': 0,
            'backup_session': None
        }
    
    def initialize(self):
        """Initialize all components"""
        self.logger.info("Initializing Field/Method Renaming Tool...")
        
        # Validate configuration
        self.config.validate()
        
        # Initialize CSV reader
        self.csv_reader = CSVReader(self.config.csv_file)
        
        # Initialize file finder
        self.file_finder = FileFinder(self.config.repo_path)
        
        # Initialize backup manager
        if self.config.create_backups:
            backup_config = self.config.get_backup_config()
            self.backup_manager = BackupManager(**backup_config)
        
        # Initialize confirmation UI
        self.confirmation_ui = ConfirmationUI(auto_approve_all=not self.config.interactive_mode)
        
        # Initialize processors
        processor_config = self.config.get_processor_config()
        self.processors = {
            '.py': PythonProcessor(
                create_backups=self.config.create_backups,
                validate_syntax=self.config.validate_syntax
            ),
            '.xml': XMLProcessor(
                create_backups=self.config.create_backups,
                validate_syntax=self.config.validate_syntax
            )
        }
        
        # Set backup manager for processors
        if self.backup_manager:
            for processor in self.processors.values():
                processor.set_backup_manager(self.backup_manager)
        
        self.logger.info("Initialization completed successfully")
    
    def run(self) -> int:
        """
        Run the main processing workflow.
        
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Load changes from CSV
            self.logger.info("Loading changes from CSV...")
            changes = self.csv_reader.load_changes()
            self.stats['total_changes'] = len(changes)
            
            if not changes:
                print("✅ No changes found in CSV file.")
                return 0
            
            # Filter changes by modules if specified
            if self.config.modules:
                changes = self.csv_reader.filter_by_module(self.config.modules, changes)
                if not changes:
                    print(f"✅ No changes found for specified modules: {', '.join(self.config.modules)}")
                    return 0
            
            # Display initial statistics
            self._display_initial_stats(changes)
            
            # Group changes by module and model
            changes_by_model = self.csv_reader.group_by_model(changes)
            
            # Find files for each model
            self.logger.info("Discovering files...")
            file_changes = self._discover_files(changes_by_model)
            
            if not file_changes:
                print("⚠️  No files found for the specified changes.")
                return 0
            
            self.stats['total_files_found'] = len(file_changes)
            
            # Handle dry run mode
            if self.config.dry_run:
                self.confirmation_ui.display_dry_run_results(file_changes)
                return 0
            
            # Get user confirmation in interactive mode
            if self.config.interactive_mode:
                approved_files = self.confirmation_ui.confirm_batch_changes(file_changes)
                file_changes = {path: changes for path, changes in file_changes.items() 
                              if approved_files.get(path, False)}
                
                if not file_changes:
                    print("❌ No files approved for processing.")
                    return 0
            
            # Start backup session
            if self.backup_manager:
                session_dir = self.backup_manager.start_backup_session()
                self.stats['backup_session'] = str(session_dir)
                self.logger.info(f"Started backup session: {session_dir}")
            
            # Process files
            self.logger.info("Processing files...")
            results = self._process_files(file_changes)
            
            # Finalize backup session
            if self.backup_manager:
                self.backup_manager.finalize_session()
            
            # Display results
            self._display_results(results)
            
            # Format XML files after processing
            self._format_xml_files(results)
            
            # Generate report if requested
            if self.config.output_report:
                self._generate_report(results, changes)
            
            # Determine exit code
            failed_count = len([r for r in results if r.status == ProcessingStatus.ERROR])
            return 1 if failed_count > 0 else 0
            
        except KeyboardInterrupt:
            self.logger.info("Process interrupted by user")
            print("\n🛑 Process interrupted by user.")
            return 130
        except CSVValidationError as e:
            self.logger.error(f"CSV validation error: {e}")
            print(f"❌ CSV validation error: {e}")
            return 2
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            print(f"❌ Unexpected error: {e}")
            if self.config.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _display_initial_stats(self, changes: List[FieldChange]):
        """Display initial statistics about changes"""
        stats = self.csv_reader.get_statistics(changes)
        
        print(f"""
🔍 Field/Method Renaming Tool - Processing Summary:
   📂 Repository: {self.config.repo_path}
   📄 CSV File: {self.config.csv_file}
   
   📊 Changes to process:
      Total: {stats['total_changes']}
      Fields: {stats['field_changes']}
      Methods: {stats['method_changes']}
      Modules: {stats['unique_modules']}
      Models: {stats['unique_models']}
   
   ⚙️  Configuration:
      Interactive Mode: {'Yes' if self.config.interactive_mode else 'No'}
      Create Backups: {'Yes' if self.config.create_backups else 'No'}
      Validate Syntax: {'Yes' if self.config.validate_syntax else 'No'}
      File Types: {', '.join(self.config.file_types)}
      Dry Run: {'Yes' if self.config.dry_run else 'No'}
        """)
    
    def _discover_files(self, changes_by_model: Dict[str, List[FieldChange]]) -> Dict[Path, List[FieldChange]]:
        """
        Discover files that need to be processed.
        
        Args:
            changes_by_model: Changes grouped by model
            
        Returns:
            Dictionary mapping file paths to their changes
        """
        file_changes = {}
        
        for model_key, model_changes in changes_by_model.items():
            # Extract module and model from key
            module, model = model_key.split('.', 1)
            
            # Find files for this model
            file_set = self.file_finder.find_files_for_model(module, model)
            
            if file_set.is_empty():
                self.logger.warning(f"No files found for model {model_key}")
                continue
            
            # Process each type of file
            for file_list_name in ['python_files', 'view_files', 'data_files', 
                                 'demo_files', 'template_files', 'report_files', 'security_files']:
                file_list = getattr(file_set, file_list_name)
                
                # Check if this file type should be processed
                file_type = file_list_name.replace('_files', '')
                if file_type == 'python':
                    if not self.config.should_process_file_type('python'):
                        continue
                elif file_type == 'view':
                    if not self.config.should_process_file_type('views'):
                        continue
                elif file_type == 'template':
                    if not self.config.should_process_file_type('templates'):
                        continue
                elif file_type == 'report':
                    if not self.config.should_process_file_type('reports'):
                        continue
                else:
                    if not self.config.should_process_file_type(file_type):
                        continue
                
                # Add files to processing list
                for file_path in file_list:
                    if file_path not in file_changes:
                        file_changes[file_path] = []
                    file_changes[file_path].extend(model_changes)
        
        # Remove duplicates from each file's changes list
        for file_path in file_changes:
            unique_changes = []
            seen = set()
            for change in file_changes[file_path]:
                change_key = (change.old_name, change.new_name, change.module, change.model)
                if change_key not in seen:
                    unique_changes.append(change)
                    seen.add(change_key)
            file_changes[file_path] = unique_changes
        
        self.logger.info(f"Discovered {len(file_changes)} files to process")
        return file_changes
    
    def _process_files(self, file_changes: Dict[Path, List[FieldChange]]) -> List[ProcessResult]:
        """
        Process all files with their changes.
        
        Args:
            file_changes: Dictionary mapping file paths to their changes
            
        Returns:
            List of processing results
        """
        results = []
        total_files = len(file_changes)
        
        for i, (file_path, changes) in enumerate(file_changes.items(), 1):
            if not self.config.quiet:
                print(f"🔄 [{i}/{total_files}] Processing {file_path}...")
            
            # Get appropriate processor
            processor = self._get_processor_for_file(file_path)
            if not processor:
                self.logger.warning(f"No processor available for file: {file_path}")
                continue
            
            # Process file
            try:
                result = processor.process_file(file_path, changes)
                results.append(result)
                
                # Update statistics
                if result.is_success:
                    self.stats['successful_files'] += 1
                elif result.status == ProcessingStatus.ERROR:
                    self.stats['failed_files'] += 1
                elif result.status == ProcessingStatus.SKIPPED:
                    self.stats['skipped_files'] += 1
                
                # Log result
                if not self.config.quiet:
                    print(f"   {result}")
                
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {e}")
                if not self.config.quiet:
                    print(f"   ❌ Error: {e}")
        
        self.stats['total_files_processed'] = len(results)
        return results
    
    def _get_processor_for_file(self, file_path: Path) -> Optional:
        """Get appropriate processor for a file"""
        extension = file_path.suffix.lower()
        return self.processors.get(extension)
    
    def _display_results(self, results: List[ProcessResult]):
        """Display final processing results"""
        self.confirmation_ui.display_processing_results(results)
        
        # Additional backup information
        if self.backup_manager and self.stats['backup_session']:
            print(f"\n💾 Backup Information:")
            print(f"   Session: {self.stats['backup_session']}")
            
            backup_stats = self.backup_manager.get_backup_statistics()
            print(f"   Total backup size: {backup_stats.get('total_disk_usage', 0)} bytes")
    
    def _format_xml_files(self, results: List[ProcessResult]):
        """Format XML files after processing to ensure consistent indentation"""
        xml_files = []
        
        # Collect all successfully processed XML files
        for result in results:
            if (result.status == ProcessingStatus.SUCCESS and 
                result.file_path.suffix.lower() == '.xml' and
                result.changes_applied > 0):
                xml_files.append(result.file_path)
        
        if not xml_files:
            self.logger.debug("No XML files to format")
            return
        
        self.logger.info(f"Formatting {len(xml_files)} XML files...")
        print(f"\n🎨 Formatting {len(xml_files)} XML files for consistent indentation...")
        
        # Run the XML formatter
        formatter_path = current_dir / "format_odoo_xml.py"
        
        if not formatter_path.exists():
            self.logger.warning("XML formatter not found, skipping formatting")
            print("⚠️  XML formatter not found, skipping formatting")
            return
        
        formatted_count = 0
        failed_count = 0
        
        for xml_file in xml_files:
            try:
                result = subprocess.run(
                    [sys.executable, str(formatter_path), str(xml_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    formatted_count += 1
                    self.logger.debug(f"Formatted: {xml_file}")
                else:
                    failed_count += 1
                    self.logger.error(f"Failed to format {xml_file}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                failed_count += 1
                self.logger.error(f"Timeout formatting {xml_file}")
            except Exception as e:
                failed_count += 1
                self.logger.error(f"Error formatting {xml_file}: {e}")
        
        if formatted_count > 0:
            print(f"✅ Successfully formatted {formatted_count} XML files")
        if failed_count > 0:
            print(f"⚠️  Failed to format {failed_count} XML files (check logs for details)")
        
        self.logger.info(f"XML formatting completed: {formatted_count} success, {failed_count} failed")
    
    def _generate_report(self, results: List[ProcessResult], changes: List[FieldChange]):
        """Generate detailed report file"""
        report_data = {
            'summary': {
                'timestamp': self.csv_reader.get_statistics(changes),
                'configuration': {
                    'repo_path': str(self.config.repo_path),
                    'csv_file': str(self.config.csv_file),
                    'interactive_mode': self.config.interactive_mode,
                    'dry_run': self.config.dry_run,
                    'create_backups': self.config.create_backups,
                    'validate_syntax': self.config.validate_syntax,
                    'file_types': self.config.file_types
                },
                'statistics': self.stats
            },
            'changes': [
                {
                    'old_name': change.old_name,
                    'new_name': change.new_name,
                    'module': change.module,
                    'model': change.model,
                    'change_type': change.change_type
                }
                for change in changes
            ],
            'results': [
                {
                    'file_path': str(result.file_path),
                    'status': result.status.value,
                    'changes_applied': result.changes_applied,
                    'changes_details': result.changes_details,
                    'error_message': result.error_message,
                    'backup_path': str(result.backup_path) if result.backup_path else None
                }
                for result in results
            ]
        }
        
        try:
            with open(self.config.output_report, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"📊 Detailed report saved to: {self.config.output_report}")
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Create configuration
    config = RenamingConfig()
    
    # Override config with command line arguments
    config.csv_file = args.csv_file
    config.repo_path = args.repo_path
    config.interactive_mode = args.interactive
    config.dry_run = args.dry_run
    config.create_backups = not args.no_backup
    config.validate_syntax = not args.no_validation
    config.verbose = args.verbose
    config.quiet = args.quiet
    config.file_types = args.file_types
    
    if args.module:
        config.modules = [args.module]
    elif args.modules:
        config.modules = args.modules
    
    if args.output_report:
        config.output_report = args.output_report
    
    if args.backup_dir:
        config.backup_dir = args.backup_dir
    
    # Create and run tool
    tool = FieldMethodRenamingTool(config)
    tool.initialize()
    
    return tool.run()


if __name__ == '__main__':
    sys.exit(main())