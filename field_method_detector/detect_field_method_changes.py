#!/usr/bin/env python3
"""
Odoo Field/Method Change Detector
==================================

Interactive script to detect renamed fields and methods between Git commits
using AST parsing and AgroMarin naming conventions.

Usage:
    python detect_field_method_changes.py --json-file modified_modules.json [options]

Example:
    # Interactive mode with auto-detected commits
    python detect_field_method_changes.py -i --json-file modified_modules.json
    
    # Automatic mode with specific commits
    python detect_field_method_changes.py --json-file modified_modules.json \
        --commit-from abc123 --commit-to def456 --confidence-threshold 0.80
"""
import sys
import os
import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from analyzers.git_analyzer import GitAnalyzer, GitRepositoryError
from analyzers.ast_parser import CodeInventoryExtractor
from analyzers.matching_engine import MatchingEngine, RenameCandidate
from interactive.validation_ui import InteractiveValidator
from utils.csv_manager import CSVManager
from config.settings import config, Config


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from some modules
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Detect field and method name changes in Odoo modules',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i --json-file modified_modules.json --repo-path /path/to/odoo
  %(prog)s --json-file modified_modules.json --commit-from abc123 --commit-to def456 --repo-path /path/to/odoo
  %(prog)s -i --json-file modified_modules.json --confidence-threshold 0.80 --output changes.csv --repo-path /path/to/odoo
  %(prog)s -m account --json-file modified_modules.json --repo-path /path/to/odoo --verbose
  %(prog)s --modules account sale fleet --json-file modified_modules.json --repo-path /path/to/odoo
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--json-file', 
        required=True,
        help='Path to modified_modules.json file'
    )
    
    # Optional arguments
    parser.add_argument(
        '--commit-from',
        help='Starting commit SHA (auto-detect if not provided)'
    )
    
    parser.add_argument(
        '--commit-to',
        help='Ending commit SHA (from JSON if not provided)'
    )
    
    parser.add_argument(
        '--repo-path',
        help='Git repository path (auto-detect if not provided)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='odoo_field_changes_detected.csv',
        help='Output CSV file (default: %(default)s)'
    )
    
    parser.add_argument(
        '--confidence-threshold', '-t',
        type=float,
        default=0.75,
        help='Confidence threshold for auto-approval (default: %(default)s)'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Enable interactive validation mode'
    )
    
    parser.add_argument(
        '--batch-mode',
        action='store_true',
        help='Enable batch processing for similar patterns'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--report-file',
        help='Export detailed report to this file'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run analysis without writing to CSV'
    )
    
    parser.add_argument(
        '--module', '-m',
        help='Analyze only specific module (if omitted, all modules are analyzed)'
    )
    
    parser.add_argument(
        '--modules',
        nargs='+',
        help='Analyze only specific modules (space-separated list)'
    )
    
    return parser.parse_args()


def load_modified_modules_json(json_file_path: str) -> Dict:
    """Load and validate modified modules JSON file"""
    json_path = Path(json_file_path)
    
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_file_path}")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate required structure
        if 'modified_modules' not in data:
            raise ValueError("JSON file missing 'modified_modules' key")
        
        logger.info(f"Loaded JSON with {len(data['modified_modules'])} modified modules")
        
        return data
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON file: {e}")


