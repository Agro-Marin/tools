"""
Odoo module utilities for common operations
Centralizes knowledge about Odoo module structure and conventions
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class OdooModuleUtils:
    """Utility class for Odoo module operations"""

    # Common Odoo directories
    PYTHON_DIRS = {"models", "wizard", "wizards", "report", "reports", "controllers"}
    VIEW_DIRS = {"views", "data", "security"}

    @classmethod
    def find_odoo_files(
        cls,
        module_path: Path,
        include_python: bool = True,
        include_xml: bool = True,
        include_data: bool = False,
    ) -> dict[str, list[Path]]:
        """
        Find Odoo files organized by type

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

    @classmethod
    def is_odoo_module(cls, path: Path) -> bool:
        """
        Check if path is an Odoo module

        Args:
            path: Path to check

        Returns:
            True if path appears to be an Odoo module
        """
        if not path.is_dir():
            return False

        # Check for __manifest__.py or __openerp__.py
        return (path / "__manifest__.py").exists() or (path / "__openerp__.py").exists()

    @classmethod
    def get_module_name_from_path(cls, file_path: Path) -> str | None:
        """
        Extract module name from file path

        Args:
            file_path: Path to file in Odoo module

        Returns:
            Module name or None
        """
        # Look for __manifest__.py or __openerp__.py in parent directories
        current = file_path.parent if file_path.is_file() else file_path
        while current.parent != current:
            if cls.is_odoo_module(current):
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
