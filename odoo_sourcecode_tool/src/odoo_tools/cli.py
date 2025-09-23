"""
Main CLI entry point for Odoo Tools
"""

import logging
import sys
from pathlib import Path

import click

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config
from odoo_tools import __version__

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(
    version=__version__,
    prog_name="odoo-tools",
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
    "target",
    type=click.Choice(["code", "attributes", "xml", "all"]),
)
@click.argument(
    "path",
    type=click.Path(exists=True),
)
@click.option(
    "--strategy",
    type=click.Choice(["semantic", "type", "strict"]),
    default="semantic",
    help="Field ordering strategy (for 'code' target)",
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
@click.pass_context
def reorder(
    ctx,
    target: str,
    path: str,
    strategy: str,
    recursive: bool,
    dry_run: bool,
    no_backup: bool,
):
    """Unified reordering command for Python and XML files

    Targets:
    - code: Reorder fields, methods, and imports in Python files
    - attributes: Reorder field attributes within field definitions
    - xml: Reorder XML element attributes
    - all: Apply all reordering operations

    Examples:
        odoo-tools reorder code ./module --strategy semantic
        odoo-tools reorder attributes ./module
        odoo-tools reorder xml ./module/views
        odoo-tools reorder all ./module
    """
    config = ctx.obj["config"]
    config.dry_run = dry_run
    config.backup.enabled = not no_backup

    # Import unified command module
    from commands.reorder import UnifiedReorderCommand

    command = UnifiedReorderCommand(config)
    options = {}
    if target == "code" and strategy:
        options["strategy"] = strategy

    result = command.execute(target, Path(path), recursive, **options)

    # Exit with appropriate code
    sys.exit(0 if result else 1)


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

    # Import command module
    from commands.detect import DetectCommand

    command = DetectCommand(config)
    result = command.execute(from_commit, to_commit, output)

    sys.exit(0 if result else 1)


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

    # Import command module
    from commands.rename import RenameCommand

    command = RenameCommand(config)
    result = command.execute(Path(csv_file))

    sys.exit(0 if result else 1)


@cli.command()
@click.argument(
    "config_file",
    type=click.Path(),
)
@click.option(
    "--pipeline",
    "-p",
    help="Pipeline name to execute",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview workflow without executing",
)
@click.pass_context
def workflow(
    ctx,
    config_file: str,
    pipeline: str | None,
    dry_run: bool,
):
    """Execute predefined workflows

    Runs complex multi-step workflows defined in configuration files,
    allowing chaining of detection, ordering, and renaming operations.
    """
    config = ctx.obj["config"]
    config.dry_run = dry_run

    # Import command module
    from commands.workflow import WorkflowCommand

    command = WorkflowCommand(config)
    result = command.execute(Path(config_file), pipeline)

    sys.exit(0 if result else 1)


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
