"""
Unified path analysis and file type registry for intelligent file handling.

This module combines path analysis with file type detection and handling,
providing a single source of truth for:
- File type detection and categorization
- Path type analysis (files, directories, Odoo modules)
- Processing recommendations and capabilities
- Handler registration and dispatch
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


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
                return "<odoo>" in content or "<openerp>" in content
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


# Global analyzer instance (singleton)
path_analyzer = PathAnalyzer()
