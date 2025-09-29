"""
Unified path analysis and file type registry for intelligent file handling.

This module combines path analysis with file type detection and handling,
providing a single source of truth for:
- File type detection and categorization
- Path type analysis (files, directories, Odoo modules)
- Processing recommendations and capabilities
- Handler registration and dispatch
- Standardized file processing with backup support
"""

import json
import logging
import shutil
import tarfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ============================================================
# Processing Status and Results
# ============================================================

class ProcessingStatus(Enum):
    """Status of processing operation"""

    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"
    NO_CHANGES = "no_changes"


@dataclass
class ProcessResult:
    """Result of a processing operation"""

    file_path: Path
    status: ProcessingStatus
    changes_applied: int = 0
    changes_details: list[dict[str, Any]] = None
    error_message: str | None = None
    backup_path: Path | None = None

    @property
    def is_success(self) -> bool:
        """Check if processing was successful"""
        return self.status in [ProcessingStatus.SUCCESS, ProcessingStatus.NO_CHANGES]

    def __str__(self) -> str:
        """String representation"""
        if self.status == ProcessingStatus.SUCCESS:
            return f"✓ {self.file_path.name}: {self.changes_applied} changes applied"
        elif self.status == ProcessingStatus.NO_CHANGES:
            return f"= {self.file_path.name}: No changes needed"
        elif self.status == ProcessingStatus.SKIPPED:
            return f"⊝ {self.file_path.name}: Skipped"
        else:
            return f"✗ {self.file_path.name}: {self.error_message}"


class FileType(Enum):
    """Enumeration of supported file types"""

    PYTHON = "python"
    XML = "xml"
    YAML = "yaml"
    CSV = "csv"
    JAVASCRIPT = "javascript"
    MARKDOWN = "markdown"
    JSON = "json"
    UNKNOWN = "unknown"


class PathType(Enum):
    """Enumeration of path types that can be detected"""

    PYTHON_FILE = "python_file"
    XML_FILE = "xml_file"
    OTHER_FILE = "other_file"
    ODOO_MODULE = "odoo_module"
    ODOO_MODULES_DIR = "odoo_modules_directory"
    PYTHON_PROJECT = "python_project"
    MIXED_PROJECT = "mixed_project"
    EMPTY_DIR = "empty_directory"
    UNKNOWN = "unknown"


@dataclass
class FileTypeInfo:
    """Information about a file type"""

    type: FileType
    extensions: set[str]
    description: str
    can_order: bool = False  # Can be reordered
    can_rename: bool = False  # Can have renames applied
    is_odoo_specific: bool = False  # Odoo-specific file type


@dataclass
class PathAnalysis:
    """Result of path analysis with detailed information"""

    path: Path
    path_type: PathType
    file_type: FileType = FileType.UNKNOWN  # For single files
    is_directory: bool = False
    is_file: bool = False

    # File statistics
    python_files: list[Path] = field(default_factory=list)
    xml_files: list[Path] = field(default_factory=list)
    other_files: list[Path] = field(default_factory=list)
    total_files: int = 0

    # Odoo-specific
    is_odoo_module: bool = False
    is_odoo_modules_dir: bool = False
    odoo_modules: list[Path] = field(default_factory=list)
    has_manifest: bool = False
    has_models: bool = False
    has_views: bool = False
    has_security: bool = False

    # Processing recommendations
    description: str = ""
    recommended_targets: list[str] = field(default_factory=list)