def analyze_module_files(module_data: Dict, git_analyzer: GitAnalyzer, 
                        commit_from: str, commit_to: str,
                        extractor: CodeInventoryExtractor,
                        matching_engine: MatchingEngine) -> List[RenameCandidate]:
    """Analyze files in a module for rename candidates"""
    module_name = module_data['module_name']
    candidates = []
    
    # Focus on model files and wizards
    relevant_files = []
    
    for category in ['models', 'wizards']:
        if category in module_data.get('file_categories', {}):
            relevant_files.extend(module_data['file_categories'][category])
    
    logger.info(f"Analyzing {len(relevant_files)} files in module '{module_name}'")
    
    for file_path in relevant_files:
        if not file_path.endswith('.py'):
            continue
            
        try:
            # Get file content at both commits
            content_before = git_analyzer.get_file_content_at_commit(file_path, commit_from)
            content_after = git_analyzer.get_file_content_at_commit(file_path, commit_to)
            
            if not content_before or not content_after:
                logger.debug(f"File {file_path} not found in one of the commits, skipping")
                continue
            
            # Extract inventories
            inventory_before = extractor.extract_inventory(content_before, file_path)
            inventory_after = extractor.extract_inventory(content_after, file_path)
            
            # Debug logging for inventories
            logger.debug(f"\n{'='*80}")
            logger.debug(f"ANALYZING FILE: {file_path}")
            logger.debug(f"{'='*80}")
            
            # Log inventory before
            logger.debug(f"COMMIT BEFORE ({commit_from[:8]}):")
            logger.debug(f"  Fields ({len(inventory_before.get('fields', []))}): {[f['name'] for f in inventory_before.get('fields', [])]}")
            logger.debug(f"  Methods ({len(inventory_before.get('methods', []))}): {[m['name'] for m in inventory_before.get('methods', [])]}")
            
            # Log inventory after
            logger.debug(f"COMMIT AFTER ({commit_to[:8]}):")
            logger.debug(f"  Fields ({len(inventory_after.get('fields', []))}): {[f['name'] for f in inventory_after.get('fields', [])]}")
            logger.debug(f"  Methods ({len(inventory_after.get('methods', []))}): {[m['name'] for m in inventory_after.get('methods', [])]}")
            
            # Find renames
            file_candidates = matching_engine.find_renames_in_inventories(
                inventory_before, inventory_after, module_name, file_path
            )
            
            candidates.extend(file_candidates)
            
            if file_candidates:
                logger.debug(f"✅ FOUND {len(file_candidates)} rename candidates:")
                for candidate in file_candidates:
                    logger.debug(f"   {candidate.old_name} → {candidate.new_name} (confidence: {candidate.confidence:.2f})")
            else:
                logger.debug(f"❌ No rename candidates found")
            
            logger.debug(f"{'='*80}\n")
                
        except Exception as e:
            logger.warning(f"Error analyzing file {file_path}: {e}")
            continue
    
    return candidates


