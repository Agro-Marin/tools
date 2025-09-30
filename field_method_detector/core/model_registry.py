"""
Model Registry for Odoo Inheritance Analysis
===========================================

This module provides a registry system to discover and catalog all Odoo model
definitions across multiple files and modules, serving as the foundation for
inheritance-aware analysis.
"""

import logging
from typing import Dict, List, Optional, Set
from pathlib import Path
from core.models import Model, Field, Method, Reference, InheritanceType, CallType

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry to discover and catalog all Odoo model definitions"""

    def __init__(self):
        self.models: Dict[str, List[Model]] = {}
        self.file_models: Dict[str, List[Model]] = {}
        self._scanned_paths: Set[str] = set()

    def scan_modules(self, module_paths: List[str]) -> None:
        """
        Scan multiple module paths and extract all model definitions

        Args:
            module_paths: List of paths to Odoo modules to scan
        """
        logger.info(f"Scanning {len(module_paths)} module paths for Odoo models")

        for module_path in module_paths:
            if module_path in self._scanned_paths:
                logger.debug(f"Skipping already scanned path: {module_path}")
                continue

            self._scan_single_module(module_path)
            self._scanned_paths.add(module_path)

        logger.info(
            f"Registry contains {len(self.models)} unique models from {len(self.file_models)} files"
        )

    def _scan_single_module(self, module_path: str) -> None:
        """Scan a single module directory for Python files"""
        module_path_obj = Path(module_path)

        if not module_path_obj.exists():
            logger.warning(f"Module path does not exist: {module_path}")
            return

        if not module_path_obj.is_dir():
            logger.warning(f"Module path is not a directory: {module_path}")
            return

        python_files = list(module_path_obj.rglob("*.py"))
        logger.debug(f"Found {len(python_files)} Python files in {module_path}")

        for py_file in python_files:
            try:
                self._process_python_file(str(py_file))
            except Exception as e:
                logger.error(f"Error processing file {py_file}: {e}")

    def _process_python_file(self, file_path: str) -> None:
        """Process a single Python file and extract model definitions"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            models = self._extract_models_from_content(content, file_path)

            if models:
                logger.debug(f"Extracted {len(models)} models from {file_path}")
                self.file_models[file_path] = models

                # Add to registry by model name
                for model in models:
                    model_name = model.name
                    if model_name:
                        if model_name not in self.models:
                            self.models[model_name] = []
                        self.models[model_name].append(model)

        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")

    def _extract_models_from_content(self, content: str, file_path: str) -> List[Model]:
        """Extract model definitions from Python file content"""
        try:
            # Use the modern extract_models function
            from analyzers.ast_visitor import extract_models

            models = extract_models(content, file_path)
            return models

        except Exception as e:
            logger.error(f"Error extracting models from {file_path}: {e}")
            return []

    def get_models_for_name(self, model_name: str) -> List[Model]:
        """Get all model definitions for a given model name"""
        return self.models.get(model_name, [])

    def get_all_model_names(self) -> Set[str]:
        """Get all known model names in the registry"""
        return set(self.models.keys())

    def get_models_in_file(self, file_path: str) -> List[Model]:
        """Get all models defined in a specific file"""
        return self.file_models.get(file_path, [])

    def clear(self) -> None:
        """Clear the registry"""
        self.models.clear()
        self.file_models.clear()
        self._scanned_paths.clear()