class PathAnalyzer:
    """
    Unified path analyzer and file type registry.

    Combines intelligent path/directory analysis with file type
    detection and handler management.
    """

    def __init__(self):
        """Initialize the analyzer with file type registry"""
        self._registry: dict[FileType, FileTypeInfo] = {}
        self._extension_map: dict[str, FileType] = {}
        self._handlers: dict[FileType, dict[str, Callable]] = {}
        self._backup_manager: Any | None = None  # Lazy-initialized BackupManager
        self._initialize_registry()

    def _initialize_registry(self):
        """Initialize the default file type registry"""
        # Python files
        self.register_file_type(
            FileTypeInfo(
                type=FileType.PYTHON,
                extensions={".py", ".pyw"},
                description="Python source files",
                can_order=True,
                can_rename=True,
                is_odoo_specific=False,
            )
        )

        # XML files
        self.register_file_type(
            FileTypeInfo(
                type=FileType.XML,
                extensions={".xml"},
                description="XML files (views, data, actions)",
                can_order=True,
                can_rename=True,
                is_odoo_specific=True,
            )
        )

        # YAML files
        self.register_file_type(
            FileTypeInfo(
                type=FileType.YAML,
                extensions={".yaml", ".yml"},
                description="YAML configuration files",
                can_order=False,
                can_rename=False,
                is_odoo_specific=False,
            )
        )

        # CSV files
        self.register_file_type(
            FileTypeInfo(
                type=FileType.CSV,
                extensions={".csv"},
                description="CSV data files",
                can_order=False,
                can_rename=False,
                is_odoo_specific=True,
            )
        )

        # JavaScript files
        self.register_file_type(
            FileTypeInfo(
                type=FileType.JAVASCRIPT,
                extensions={".js", ".mjs"},
                description="JavaScript files",
                can_order=False,
                can_rename=True,
                is_odoo_specific=False,
            )
        )

        # Markdown files
        self.register_file_type(
            FileTypeInfo(
                type=FileType.MARKDOWN,
                extensions={".md", ".markdown"},
                description="Markdown documentation files",
                can_order=False,
                can_rename=False,
                is_odoo_specific=False,
            )
        )

        # JSON files
        self.register_file_type(
            FileTypeInfo(
                type=FileType.JSON,
                extensions={".json"},
                description="JSON data files",
                can_order=False,
                can_rename=False,
                is_odoo_specific=False,
            )
        )

    # ========================================================================
    # FILE TYPE REGISTRY METHODS
    # ========================================================================

    def register_file_type(self, info: FileTypeInfo):
        """Register a new file type"""
        self._registry[info.type] = info
        for ext in info.extensions:
            self._extension_map[ext.lower()] = info.type

    def register_handler(
        self,
        file_type: FileType,
        action: str,
        handler: Callable,
    ):
        """Register a handler for a specific file type and action"""
        if file_type not in self._handlers:
            self._handlers[file_type] = {}
        self._handlers[file_type][action] = handler
        logger.debug(f"Registered handler for {file_type.value}:{action}")

    def get_file_type(self, path: Path) -> FileType:
        """Detect file type from path"""
        suffix = path.suffix.lower()
        return self._extension_map.get(suffix, FileType.UNKNOWN)

    def get_file_info(self, path: Path) -> FileTypeInfo | None:
        """Get file type information for a path"""
        file_type = self.get_file_type(path)
        return self._registry.get(file_type)

    def get_handler(
        self,
        file_type: FileType,
        action: str,
    ) -> Callable | None:
        """Get handler for a file type and action"""
        if file_type in self._handlers:
            return self._handlers[file_type].get(action)
        return None

    def can_process(
        self,
        path: Path,
        action: str,
    ) -> bool:
        """Check if a file can be processed with the given action"""
        info = self.get_file_info(path)
        if not info:
            return False

        # Check capabilities based on action
        if action == "order":
            return info.can_order
        elif action == "rename":
            return info.can_rename
        else:
            # Check if handler exists
            return self.get_handler(info.type, action) is not None

    def process_file(
        self,
        path: Path,
        action: str,
        **kwargs,
    ):
        """Process a file with the appropriate handler"""
        file_type = self.get_file_type(path)
        handler = self.get_handler(file_type, action)

        if not handler:
            logger.warning(
                f"No handler found for {file_type.value}:{action} for file {path}"
            )
            return None

        logger.debug(f"Processing {path} with {file_type.value}:{action}")
        return handler(path, **kwargs)

    # ========================================================================
    # FILE PROCESSING WITH BACKUP SUPPORT
    # ========================================================================

    def with_backup(self, config: Any | None = None) -> "PathAnalyzer":
        """
        Enable backup support for this analyzer.

        Args:
            config: Configuration object with backup settings

        Returns:
            Self for method chaining
        """
        if config and hasattr(config, "backup") and config.backup.enabled:
            self._backup_manager = BackupManager(
                backup_dir=config.backup.directory,
                compression=config.backup.compression,
                keep_sessions=config.backup.keep_sessions,
            )
        return self

    def process_file_with_transform(
        self,
        file_path: Path,
        transformer: Callable[[str], str | tuple[str, dict]],
        dry_run: bool = False,
        backup: bool = True,
        encoding: str = "utf-8",
    ) -> ProcessResult:
        """
        Standard file processing pattern with transformation.

        Provides a unified way to:
        1. Backup files (if enabled)
        2. Read file content
        3. Apply transformation
        4. Check for changes
        5. Write changes (or preview in dry-run)
        6. Return standardized result

        Args:
            file_path: Path to file to process
            transformer: Function that takes content and returns new content
                        Can return (content, metadata) tuple for ProcessResult
            dry_run: If True, don't write changes
            backup: If True and backup_manager exists, backup file first
            encoding: File encoding (default: utf-8)

        Returns:
            ProcessResult with status and optional metadata

        Example:
            >>> def uppercase_transform(content):
            ...     return content.upper(), {"lines_changed": len(content.splitlines())}
            >>> analyzer = PathAnalyzer().with_backup(config)
            >>> result = analyzer.process_file_with_transform(
            ...     Path("file.txt"),
            ...     uppercase_transform,
            ...     dry_run=False
            ... )
        """
        try:
            # 1. Backup if enabled
            if backup and self._backup_manager and not dry_run:
                self._backup_manager.backup_file(file_path)

            # 2. Read
            original_content = file_path.read_text(encoding=encoding)

            # 3. Transform
            result = transformer(original_content)
            if isinstance(result, tuple):
                new_content, metadata = result
            else:
                new_content, metadata = result, {}

            # 4. Check for changes
            if new_content == original_content:
                logger.debug(f"No changes needed for {file_path}")
                return ProcessResult(
                    file_path=file_path, status=ProcessingStatus.NO_CHANGES
                )

            # 5. Write or dry-run
            if dry_run:
                logger.info(f"[DRY RUN] Would modify {file_path}")
            else:
                file_path.write_text(new_content, encoding=encoding)
                logger.info(f"Modified {file_path}")

            # 6. Return result with metadata
            return ProcessResult(
                file_path=file_path,
                status=ProcessingStatus.SUCCESS,
                changes_applied=metadata.get("changes_count", 1),
            )

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return ProcessResult(
                file_path=file_path, status=ProcessingStatus.ERROR, error_message=str(e)
            )

    def start_backup_session(self, description: str = None) -> Path | None:
        """
        Start a backup session if backup is enabled.

        Args:
            description: Optional description for the session

        Returns:
            Path to backup directory if started, None otherwise
        """
        if self._backup_manager:
            return self._backup_manager.start_session(description)
        return None

    def finalize_backup_session(self) -> Path | None:
        """
        Finalize current backup session.

        Returns:
            Path to backup directory or archive if finalized, None otherwise
        """
        if self._backup_manager:
            return self._backup_manager.finalize_session()
        return None

    def process_files(
        self,
        files: list[Path],
        transformer: Callable[[str], str | tuple[str, dict]],
        dry_run: bool = False,
        backup: bool = True,
        session_description: str = None,
    ) -> list[ProcessResult]:
        """
        Process multiple files with the same transformer.

        Manages a backup session for all files if backup is enabled.

        Args:
            files: List of file paths to process
            transformer: Transformation function to apply
            dry_run: If True, don't write changes
            backup: If True and backup_manager exists, backup files
            session_description: Description for backup session

        Returns:
            List of ProcessResult objects for each file
        """
        results = []

        # Start backup session if needed
        if backup and self._backup_manager and not dry_run:
            self.start_backup_session(session_description)

        try:
            for file_path in files:
                result = self.process_file_with_transform(
                    file_path, transformer, dry_run=dry_run, backup=backup
                )
                results.append(result)

        finally:
            # Finalize backup session
            if backup and self._backup_manager and not dry_run:
                self.finalize_backup_session()

        return results

    # ========================================================================
    # PATH ANALYSIS METHODS
    # ========================================================================

    def analyze(self, path: Path) -> PathAnalysis:
        """
        Analyze a path and return detailed information.

        Args:
            path: File or directory path to analyze

        Returns:
            PathAnalysis object with detailed information
        """
        if not path.exists():
            return PathAnalysis(
                path=path,
                path_type=PathType.UNKNOWN,
                description=f"Path does not exist: {path}",
            )

        if path.is_file():
            return self._analyze_file(path)
        else:
            return self._analyze_directory(path)

    def _analyze_file(self, path: Path) -> PathAnalysis:
        """Analyze a single file"""
        analysis = PathAnalysis(
            path=path,
            path_type=PathType.UNKNOWN,
            is_directory=False,
            is_file=True,
            total_files=1,
        )

        file_type = self.get_file_type(path)
        file_info = self.get_file_info(path)
        analysis.file_type = file_type

        if file_type == FileType.PYTHON:
            analysis.path_type = PathType.PYTHON_FILE
            analysis.python_files = [path]
            analysis.description = (
                file_info.description if file_info else "Python source file"
            )
            analysis.recommended_targets = ["python_code", "python_field_attr"]
        elif file_type == FileType.XML:
            analysis.path_type = PathType.XML_FILE
            analysis.xml_files = [path]
            analysis.description = file_info.description if file_info else "XML file"
            analysis.recommended_targets = ["xml_code", "xml_node_attr"]

            # Check if it's an Odoo view file
            if self._is_odoo_xml(path):
                analysis.description = "Odoo XML view file"
        else:
            analysis.path_type = PathType.OTHER_FILE
            analysis.other_files = [path]
            analysis.description = (
                file_info.description
                if file_info
                else f"Other file type ({path.suffix})"
            )
            analysis.recommended_targets = []

        return analysis

    def _analyze_directory(self, path: Path) -> PathAnalysis:
        """Analyze a directory and its contents"""
        analysis = PathAnalysis(
            path=path,
            path_type=PathType.UNKNOWN,
            is_directory=True,
            is_file=False,
            python_files=[],
            xml_files=[],
            other_files=[],
        )

        # Check if it's an Odoo module
        if self._is_odoo_module(path):
            return self._analyze_odoo_module(path, analysis)

        # Check if it contains Odoo modules
        odoo_modules = self._find_odoo_modules(path)
        if odoo_modules:
            analysis.path_type = PathType.ODOO_MODULES_DIR
            analysis.is_odoo_modules_dir = True
            analysis.odoo_modules = odoo_modules
            analysis.description = (
                f"Directory containing {len(odoo_modules)} Odoo modules"
            )
            analysis.recommended_targets = ["all"]

            # Collect files from all modules
            for module in odoo_modules:
                module_analysis = self._analyze_odoo_module(
                    module,
                    PathAnalysis(
                        path=module,
                        path_type=PathType.ODOO_MODULE,
                        is_directory=True,
                        is_file=False,
                    ),
                )
                analysis.python_files.extend(module_analysis.python_files)
                analysis.xml_files.extend(module_analysis.xml_files)
                analysis.other_files.extend(module_analysis.other_files)
                analysis.total_files += module_analysis.total_files
        else:
            # Regular directory
            return self._analyze_regular_directory(path, analysis)

        return analysis

    def _analyze_odoo_module(self, path: Path, analysis: PathAnalysis) -> PathAnalysis:
        """Analyze an Odoo module directory"""
        analysis.path_type = PathType.ODOO_MODULE
        analysis.is_odoo_module = True
        analysis.description = f"Odoo module: {path.name}"
        analysis.recommended_targets = ["all", "python_code", "xml_code"]

        # Check for standard Odoo directories and files
        analysis.has_manifest = (path / "__manifest__.py").exists() or (
            path / "__openerp__.py"
        ).exists()
        analysis.has_models = (path / "models").is_dir()
        analysis.has_views = (path / "views").is_dir()
        analysis.has_security = (path / "security").is_dir()

        # Collect files by type
        for file_path in path.rglob("*"):
            if file_path.is_file():
                file_type = self.get_file_type(file_path)
                if file_type == FileType.PYTHON:
                    analysis.python_files.append(file_path)
                elif file_type == FileType.XML:
                    analysis.xml_files.append(file_path)
                else:
                    analysis.other_files.append(file_path)

        analysis.total_files = (
            len(analysis.python_files)
            + len(analysis.xml_files)
            + len(analysis.other_files)
        )

        return analysis

    def _analyze_regular_directory(
        self, path: Path, analysis: PathAnalysis
    ) -> PathAnalysis:
        """Analyze a regular (non-Odoo) directory"""
        # Collect all files
        all_files = list(path.rglob("*"))

        for file_path in all_files:
            if file_path.is_file():
                file_type = self.get_file_type(file_path)
                if file_type == FileType.PYTHON:
                    analysis.python_files.append(file_path)
                elif file_type == FileType.XML:
                    analysis.xml_files.append(file_path)
                else:
                    analysis.other_files.append(file_path)

        analysis.total_files = len(all_files)

        # Determine directory type based on content
        has_python = len(analysis.python_files) > 0
        has_xml = len(analysis.xml_files) > 0

        if has_python and has_xml:
            analysis.path_type = PathType.MIXED_PROJECT
            analysis.description = "Mixed Python and XML project"
            analysis.recommended_targets = ["all"]
        elif has_python:
            analysis.path_type = PathType.PYTHON_PROJECT
            analysis.description = "Python project"
            analysis.recommended_targets = ["python_code"]
        elif analysis.total_files == 0:
            analysis.path_type = PathType.EMPTY_DIR
            analysis.description = "Empty directory"
        else:
            analysis.path_type = PathType.UNKNOWN
            analysis.description = "Directory with miscellaneous files"

        return analysis

    def _is_odoo_module(self, path: Path) -> bool:
        """Check if a directory is an Odoo module"""
        if not path.is_dir():
            return False

        # Check for manifest file
        has_manifest = (path / "__manifest__.py").exists() or (
            path / "__openerp__.py"
        ).exists()

        # Check for standard Odoo directories
        has_models = (path / "models").is_dir()
        has_views = (path / "views").is_dir()

        return has_manifest or (has_models and has_views)

    def _is_odoo_xml(self, path: Path) -> bool:
        """Check if an XML file is an Odoo view file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read(500)  # Read first 500 chars
                return "<odoo>" in content
        except Exception:
            return False

    def _find_odoo_modules(self, path: Path) -> list[Path]:
        """Find all Odoo modules in a directory"""
        modules = []

        # Check immediate subdirectories
        for subdir in path.iterdir():
            if subdir.is_dir() and self._is_odoo_module(subdir):
                modules.append(subdir)

        return modules

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def filter_files_by_capability(
        self,
        files: list[Path],
        capability: str,
    ) -> list[Path]:
        """Filter files by capability (order, rename, etc.)"""
        result = []
        for file_path in files:
            if self.can_process(file_path, capability):
                result.append(file_path)
        return result

    def group_files_by_type(
        self,
        files: list[Path],
    ) -> dict[FileType, list[Path]]:
        """Group files by their type"""
        grouped = {}
        for file_path in files:
            file_type = self.get_file_type(file_path)
            if file_type not in grouped:
                grouped[file_type] = []
            grouped[file_type].append(file_path)
        return grouped

    def get_extensions_for_action(self, action: str) -> set[str]:
        """Get all file extensions that support a given action"""
        extensions = set()
        for info in self._registry.values():
            if action == "order" and info.can_order:
                extensions.update(info.extensions)
            elif action == "rename" and info.can_rename:
                extensions.update(info.extensions)
            elif info.type in self._handlers and action in self._handlers[info.type]:
                extensions.update(info.extensions)
        return extensions

    def find_odoo_files(
        self,
        path: Path,
        include_python: bool = True,
        include_xml: bool = True,
        include_data: bool = False,
    ) -> dict[str, list[Path]]:
        """Find Odoo-specific files in a directory"""
        result = {
            "models": [],
            "wizards": [],
            "views": [],
            "data": [],
            "security": [],
        }

        if not path.exists():
            return result

        # Find model files
        if include_python:
            models_dir = path / "models"
            if models_dir.exists():
                result["models"] = [
                    f for f in models_dir.rglob("*.py") if f.name != "__init__.py"
                ]

            wizards_dir = path / "wizards"
            if wizards_dir.exists():
                result["wizards"] = [
                    f for f in wizards_dir.rglob("*.py") if f.name != "__init__.py"
                ]

        # Find view files
        if include_xml:
            views_dir = path / "views"
            if views_dir.exists():
                result["views"] = list(views_dir.rglob("*.xml"))

            if include_data:
                data_dir = path / "data"
                if data_dir.exists():
                    result["data"] = list(data_dir.rglob("*.xml"))

                security_dir = path / "security"
                if security_dir.exists():
                    result["security"] = list(security_dir.rglob("*.xml"))

        return result

    def get_recommendation_string(self, analysis: PathAnalysis) -> str:
        """Get a human-readable recommendation string"""
        if not analysis.recommended_targets:
            return "No processing recommended"

        targets = analysis.recommended_targets
        if "all" in targets:
            return "Process all files (Python and XML)"
        elif len(targets) == 1:
            target_map = {
                "python_code": "Reorder Python code",
                "python_field_attr": "Reorder Python field attributes",
                "xml_code": "Reorder XML structure",
                "xml_node_attr": "Reorder XML attributes",
            }
            return target_map.get(targets[0], targets[0])
        else:
            return f"Multiple options: {', '.join(targets)}"

    @staticmethod
    def get_module_name_from_path(path: Path) -> str | None:
        """Extract Odoo module name from a file path"""
        parts = path.parts

        # Look for common Odoo module indicators
        for i, part in enumerate(parts):
            if part in [
                "models",
                "views",
                "wizards",
                "controllers",
                "security",
                "data",
            ]:
                if i > 0:
                    return parts[i - 1]

        # If path contains __manifest__.py or __openerp__.py
        if "__manifest__.py" in str(path) or "__openerp__.py" in str(path):
            return path.parent.name

        return None

    def is_odoo_file(self, path: Path) -> bool:
        """Check if file is Odoo-specific"""
        info = self.get_file_info(path)
        if not info:
            return False

        # Special case: Python files in Odoo modules are considered Odoo files
        if info.type == FileType.PYTHON:
            # Check if it's in an Odoo module structure
            parts = path.parts
            return "models" in parts or "wizards" in parts or "controllers" in parts

        return info.is_odoo_specific


# ============================================================
# Backup Management
# ============================================================


@dataclass
class BackupSession:
    """Information about a backup session"""

    session_id: str
    timestamp: str
    directory: Path
    files_backed_up: list[str] = field(default_factory=list)
    total_size: int = 0
    compressed: bool = False


class BackupManager:
    """Unified backup manager for file operations"""

    def __init__(
        self,
        backup_dir: str = ".backups",
        compression: bool = False,
        keep_sessions: int = 10,
    ):
        """
        Initialize backup manager

        Args:
            backup_dir: Directory to store backups
            compression: Whether to compress backups
            keep_sessions: Number of backup sessions to keep
        """
        self.backup_dir = Path(backup_dir)
        self.compression = compression
        self.keep_sessions = keep_sessions
        self.current_session: BackupSession | None = None
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def start_session(self, description: str | None = None) -> Path:
        """Start a new backup session"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{timestamp}"
        if description:
            session_id = f"{session_id}_{description}"
        session_dir = self.backup_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        self.current_session = BackupSession(
            session_id=session_id, timestamp=timestamp, directory=session_dir
        )
        logger.info(f"Started backup session: {session_id}")
        return session_dir

    def backup_file(self, file_path: Path) -> Path | None:
        """Backup a single file"""
        if not self.current_session:
            self.start_session()

        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return None

        try:
            # Create relative path structure in backup
            if file_path.is_absolute():
                # For absolute paths, create a safe relative structure
                rel_path = (
                    Path(*file_path.parts[1:])
                    if len(file_path.parts) > 1
                    else file_path.name
                )
            else:
                rel_path = file_path

            backup_path = self.current_session.directory / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(file_path, backup_path)

            # Update session info
            self.current_session.files_backed_up.append(str(file_path))
            self.current_session.total_size += file_path.stat().st_size

            logger.debug(f"Backed up: {file_path} -> {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Error backing up {file_path}: {e}")
            return None

    def restore_file(
        self, original_path: Path, backup_path: Path | None = None
    ) -> bool:
        """Restore a file from backup"""
        try:
            if backup_path and backup_path.exists():
                # Restore from specific backup path
                shutil.copy2(backup_path, original_path)
                logger.info(f"Restored {original_path} from {backup_path}")
                return True

            # Try to find in current session
            if self.current_session:
                rel_path = (
                    Path(*original_path.parts[1:])
                    if original_path.is_absolute()
                    else original_path
                )
                session_backup = self.current_session.directory / rel_path
                if session_backup.exists():
                    shutil.copy2(session_backup, original_path)
                    logger.info(f"Restored {original_path} from current session")
                    return True

            logger.warning(f"No backup found for {original_path}")
            return False

        except Exception as e:
            logger.error(f"Error restoring {original_path}: {e}")
            return False

    def finalize_session(self) -> Path | None:
        """Finalize current backup session"""
        if not self.current_session:
            logger.warning("No active backup session")
            return None

        try:
            # Save session metadata
            metadata_file = self.current_session.directory / "session_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(asdict(self.current_session), f, indent=2, default=str)

            # Compress if requested
            if self.compression:
                archive_path = self._compress_session()
                if archive_path:
                    # Remove uncompressed directory
                    shutil.rmtree(self.current_session.directory)
                    self.current_session.compressed = True
                    logger.info(f"Compressed backup session to {archive_path}")
                    result = archive_path
                else:
                    result = self.current_session.directory
            else:
                result = self.current_session.directory

            # Clean old sessions
            self._cleanup_old_sessions()

            logger.info(f"Finalized backup session: {self.current_session.session_id}")
            self.current_session = None
            return result

        except Exception as e:
            logger.error(f"Error finalizing backup session: {e}")
            return None

    def _compress_session(self) -> Path | None:
        """Compress current session directory"""
        if not self.current_session:
            return None

        try:
            archive_path = self.backup_dir / f"{self.current_session.session_id}.tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(
                    self.current_session.directory,
                    arcname=self.current_session.session_id,
                )
            return archive_path
        except Exception as e:
            logger.error(f"Error compressing session: {e}")
            return None

    def _cleanup_old_sessions(self) -> None:
        """Remove old backup sessions beyond keep_sessions limit"""
        try:
            # Get all session directories and archives
            sessions = []
            for item in self.backup_dir.iterdir():
                if item.is_dir() and item.name.startswith("session_"):
                    sessions.append(item)
                elif item.suffix in [".tar", ".gz"] and item.stem.startswith(
                    "session_"
                ):
                    sessions.append(item)

            # Sort by modification time
            sessions.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Remove old sessions
            for session in sessions[self.keep_sessions :]:
                if session.is_dir():
                    shutil.rmtree(session)
                else:
                    session.unlink()
                logger.debug(f"Removed old backup: {session}")

        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {e}")

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all backup sessions"""
        sessions = []

        for item in self.backup_dir.iterdir():
            if item.is_dir() and item.name.startswith("session_"):
                # Try to load metadata
                metadata_file = item / "session_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, "r") as f:
                        sessions.append(json.load(f))
                else:
                    # Create basic info
                    sessions.append(
                        {
                            "session_id": item.name,
                            "directory": str(item),
                            "timestamp": datetime.fromtimestamp(
                                item.stat().st_mtime
                            ).isoformat(),
                        }
                    )
            elif item.suffix in [".tar", ".gz"] and item.stem.startswith("session_"):
                sessions.append(
                    {
                        "session_id": item.stem,
                        "archive": str(item),
                        "compressed": True,
                        "timestamp": datetime.fromtimestamp(
                            item.stat().st_mtime
                        ).isoformat(),
                    }
                )

        return sorted(sessions, key=lambda x: x.get("timestamp", ""), reverse=True)

    def restore_session(self, session_id: str) -> bool:
        """Restore all files from a backup session"""
        try:
            session_path = self.backup_dir / session_id
            archive_path = self.backup_dir / f"{session_id}.tar.gz"

            # Check if compressed archive exists
            if archive_path.exists():
                # Extract archive
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(self.backup_dir)
                session_path = self.backup_dir / session_id

            if not session_path.exists():
                logger.error(f"Backup session not found: {session_id}")
                return False

            # Load metadata
            metadata_file = session_path / "session_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)

                # Restore each file
                for file_path in metadata.get("files_backed_up", []):
                    original = Path(file_path)
                    rel_path = (
                        Path(*original.parts[1:])
                        if original.is_absolute()
                        else original
                    )
                    backup = session_path / rel_path

                    if backup.exists():
                        original.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup, original)
                        logger.info(f"Restored: {original}")

            # Clean up extracted directory if it was compressed
            if archive_path.exists() and session_path.exists():
                shutil.rmtree(session_path)

            return True

        except Exception as e:
            logger.error(f"Error restoring session {session_id}: {e}")
            return False

    def get_backup_for_file(
        self, file_path: Path, session_id: str | None = None
    ) -> Path | None:
        """Get backup path for a specific file"""
        if session_id:
            session_path = self.backup_dir / session_id
        elif self.current_session:
            session_path = self.current_session.directory
        else:
            return None

        rel_path = Path(*file_path.parts[1:]) if file_path.is_absolute() else file_path
        backup_path = session_path / rel_path

        return backup_path if backup_path.exists() else None


# Global analyzer instance (singleton)
path_analyzer = PathAnalyzer()