def main():
    """Main function"""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.verbose)
    
    global logger
    logger = logging.getLogger(__name__)
    
    try:
        # Load and validate inputs
        logger.info("Loading modified modules JSON...")
        modules_data = load_modified_modules_json(args.json_file)
        
        # Initialize configuration
        app_config = Config()
        app_config.confidence_threshold = args.confidence_threshold
        app_config.interactive_mode = args.interactive
        app_config.batch_mode = args.batch_mode
        app_config.verbose = args.verbose
        app_config.output_csv = args.output
        app_config.report_file = args.report_file
        
        # Determine repository path
        repo_path = args.repo_path or app_config.get_repo_path_from_json(args.json_file)
        logger.info(f"Using repository path: {repo_path}")
        
        # Initialize Git analyzer
        logger.info("Initializing Git analyzer...")
        git_analyzer = GitAnalyzer(repo_path)
        
        # Resolve commits
        logger.info("Resolving commits...")
        commit_from, commit_to = git_analyzer.resolve_commits(
            args.commit_from, args.commit_to, modules_data
        )
        
        # Show commit information
        commit_from_info = git_analyzer.get_commit_info(commit_from)
        commit_to_info = git_analyzer.get_commit_info(commit_to)
        
        # Module filtering info for display
        module_filter_info = ""
        if args.module:
            module_filter_info = f"\n   🎯 Módulo específico: {args.module}"
        elif args.modules:
            module_filter_info = f"\n   🎯 Módulos específicos: {', '.join(args.modules)}"
        
        print(f"""
🔍 Análisis de Cambios de Nombres - Configuración:
   📂 Repositorio: {repo_path}
   📊 Total módulos modificados: {len(modules_data['modified_modules'])}{module_filter_info}
   
   📅 Commits a comparar:
      Desde: {commit_from[:8]} - {commit_from_info['message'][:50]}...
      Hasta: {commit_to[:8]} - {commit_to_info['message'][:50]}...
   
   ⚙️  Configuración:
      Umbral de confianza: {app_config.confidence_threshold:.1%}
      Modo interactivo: {'Sí' if app_config.interactive_mode else 'No'}
      Archivo de salida: {app_config.output_csv}
        """)
        
        # Initialize components
        extractor = CodeInventoryExtractor()
        matching_engine = MatchingEngine()
        csv_manager = CSVManager(app_config.output_csv)
        
        # Load existing CSV records
        logger.info("Loading existing CSV records...")
        existing_records = csv_manager.load_existing_csv()
        
        # Filter modules if specified
        modules_to_analyze = modules_data['modified_modules']
        
        if args.module:
            # Single module specified
            modules_to_analyze = [m for m in modules_to_analyze if m['module_name'] == args.module]
            if not modules_to_analyze:
                logger.error(f"Module '{args.module}' not found in modified modules")
                return 4
            logger.info(f"Analyzing single module: {args.module}")
            
        elif args.modules:
            # Multiple modules specified
            specified_modules = set(args.modules)
            modules_to_analyze = [m for m in modules_to_analyze if m['module_name'] in specified_modules]
            
            found_modules = {m['module_name'] for m in modules_to_analyze}
            missing_modules = specified_modules - found_modules
            
            if missing_modules:
                logger.warning(f"Modules not found in modified modules: {', '.join(missing_modules)}")
            
            if not modules_to_analyze:
                logger.error("None of the specified modules were found in modified modules")
                return 4
                
            logger.info(f"Analyzing {len(modules_to_analyze)} specified modules: {', '.join(found_modules)}")
        
        else:
            logger.info(f"Analyzing all {len(modules_to_analyze)} modified modules")
        
        # Analyze selected modules
        logger.info("Starting analysis of selected modules...")
        all_candidates = []
        
        for i, module_data in enumerate(modules_to_analyze, 1):
            module_name = module_data['module_name']
            logger.info(f"[{i}/{len(modules_to_analyze)}] Analyzing module: {module_name}")
            
            module_candidates = analyze_module_files(
                module_data, git_analyzer, commit_from, commit_to,
                extractor, matching_engine
            )
            
            all_candidates.extend(module_candidates)
        
        logger.info(f"Analysis complete. Found {len(all_candidates)} potential renames")
        
        if not all_candidates:
            print("\n✅ No se detectaron cambios de nombres de campos o métodos.")
            return 0
        
        # Filter out duplicates
        new_candidates, duplicate_candidates = csv_manager.filter_new_candidates(all_candidates)
        
        if duplicate_candidates:
            logger.info(f"Filtered out {len(duplicate_candidates)} duplicates")
        
        if not new_candidates:
            print(f"\n✅ Todos los {len(all_candidates)} cambios detectados ya están en el CSV.")
            return 0
        
        # Interactive validation or automatic processing
        if app_config.interactive_mode:
            # Interactive validation
            validator = InteractiveValidator(
                confidence_threshold=app_config.confidence_threshold,
                auto_approve_threshold=0.90
            )
            
            approved_candidates, validation_summary = validator.validate_candidates(new_candidates)
            
            if not approved_candidates:
                print("\n❌ No se aprobaron cambios para incluir en el CSV.")
                return 0
            
        else:
            # Automatic processing - only high confidence
            approved_candidates = [
                c for c in new_candidates 
                if c.confidence >= app_config.confidence_threshold
            ]
            
            validation_summary = {
                'total_detected': len(new_candidates),
                'total_approved': len(approved_candidates),
                'auto_approved': len(approved_candidates),
                'manually_approved': 0,
                'auto_rejected': len(new_candidates) - len(approved_candidates)
            }
            
            print(f"""
📊 Procesamiento Automático:
   • Total detectados: {validation_summary['total_detected']}
   • Auto-aprobados (≥{app_config.confidence_threshold:.0%}): {validation_summary['auto_approved']}
   • Auto-rechazados (<{app_config.confidence_threshold:.0%}): {validation_summary['auto_rejected']}
            """)
        
        # Write to CSV unless dry run
        if args.dry_run:
            logger.info(f"DRY RUN: Would add {len(approved_candidates)} records to CSV")
        else:
            # Add approved candidates to CSV
            records_added = csv_manager.add_candidates_to_csv(approved_candidates)
            logger.info(f"Added {records_added} new records to CSV")
        
        # Export detailed report if requested
        if app_config.report_file and approved_candidates:
            csv_manager.export_candidates_report(approved_candidates, app_config.report_file)
        
        # Show final summary
        if app_config.interactive_mode:
            validator.show_final_summary(approved_candidates, validation_summary, app_config.output_csv)
        else:
            print(f"""
✅ Proceso completado exitosamente:
   💾 Archivo CSV: {app_config.output_csv}
   📝 Registros añadidos: {len(approved_candidates)}
   📊 Total registros en CSV: {len(existing_records) + len(approved_candidates)}
            """)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 130
    except GitRepositoryError as e:
        logger.error(f"Git repository error: {e}")
        return 1
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 2
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return 3
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())