"""
Main CLI entry point for Odoo Tools
"""

import logging
import sys
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).parent.parent))

from commands.detect import DetectCommand
from commands.rename import RenameCommand
from core.backup_manager import BackupManager
from core.base_processor import ProcessingStatus
from core.config import Config
from src.core.order import Order
from core.path_analyzer import PathAnalyzer, PathType
from odoo_tools import __version__

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(
    version=__version__,
    prog_name="odoo-sourcecode-tools",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file path",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress output",
)
@click.pass_context
def cli(
    ctx,
    config: str | None,
    verbose: bool,
    quiet: bool,
):
    """Unified Odoo Source Code Management Tool

    A comprehensive tool for managing Odoo source code including:
    - Code ordering and formatting
    - Field/method change detection
    - Automated renaming operations
    """
    # Initialize context
    ctx.ensure_object(dict)

    # Load configuration
    if config:
        config_path = Path(config)
        ctx.obj["config"] = Config.from_file(config_path)
    else:
        ctx.obj["config"] = Config.load_hierarchy(Path.cwd())

    # Apply CLI flags
    if verbose:
        ctx.obj["config"].verbose = True
        logging.getLogger().setLevel(logging.DEBUG)

    if quiet:
        ctx.obj["config"].quiet = True
        logging.getLogger().setLevel(logging.WARNING)


@cli.command()
@click.argument(
    "path",
    type=click.Path(exists=True),
)
def analyze(path: str):
    """Analyze a path to determine its type and recommended processing.

    This command inspects a file or directory to determine:
    - Whether it's an Odoo module, Python project, or mixed content
    - File type statistics (Python, XML, other)
    - Recommended processing targets

    Examples:
        odoo-tools analyze ./my_module
        odoo-tools analyze ./src/models.py
    """
    analyzer = PathAnalyzer()
    analysis = analyzer.analyze(Path(path))

    # Display analysis results
    click.echo(f"\nPath Analysis: {path}")
    click.echo("=" * 60)
    click.echo(f"Type: {analysis.path_type.value}")
    click.echo(f"Description: {analysis.description}")

    if analysis.is_directory:
        click.echo(f"\nFile Statistics:")
        if analysis.python_files:
            click.echo(f"  Python files: {len(analysis.python_files)}")
        if analysis.xml_files:
            click.echo(f"  XML files: {len(analysis.xml_files)}")
        if analysis.other_files:
            click.echo(f"  Other files: {len(analysis.other_files)}")

        if analysis.is_odoo_module:
            click.echo(f"\nOdoo Module Features:")
            click.echo(f"  Has manifest: {analysis.has_manifest}")
            click.echo(f"  Has models: {analysis.has_models}")
            click.echo(f"  Has views: {analysis.has_views}")
            click.echo(f"  Has security: {analysis.has_security}")

        if analysis.odoo_modules and len(analysis.odoo_modules) > 1:
            click.echo(f"\nDetected Odoo Modules:")
            for module in analysis.odoo_modules:
                click.echo(f"  - {module.name}")

    if analysis.recommended_targets:
        click.echo(f"\nRecommended Processing:")
        click.echo(analyzer.get_recommendation_string(analysis))
    else:
        click.echo(f"\nNo recommended processing for this path type.")


