"""
Path analysis utilities for intelligent detection of directory/file types.

This module provides smart detection of:
- Odoo modules vs regular Python projects
- File type composition in directories
- Optimal processing strategies based on content
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class PathType(Enum):
    """Enumeration of path types that can be detected."""

    PYTHON_FILE = "python_file"
    XML_FILE = "xml_file"
    OTHER_FILE = "other_file"
    ODOO_MODULE = "odoo_module"
    ODOO_MODULES_DIR = "odoo_modules_directory"  # Contains multiple Odoo modules
    PYTHON_PROJECT = "python_project"  # Regular Python project
    MIXED_PROJECT = "mixed_project"  # Contains Python and XML but not Odoo
    EMPTY_DIR = "empty_directory"
    UNKNOWN = "unknown"


@dataclass
class PathAnalysis:
    """Result of path analysis with detailed information."""

    path: Path
    path_type: PathType
    is_directory: bool
    is_file: bool

    # File statistics
    python_files: list[Path] = None
    xml_files: list[Path] = None
    other_files: list[Path] = None
    total_files: int = 0

    # Odoo-specific
    is_odoo_module: bool = False
    is_odoo_modules_dir: bool = False
    odoo_modules: list[Path] = None  # List of detected Odoo modules
    has_manifest: bool = False
    has_init: bool = False
    has_models: bool = False
    has_views: bool = False
    has_security: bool = False

    # Recommendations
    recommended_targets: list[str] = None  # Suggested processing targets
    description: str = ""

    def __post_init__(self):
        """Initialize lists if not provided."""
        if self.python_files is None:
            self.python_files = []
        if self.xml_files is None:
            self.xml_files = []
        if self.other_files is None:
            self.other_files = []
        if self.odoo_modules is None:
            self.odoo_modules = []
        if self.recommended_targets is None:
            self.recommended_targets = []


class PathAnalyzer:
    """Analyzes paths to determine their type and characteristics."""

    # Odoo module indicators
    MANIFEST_FILES = {"__manifest__.py", "__openerp__.py"}
    ODOO_DIRS = {
        "models",
        "views",
        "controllers",
        "wizards",
        "security",
        "data",
        "static",
        "reports",
    }
    ODOO_FILE_PATTERNS = {
        "models": ["*.py"],
        "views": ["*.xml"],
        "data": ["*.xml", "*.csv"],
        "security": ["ir.model.access.csv", "*.xml"],
    }

    def __init__(self):
        """Initialize the path analyzer."""
        pass

    def analyze(self, path: Path | str) -> PathAnalysis:
        """
        Analyze a path and return detailed information about it.

        Args:
            path: Path to analyze (file or directory)

        Returns:
            PathAnalysis object with detailed information
        """
        path = Path(path) if isinstance(path, str) else path

        if not path.exists():
            return PathAnalysis(
                path=path,
                path_type=PathType.UNKNOWN,
                is_directory=False,
                is_file=False,
                description=f"Path does not exist: {path}",
            )

        if path.is_file():
            return self._analyze_file(path)
        elif path.is_dir():
            return self._analyze_directory(path)
        else:
            return PathAnalysis(
                path=path,
                path_type=PathType.UNKNOWN,
                is_directory=False,
                is_file=False,
                description=f"Path is neither file nor directory: {path}",
            )

    def _analyze_file(self, path: Path) -> PathAnalysis:
        """Analyze a single file."""
        analysis = PathAnalysis(
            path=path,
            path_type=PathType.UNKNOWN,
            is_directory=False,
            is_file=True,
            total_files=1,
        )

        if path.suffix == ".py":
            analysis.path_type = PathType.PYTHON_FILE
            analysis.python_files = [path]
            analysis.description = "Python source file"
            analysis.recommended_targets = ["python_code", "python_field_attr"]
        elif path.suffix == ".xml":
            analysis.path_type = PathType.XML_FILE
            analysis.xml_files = [path]
            analysis.description = "XML file"
            analysis.recommended_targets = ["xml_code", "xml_node_attr"]

            # Check if it's an Odoo view file
            if self._is_odoo_xml(path):
                analysis.description = "Odoo XML view file"
        else:
            analysis.path_type = PathType.OTHER_FILE
            analysis.other_files = [path]
            analysis.description = f"Other file type ({path.suffix})"
            analysis.recommended_targets = []

        return analysis

    def _analyze_directory(self, path: Path) -> PathAnalysis:
        """Analyze a directory and its contents."""
        analysis = PathAnalysis(
            path=path,
            path_type=PathType.UNKNOWN,
            is_directory=True,
            is_file=False,
        )

        # First, check if this is an Odoo module
        if self._is_odoo_module(path):
            analysis = self._analyze_odoo_module(path, analysis)
        # Check if this directory contains Odoo modules
        elif self._contains_odoo_modules(path):
            analysis = self._analyze_odoo_modules_dir(path, analysis)
        else:
            # Regular directory analysis
            analysis = self._analyze_regular_directory(path, analysis)

        return analysis

    def _is_odoo_module(self, path: Path) -> bool:
        """Check if a directory is an Odoo module."""
        # Check for manifest file
        for manifest in self.MANIFEST_FILES:
            if (path / manifest).exists():
                return True
        return False

    def _contains_odoo_modules(self, path: Path) -> bool:
        """Check if a directory contains Odoo modules."""
        # Look for subdirectories that are Odoo modules
        for subdir in path.iterdir():
            if subdir.is_dir() and self._is_odoo_module(subdir):
                return True
        return False

    def _is_odoo_xml(self, path: Path) -> bool:
        """Check if an XML file is an Odoo-specific XML."""
        try:
            content = path.read_text(encoding="utf-8")
            # Look for Odoo-specific XML patterns
            odoo_indicators = [
                "<odoo>",
                "<openerp>",
                "<record ",
                "<menuitem ",
                "<template ",
                "ir.ui.view",
                "ir.model.access",
            ]
            return any(indicator in content for indicator in odoo_indicators)
        except Exception:
            return False

    def _analyze_odoo_module(self, path: Path, analysis: PathAnalysis) -> PathAnalysis:
        """Analyze an Odoo module directory."""
        analysis.path_type = PathType.ODOO_MODULE
        analysis.is_odoo_module = True
        analysis.odoo_modules = [path]

        # Check for manifest
        for manifest in self.MANIFEST_FILES:
            if (path / manifest).exists():
                analysis.has_manifest = True
                break

        # Check for __init__.py
        if (path / "__init__.py").exists():
            analysis.has_init = True

        # Check for standard Odoo directories
        if (path / "models").exists():
            analysis.has_models = True
        if (path / "views").exists():
            analysis.has_views = True
        if (path / "security").exists():
            analysis.has_security = True

        # Collect all Python and XML files
        analysis.python_files = list(path.rglob("*.py"))
        analysis.xml_files = list(path.rglob("*.xml"))
        analysis.total_files = len(analysis.python_files) + len(analysis.xml_files)

        # Set description
        components = []
        if analysis.has_models:
            components.append("models")
        if analysis.has_views:
            components.append("views")
        if analysis.has_security:
            components.append("security")

        analysis.description = (
            f"Odoo module with {', '.join(components)}" if components else "Odoo module"
        )
        analysis.description += (
            f" ({len(analysis.python_files)} .py, {len(analysis.xml_files)} .xml files)"
        )

        # Recommendations
        analysis.recommended_targets = ["all"]  # Process everything in Odoo modules
        if analysis.python_files:
            analysis.recommended_targets.extend(["python_code", "python_field_attr"])
        if analysis.xml_files:
            analysis.recommended_targets.extend(["xml_code", "xml_node_attr"])

        return analysis

    def _analyze_odoo_modules_dir(
        self, path: Path, analysis: PathAnalysis
    ) -> PathAnalysis:
        """Analyze a directory containing multiple Odoo modules."""
        analysis.path_type = PathType.ODOO_MODULES_DIR
        analysis.is_odoo_modules_dir = True

        # Find all Odoo modules
        for subdir in path.iterdir():
            if subdir.is_dir() and self._is_odoo_module(subdir):
                analysis.odoo_modules.append(subdir)

        # Collect files from all modules
        for module_path in analysis.odoo_modules:
            analysis.python_files.extend(list(module_path.rglob("*.py")))
            analysis.xml_files.extend(list(module_path.rglob("*.xml")))

        analysis.total_files = len(analysis.python_files) + len(analysis.xml_files)

        analysis.description = (
            f"Directory containing {len(analysis.odoo_modules)} Odoo modules "
            f"({len(analysis.python_files)} .py, {len(analysis.xml_files)} .xml files)"
        )

        # Recommendations
        analysis.recommended_targets = ["all"]

        return analysis

    def _analyze_regular_directory(
        self, path: Path, analysis: PathAnalysis
    ) -> PathAnalysis:
        """Analyze a regular (non-Odoo) directory."""
        # Collect all files
        all_files = list(path.rglob("*"))

        for file_path in all_files:
            if file_path.is_file():
                if file_path.suffix == ".py":
                    analysis.python_files.append(file_path)
                elif file_path.suffix == ".xml":
                    analysis.xml_files.append(file_path)
                else:
                    analysis.other_files.append(file_path)

        analysis.total_files = len(all_files)

        # Determine directory type based on content
        has_python = len(analysis.python_files) > 0
        has_xml = len(analysis.xml_files) > 0

        if has_python and not has_xml:
            analysis.path_type = PathType.PYTHON_PROJECT
            analysis.description = (
                f"Python project ({len(analysis.python_files)} .py files)"
            )
            analysis.recommended_targets = ["python_code"]
        elif has_xml and not has_python:
            analysis.path_type = PathType.MIXED_PROJECT
            analysis.description = f"XML project ({len(analysis.xml_files)} .xml files)"
            analysis.recommended_targets = ["xml_code", "xml_node_attr"]
        elif has_python and has_xml:
            analysis.path_type = PathType.MIXED_PROJECT
            analysis.description = (
                f"Mixed project ({len(analysis.python_files)} .py, "
                f"{len(analysis.xml_files)} .xml files)"
            )
            analysis.recommended_targets = ["python_code", "xml_code"]
        elif analysis.total_files == 0:
            analysis.path_type = PathType.EMPTY_DIR
            analysis.description = "Empty directory"
            analysis.recommended_targets = []
        else:
            analysis.path_type = PathType.UNKNOWN
            analysis.description = (
                f"Directory with {len(analysis.other_files)} non-Python/XML files"
            )
            analysis.recommended_targets = []

        return analysis

    def get_recommendation_string(self, analysis: PathAnalysis) -> str:
        """
        Get a human-readable recommendation string based on analysis.

        Args:
            analysis: PathAnalysis object

        Returns:
            String with processing recommendations
        """
        if not analysis.recommended_targets:
            return "No recommended processing for this path type."

        recommendations = []

        if "all" in analysis.recommended_targets:
            recommendations.append("• Process all (Python and XML): --target all")
        else:
            if "python_code" in analysis.recommended_targets:
                recommendations.append("• Reorder Python code: --target python_code")
            if "python_field_attr" in analysis.recommended_targets:
                recommendations.append(
                    "• Reorder field attributes: --target python_field_attr"
                )
            if "xml_code" in analysis.recommended_targets:
                recommendations.append("• Reorder XML structure: --target xml_code")
            if "xml_node_attr" in analysis.recommended_targets:
                recommendations.append(
                    "• Reorder XML attributes: --target xml_node_attr"
                )

        return "\n".join(recommendations)

    @staticmethod
    def get_module_name_from_path(file_path: Path) -> str | None:
        """
        Extract Odoo module name from file path.

        Args:
            file_path: Path to file in Odoo module

        Returns:
            Module name or None
        """
        # Look for __manifest__.py or __openerp__.py in parent directories
        current = file_path.parent if file_path.is_file() else file_path
        while current.parent != current:
            if (current / "__manifest__.py").exists() or (
                current / "__openerp__.py"
            ).exists():
                return current.name
            current = current.parent

        # Fallback: use first directory name if it looks like a module
        parts = file_path.parts
        if parts:
            potential_module = parts[0]
            # Simple heuristic: module names are usually lowercase with underscores
            if "_" in potential_module or potential_module.islower():
                return potential_module

        return None

    def find_odoo_files(
        self,
        module_path: Path,
        include_python: bool = True,
        include_xml: bool = True,
        include_data: bool = False,
    ) -> dict[str, list[Path]]:
        """
        Find Odoo files organized by type.

        Args:
            module_path: Path to Odoo module
            include_python: Include Python files
            include_xml: Include XML view files
            include_data: Include data files (yaml, csv)

        Returns:
            Dictionary with file types as keys and list of paths as values
        """
        files = {
            "models": [],
            "wizards": [],
            "controllers": [],
            "views": [],
            "data": [],
            "security": [],
        }

        if not module_path.is_dir():
            return files

        # Python files
        if include_python:
            for dir_name in ["models", "wizard", "wizards"]:
                dir_path = module_path / dir_name
                if dir_path.exists():
                    files["models" if dir_name == "models" else "wizards"].extend(
                        dir_path.glob("*.py")
                    )

            controllers_dir = module_path / "controllers"
            if controllers_dir.exists():
                files["controllers"].extend(controllers_dir.glob("*.py"))

        # XML files
        if include_xml:
            views_dir = module_path / "views"
            if views_dir.exists():
                files["views"].extend(views_dir.glob("*.xml"))

            data_dir = module_path / "data"
            if data_dir.exists():
                files["data"].extend(data_dir.glob("*.xml"))

            security_dir = module_path / "security"
            if security_dir.exists():
                files["security"].extend(security_dir.glob("*.xml"))

        # Data files
        if include_data:
            for dir_path in [module_path / "data", module_path / "demo"]:
                if dir_path.exists():
                    files["data"].extend(dir_path.glob("*.csv"))
                    files["data"].extend(dir_path.glob("*.yml"))
                    files["data"].extend(dir_path.glob("*.yaml"))

        return files
