"""
Model Registry for Odoo Inheritance Analysis
===========================================

This module provides a registry system to discover and catalog all Odoo model
definitions across multiple files and modules, serving as the foundation for
inheritance-aware analysis.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FieldDefinition:
    """Represents a field definition in an Odoo model"""

    name: str
    field_type: str
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, str] = field(default_factory=dict)
    signature: str = ""
    definition: str = ""
    line_number: int = 0
    source_file: str = ""


@dataclass
class MethodDefinition:
    """Represents a method definition in an Odoo model"""

    name: str
    args: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    signature: str = ""
    definition: str = ""
    line_number: int = 0
    source_file: str = ""


@dataclass
class MethodCall:
    """Represents a method call within a model"""

    method_name: str
    calling_method: str
    call_type: str  # 'self', 'super', 'record'
    line_number: int = 0
    source_file: str = ""


@dataclass
class FieldReference:
    """Represents a field reference within a model"""

    field_name: str
    referencing_method: str
    context_type: str  # 'self', 'record', 'assignment'
    line_number: int = 0
    source_file: str = ""


@dataclass
class ModelDefinition:
    """Complete definition of an Odoo model from a single file"""

    class_name: str
    model_name: Optional[str]  # _name attribute
    inherit_models: List[str] = field(default_factory=list)  # _inherit attribute
    inherits_models: Dict[str, str] = field(default_factory=dict)  # _inherits attribute
    fields: List[FieldDefinition] = field(default_factory=list)
    methods: List[MethodDefinition] = field(default_factory=list)
    method_calls: List[MethodCall] = field(default_factory=list)
    field_references: List[FieldReference] = field(default_factory=list)
    source_file: str = ""
    line_number: int = 0

    def is_base_model(self) -> bool:
        """Check if this is a base model definition (has _name)"""
        return self.model_name is not None

    def is_inheritance(self) -> bool:
        """Check if this is an inheritance definition (has _inherit)"""
        return len(self.inherit_models) > 0

    def get_target_model(self) -> Optional[str]:
        """Get the target model name (either _name or first _inherit)"""
        if self.model_name:
            return self.model_name
        elif self.inherit_models:
            return self.inherit_models[0]
        return None


class ModelRegistry:
    """Registry to discover and catalog all Odoo model definitions"""

    def __init__(self):
        self.models: Dict[str, List[ModelDefinition]] = {}
        self.file_models: Dict[str, List[ModelDefinition]] = {}
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
                    target_model = model.get_target_model()
                    if target_model:
                        if target_model not in self.models:
                            self.models[target_model] = []
                        self.models[target_model].append(model)

        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")

    def _extract_models_from_content(
        self, content: str, file_path: str
    ) -> List[ModelDefinition]:
        """Extract model definitions from Python file content"""
        try:
            # Use the existing extract_definitions function for consistency
            from ..analyzers.ast_parser import extract_definitions

            inventory = extract_definitions(content, file_path)
            return self._convert_inventory_to_models(inventory, file_path)

        except Exception as e:
            logger.error(f"Error extracting models from {file_path}: {e}")
            return []

    def _convert_inventory_to_models(
        self, inventory: dict, file_path: str
    ) -> List[ModelDefinition]:
        """Convert AST parser inventory to ModelDefinition objects"""
        models = []

        # Group by model name from classes
        models_by_name = {}

        for class_info in inventory.get("classes", []):
            model_name = class_info.get("model_name")
            inheritance = class_info.get("inheritance", [])

            # Determine target model name
            target_model = model_name
            inherit_models = []

            if not model_name:
                # This is an inheritance class, extract _inherit info
                for inherit_item in inheritance:
                    if not inherit_item.startswith("models."):
                        inherit_models.append(inherit_item)

                if inherit_models:
                    target_model = inherit_models[0]  # Use first inherit as target

            if target_model:
                if target_model not in models_by_name:
                    models_by_name[target_model] = ModelDefinition(
                        class_name=class_info["name"],
                        model_name=model_name,
                        inherit_models=inherit_models,
                        source_file=file_path,
                        line_number=class_info.get("line", 0),
                    )

        # Add fields and methods to corresponding models
        for field_info in inventory.get("fields", []):
            model_name = field_info.get("model")
            if model_name in models_by_name:
                field_def = FieldDefinition(
                    name=field_info["name"],
                    field_type=field_info.get("field_type", ""),
                    args=field_info.get("args", []),
                    kwargs=field_info.get("kwargs", {}),
                    signature=field_info.get("signature", ""),
                    definition=field_info.get("definition", ""),
                    line_number=field_info.get("line", 0),
                    source_file=file_path,
                )
                models_by_name[model_name].fields.append(field_def)

        for method_info in inventory.get("methods", []):
            model_name = method_info.get("model")
            if model_name in models_by_name:
                method_def = MethodDefinition(
                    name=method_info["name"],
                    args=method_info.get("args", []),
                    decorators=method_info.get("decorators", []),
                    signature=method_info.get("signature", ""),
                    definition=method_info.get("definition", ""),
                    line_number=method_info.get("line", 0),
                    source_file=file_path,
                )
                models_by_name[model_name].methods.append(method_def)

        return list(models_by_name.values())

    def get_models_for_name(self, model_name: str) -> List[ModelDefinition]:
        """Get all model definitions for a given model name"""
        return self.models.get(model_name, [])

    def get_all_model_names(self) -> Set[str]:
        """Get all known model names in the registry"""
        return set(self.models.keys())

    def get_models_in_file(self, file_path: str) -> List[ModelDefinition]:
        """Get all models defined in a specific file"""
        return self.file_models.get(file_path, [])

    def clear(self) -> None:
        """Clear the registry"""
        self.models.clear()
        self.file_models.clear()
        self._scanned_paths.clear()