@cli.command()
@click.argument(
    "path",
    type=click.Path(exists=True),
)
@click.argument(
    "target",
    type=click.Choice(
        [
            "python_code",
            "python_field_attr",
            "xml_code",
            "xml_node_attr",
            "all",
            "auto",  # New auto option
        ],
    ),
    required=False,
    default="auto",
)
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="Process directories recursively",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without applying",
)
@click.option(
    "--no-backup",
    is_flag=True,
    help="Skip creating backup files",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Skip confirmation prompts",
)
@click.pass_context
def reorder(
    ctx,
    path: str,
    target: str,
    recursive: bool,
    dry_run: bool,
    no_backup: bool,
    force: bool,
):
    """Smart reordering command for Python and XML files

    Automatically detects path type and suggests appropriate processing.

    Targets:
    - auto: Automatically detect and apply appropriate reordering (default)
    - python_code: Reorder Python code structure
    - python_field_attr: Reorder field attributes only
    - xml_code: Reorder XML structure
    - xml_node_attr: Reorder XML attributes only
    - all: Apply all reordering operations

    Examples:
        odoo-tools reorder ./my_module           # Auto-detect and process
        odoo-tools reorder ./my_module all       # Process everything
        odoo-tools reorder ./models.py          # Auto-detect Python file
        odoo-tools reorder ./views xml_code     # Force XML structure reordering
    """
    config = ctx.obj["config"]
    config.dry_run = dry_run
    config.backup.enabled = not no_backup

    path_obj = Path(path)

    # Always analyze the path to avoid redundant checks
    analyzer = PathAnalyzer()
    analysis = analyzer.analyze(path_obj)

    # If target is auto, determine the best target
    if target == "auto":
        # Display analysis
        click.echo(f"\n📁 Analyzing: {path}")
        click.echo(f"   Type: {analysis.description}")

        # Determine best target based on analysis
        if not analysis.recommended_targets:
            click.echo("   ⚠️  No processing recommended for this path type.")
            sys.exit(0)

        # Choose the most comprehensive target from recommendations
        if "all" in analysis.recommended_targets:
            target = "all"
            click.echo(f"   ✓ Auto-selected: Process all (Python and XML)")
        elif (
            analysis.path_type == PathType.PYTHON_FILE
            or analysis.path_type == PathType.PYTHON_PROJECT
        ):
            target = "python_code"
            click.echo(f"   ✓ Auto-selected: Python code reordering")
        elif analysis.path_type == PathType.XML_FILE:
            target = "xml_code"
            click.echo(f"   ✓ Auto-selected: XML structure reordering")
        elif analysis.path_type == PathType.ODOO_MODULE:
            target = "all"
            click.echo(f"   ✓ Auto-selected: Process all (Odoo module)")
        elif analysis.path_type == PathType.ODOO_MODULES_DIR:
            target = "all"
            click.echo(
                f"   ✓ Auto-selected: Process all ({len(analysis.odoo_modules)} modules)"
            )
        else:
            # Default to all for mixed projects
            target = "all"
            click.echo(f"   ✓ Auto-selected: Process all (mixed content)")

        # Show what will be processed
        if analysis.python_files:
            click.echo(f"   📄 Python files: {len(analysis.python_files)}")
        if analysis.xml_files:
            click.echo(f"   📄 XML files: {len(analysis.xml_files)}")

        # Confirm unless forced
        if not force and not dry_run:
            if not click.confirm("\nProceed with reordering?"):
                click.echo("Operation cancelled.")
                sys.exit(0)

    # Convert PathAnalysis to dict for the command
    path_info = {
        "is_file": analysis.is_file,
        "is_dir": analysis.is_directory,
        "python_files": analysis.python_files,
        "xml_files": analysis.xml_files,
        "total_files": analysis.total_files,
    }

    # Initialize backup manager if needed
    backup_manager = None
    if config.backup.enabled and not dry_run:
        backup_manager = BackupManager(
            backup_dir=config.backup.directory,
            compression=config.backup.compression,
            keep_sessions=config.backup.keep_sessions,
        )
        # Start backup session
        session_type = f"reorder_{target}"
        backup_manager.start_session(session_type)

    # Execute the reordering using Order directly
    ordering = Order(config)
    options = {}

    click.echo(f"\n🔧 Processing with target: {target}")

    # Use getattr to dynamically call the appropriate method
    method_name = f"process_{target}" if target != "all" else "process_all"
    if hasattr(ordering, method_name):
        process_method = getattr(ordering, method_name)
        result = process_method(
            path_obj,
            path_info=path_info,
            **options,
        )
    else:
        click.echo(f"❌ Unknown target: {target}")
        sys.exit(1)

    # Finalize backup session if needed
    if backup_manager and not dry_run:
        backup_manager.finalize_session()

    # Exit with appropriate code
    if result.status == ProcessingStatus.SUCCESS:
        click.echo("✅ Reordering completed successfully!")
        sys.exit(0)
    else:
        click.echo("❌ Reordering failed!")
        sys.exit(1)


@cli.command()
@click.option(
    "--from",
    "from_commit",
    help="Starting commit SHA",
)
@click.option(
    "--to",
    "to_commit",
    help="Ending commit SHA",
)
@click.option(
    "--output",
    "-o",
    default="changes.csv",
    help="Output CSV file",
)
@click.option(
    "--repo",
    type=click.Path(exists=True),
    help="Repository path",
)
@click.option(
    "--module",
    "-m",
    help="Specific module to analyze",
)
@click.option(
    "--threshold",
    "-t",
    type=float,
    default=0.75,
    help="Confidence threshold (0-1)",
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Interactive validation mode",
)
@click.pass_context
def detect(
    ctx,
    from_commit: str | None,
    to_commit: str | None,
    output: str,
    repo: str | None,
    module: str | None,
    threshold: float,
    interactive: bool,
):
    """Detect renamed fields and methods between commits

    Analyzes Git history to identify potential field and method renames
    in Odoo modules, outputting results to a CSV file.
    """
    config = ctx.obj["config"]

    if repo:
        config.repo_path = repo

    if module:
        config.modules = [module]

    config.detection.confidence_threshold = threshold
    config.interactive = interactive

    command = DetectCommand(config)
    result = command.execute(from_commit, to_commit, output)

    sys.exit(0 if result.status == ProcessingStatus.SUCCESS else 1)


@cli.command()
@click.argument(
    "csv_file",
    type=click.Path(exists=True),
)
@click.option(
    "--repo",
    type=click.Path(exists=True),
    required=True,
    help="Repository path",
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Confirm each change interactively",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without applying",
)
@click.option(
    "--no-backup",
    is_flag=True,
    help="Skip creating backups",
)
@click.option(
    "--module",
    "-m",
    help="Process only specific module",
)
@click.pass_context
def rename(
    ctx,
    csv_file: str,
    repo: str,
    interactive: bool,
    dry_run: bool,
    no_backup: bool,
    module: str | None,
):
    """Apply field/method name changes from CSV

    Reads a CSV file containing field/method renames and applies them
    across Python and XML files in the Odoo repository.
    """
    config = ctx.obj["config"]
    config.repo_path = repo
    config.interactive = interactive
    config.dry_run = dry_run
    config.backup.enabled = not no_backup

    if module:
        config.modules = [module]

    command = RenameCommand(config)
    result = command.execute(Path(csv_file))

    sys.exit(0 if result.status == ProcessingStatus.SUCCESS else 1)


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize configuration in current directory

    Creates a default .odoo-tools.yaml configuration file in the current
    directory with sensible defaults for Odoo development.
    """
    config_path = Path.cwd() / ".odoo-tools.yaml"

    if config_path.exists():
        click.confirm(f"{config_path} already exists. Overwrite?", abort=True)

    # Create default configuration
    default_config = Config()
    default_config.save(config_path)

    click.echo(f"Created configuration file: {config_path}")
    click.echo("Edit this file to customize your settings.")


@cli.command()
@click.option(
    "--sessions",
    is_flag=True,
    help="List backup sessions",
)
@click.option(
    "--restore",
    help="Restore from backup session ID",
)
@click.option(
    "--clean",
    is_flag=True,
    help="Clean old backup sessions",
)
@click.pass_context
def backup(
    ctx,
    sessions: bool,
    restore: str | None,
    clean: bool,
):
    """Manage backup sessions

    View, restore, or clean backup sessions created during tool operations.
    """
    config = ctx.obj["config"]

    # Import backup manager directly
    from core.backup_manager import BackupManager

    manager = BackupManager(
        backup_dir=config.backup.directory,
        compression=config.backup.compression,
        keep_sessions=config.backup.keep_sessions,
    )

    if sessions:
        # List all sessions
        all_sessions = manager.list_sessions()
        if not all_sessions:
            click.echo("No backup sessions found.")
        else:
            click.echo(f"Found {len(all_sessions)} backup sessions:")
            for session in all_sessions:
                click.echo(f"  - {session['session_id']} ({session['timestamp']})")
                if "files_backed_up" in session:
                    click.echo(f"    Files: {len(session['files_backed_up'])}")

    elif restore:
        # Restore specific session
        click.confirm(f"Restore all files from session {restore}?", abort=True)
        if manager.restore_session(restore):
            click.echo(f"Successfully restored session: {restore}")
        else:
            click.echo(f"Failed to restore session: {restore}", err=True)
            sys.exit(1)

    elif clean:
        # Clean old sessions
        click.confirm(
            f"Remove backup sessions older than {config.backup.keep_sessions} most recent?",
            abort=True,
        )
        manager._cleanup_old_sessions()
        click.echo("Cleaned old backup sessions.")

    else:
        click.echo("Use --sessions, --restore, or --clean")


def main():
    """Main entry point"""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user.", err=True)
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if "--verbose" in sys.argv or "-v" in sys.argv:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
