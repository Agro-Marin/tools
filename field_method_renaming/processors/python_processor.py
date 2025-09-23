"""
Python Processor for Field/Method Renaming
==========================================

Handles renaming of fields and methods in Python files using AST parsing
for precise and safe modifications.
"""

import ast
import logging
import re
from pathlib import Path

from utils.csv_reader import FieldChange

from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class ASTFieldMethodTransformer(ast.NodeTransformer):
    """AST transformer for renaming fields and methods"""

    def __init__(self, field_changes: dict[str, str], method_changes: dict[str, str]):
        """
        Initialize transformer.

        Args:
            field_changes: Dict mapping old field names to new names
            method_changes: Dict mapping old method names to new names
        """
        self.field_changes = field_changes
        self.method_changes = method_changes
        self.changes_applied = []

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        """Visit assignment nodes to rename field definitions"""
        # Check if this is a field assignment
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and self._is_fields_call(node.value)
        ):

            field_name = node.targets[0].id
            if field_name in self.field_changes:
                new_name = self.field_changes[field_name]
                node.targets[0].id = new_name
                self.changes_applied.append(
                    f"Field definition: {field_name} → {new_name}"
                )
                logger.debug(f"Renamed field definition: {field_name} → {new_name}")

        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Visit function definitions to rename methods"""
        if node.name in self.method_changes:
            new_name = self.method_changes[node.name]
            node.name = new_name
            self.changes_applied.append(f"Method definition: {node.name} → {new_name}")
            logger.debug(f"Renamed method definition: {node.name} → {new_name}")

        return self.generic_visit(node)

    def visit_AsyncFunctionDef(
        self, node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef:
        """Visit async function definitions to rename methods"""
        if node.name in self.method_changes:
            new_name = self.method_changes[node.name]
            node.name = new_name
            self.changes_applied.append(
                f"Async method definition: {node.name} → {new_name}"
            )
            logger.debug(f"Renamed async method definition: {node.name} → {new_name}")

        return self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        """Visit string constants to rename field/method references"""
        if isinstance(node.value, str):
            original_value = node.value
            new_value = self._replace_references_in_string(original_value)

            if new_value != original_value:
                node.value = new_value
                self.changes_applied.append(
                    f"String reference: '{original_value}' → '{new_value}'"
                )
                logger.debug(
                    f"Updated string reference: '{original_value}' → '{new_value}'"
                )

        return node

    def visit_Str(self, node: ast.Str) -> ast.Str:
        """Visit string nodes (for Python < 3.8 compatibility)"""
        original_value = node.s
        new_value = self._replace_references_in_string(original_value)

        if new_value != original_value:
            node.s = new_value
            self.changes_applied.append(
                f"String reference: '{original_value}' → '{new_value}'"
            )
            logger.debug(
                f"Updated string reference: '{original_value}' → '{new_value}'"
            )

        return node

    def _is_fields_call(self, node) -> bool:
        """Check if node is a fields.FieldType() call"""
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "fields"
        )

    def _replace_references_in_string(self, text: str) -> str:
        """Replace field/method references in string content"""
        # Replace field references
        for old_name, new_name in self.field_changes.items():
            # Exact match patterns
            patterns = [
                f"'{old_name}'",  # Single quotes
                f'"{old_name}"',  # Double quotes
                f" {old_name} ",  # Space-separated
                f",{old_name},",  # Comma-separated
                f"({old_name})",  # Parentheses
                f"[{old_name}]",  # Brackets
            ]

            for pattern in patterns:
                replacement = pattern.replace(old_name, new_name)
                text = text.replace(pattern, replacement)

        # Replace method references
        for old_name, new_name in self.method_changes.items():
            # Method call patterns
            patterns = [
                f"'{old_name}'",  # Single quotes
                f'"{old_name}"',  # Double quotes
                f".{old_name}(",  # Method call
                f" {old_name}(",  # Function call
            ]

            for pattern in patterns:
                replacement = pattern.replace(old_name, new_name)
                text = text.replace(pattern, replacement)

        return text


class PythonProcessor(BaseProcessor):
    """Processor for Python files (.py)"""

    def __init__(self, create_backups: bool = True, validate_syntax: bool = True):
        """
        Initialize Python processor.

        Args:
            create_backups: Whether to create backups before modifying files
            validate_syntax: Whether to validate Python syntax after modifications
        """
        super().__init__(create_backups, validate_syntax)

    def get_supported_extensions(self) -> list[str]:
        """Get supported file extensions"""
        return [".py"]

    def _apply_changes(
        self, file_path: Path, content: str, changes: list[FieldChange]
    ) -> tuple[str, list[str]]:
        """
        Apply field and method changes to Python file content.

        Args:
            file_path: Path to the Python file
            content: Original file content
            changes: List of changes to apply

        Returns:
            Tuple of (modified_content, list_of_applied_changes)
        """
        logger.debug(f"Applying {len(changes)} changes to Python file: {file_path}")

        # Separate field and method changes
        field_changes = {
            change.old_name: change.new_name for change in changes if change.is_field
        }
        method_changes = {
            change.old_name: change.new_name for change in changes if change.is_method
        }

        logger.debug(f"Field changes: {field_changes}")
        logger.debug(f"Method changes: {method_changes}")

        try:
            # Apply comprehensive regex-based transformations preserving original formatting
            modified_content, changes_applied = (
                self._apply_comprehensive_regex_transformations(
                    content, field_changes, method_changes
                )
            )

            return modified_content, changes_applied

        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing Python file {file_path}: {e}")
            raise

    def _apply_comprehensive_regex_transformations(
        self,
        content: str,
        field_changes: dict[str, str],
        method_changes: dict[str, str],
    ) -> tuple[str, list[str]]:
        """
        Apply comprehensive regex-based transformations preserving original formatting.

        This method handles all transformation patterns:
        - Field and method definitions
        - Attribute access and assignments (self.field, obj.field)
        - Augmented assignments (obj.field += value)
        - Dictionary access (["field"], ['field'])
        - String references and compound strings
        - Odoo-specific patterns (@api.depends, compute=, etc.)

        Args:
            content: Python content to transform
            field_changes: Dict of field name changes
            method_changes: Dict of method name changes

        Returns:
            Tuple of (modified_content, list_of_applied_changes)
        """
        modified_content = content
        applied_changes = []

        # 1. Field definitions: field_name = fields.Type(...)
        for old_name, new_name in field_changes.items():
            pattern = rf"\b{re.escape(old_name)}\s*=\s*fields\."
            if re.search(pattern, modified_content):
                modified_content = re.sub(
                    rf"\b{re.escape(old_name)}\b(?=\s*=\s*fields\.)",
                    new_name,
                    modified_content,
                )
                applied_changes.append(f"Field definition: {old_name} → {new_name}")

        # 2. Method definitions: def method_name(self, ...):
        for old_name, new_name in method_changes.items():
            pattern = rf"\bdef\s+{re.escape(old_name)}\s*\("
            if re.search(pattern, modified_content):
                modified_content = re.sub(
                    rf"\bdef\s+{re.escape(old_name)}\b(?=\s*\()",
                    f"def {new_name}",
                    modified_content,
                )
                applied_changes.append(f"Method definition: {old_name} → {new_name}")

        # 3. Attribute access and assignments: self.field, record.field = value, obj.field += 1
        for old_name, new_name in field_changes.items():
            # Pattern for attribute access/assignment (handles =, +=, -=, *=, etc.)
            pattern = rf"\.{re.escape(old_name)}\b"
            if re.search(pattern, modified_content):
                modified_content = re.sub(
                    rf"\.{re.escape(old_name)}\b",
                    f".{new_name}",
                    modified_content,
                )
                applied_changes.append(
                    f"Attribute access/assignment: *.{old_name} → *.{new_name}"
                )

        # 4. Method calls: self.method(...) or obj.method(...)
        for old_name, new_name in method_changes.items():
            pattern = rf"\.{re.escape(old_name)}\s*\("
            if re.search(pattern, modified_content):
                modified_content = re.sub(
                    rf"\.{re.escape(old_name)}\b(?=\s*\()",
                    f".{new_name}",
                    modified_content,
                )
                applied_changes.append(f"Method call: *.{old_name}() → *.{new_name}()")

        # 5. Dictionary access: vals['field'], data["field"]
        for old_name, new_name in field_changes.items():
            # Single quotes in dictionary keys
            pattern = rf"\['{re.escape(old_name)}'\]"
            if re.search(pattern, modified_content):
                modified_content = re.sub(pattern, f"['{new_name}']", modified_content)
                applied_changes.append(
                    f"Dictionary access: ['{old_name}'] → ['{new_name}']"
                )

            # Double quotes in dictionary keys
            pattern = rf'\["{re.escape(old_name)}"\]'
            if re.search(pattern, modified_content):
                modified_content = re.sub(pattern, f'["{new_name}"]', modified_content)
                applied_changes.append(
                    f'Dictionary access: ["{old_name}"] → ["{new_name}"]'
                )

        # 6. String references (exact matches)
        for old_name, new_name in field_changes.items():
            # Single quotes - exact match
            pattern = rf"'{re.escape(old_name)}'"
            if re.search(pattern, modified_content):
                modified_content = re.sub(pattern, f"'{new_name}'", modified_content)
                applied_changes.append(f"String reference: '{old_name}' → '{new_name}'")

            # Double quotes - exact match
            pattern = rf'"{re.escape(old_name)}"'
            if re.search(pattern, modified_content):
                modified_content = re.sub(pattern, f'"{new_name}"', modified_content)
                applied_changes.append(f'String reference: "{old_name}" → "{new_name}"')

        # 7. Compound strings: 'default_field_name', 'compute_field_name', etc.
        # This handles compound strings that weren't already covered by exact matches
        for old_name, new_name in field_changes.items():
            # Only apply compound string replacement if it wasn't already covered
            # Single quotes compound strings (avoid already processed exact matches)
            pattern = rf"'([^']+){re.escape(old_name)}([^']+)'"
            matches = re.findall(pattern, modified_content)
            if matches:
                replacement = rf"'\g<1>{new_name}\g<2>'"
                modified_content = re.sub(pattern, replacement, modified_content)
                for match in matches:
                    old_full = f"{match[0]}{old_name}{match[1]}"
                    new_full = f"{match[0]}{new_name}{match[1]}"
                    applied_changes.append(
                        f"Compound string: '{old_full}' → '{new_full}'"
                    )

            # Double quotes compound strings (avoid already processed exact matches)
            pattern = rf'"([^"]+){re.escape(old_name)}([^"]+)"'
            matches = re.findall(pattern, modified_content)
            if matches:
                replacement = rf'"\g<1>{new_name}\g<2>"'
                modified_content = re.sub(pattern, replacement, modified_content)
                for match in matches:
                    old_full = f"{match[0]}{old_name}{match[1]}"
                    new_full = f"{match[0]}{new_name}{match[1]}"
                    applied_changes.append(
                        f'Compound string: "{old_full}" → "{new_full}"'
                    )

        # 8. Odoo-specific patterns
        # @api.depends decorators
        for old_name, new_name in field_changes.items():
            pattern = (
                rf"@api\.depends\(([^)]*)(['\"]){re.escape(old_name)}(['\"])([^)]*)\)"
            )
            if re.search(pattern, modified_content):
                replacement = rf"@api.depends(\g<1>\g<2>{new_name}\g<3>\g<4>)"
                modified_content = re.sub(pattern, replacement, modified_content)
                applied_changes.append(
                    f"@api.depends decorator: {old_name} → {new_name}"
                )

        # compute, inverse, search method references
        for old_name, new_name in field_changes.items():
            patterns = [
                (
                    rf"compute\s*=\s*(['\"])_compute_{re.escape(old_name)}\1",
                    rf"compute=\g<1>_compute_{new_name}\g<1>",
                ),
                (
                    rf"inverse\s*=\s*(['\"])_inverse_{re.escape(old_name)}\1",
                    rf"inverse=\g<1>_inverse_{new_name}\g<1>",
                ),
                (
                    rf"search\s*=\s*(['\"])_search_{re.escape(old_name)}\1",
                    rf"search=\g<1>_search_{new_name}\g<1>",
                ),
            ]

            for pattern, replacement in patterns:
                if re.search(pattern, modified_content):
                    modified_content = re.sub(pattern, replacement, modified_content)
                    method_type = pattern.split("\\")[0]  # compute, inverse, or search
                    applied_changes.append(
                        f"{method_type} method reference: _{method_type}_{old_name} → _{method_type}_{new_name}"
                    )

        # Domain references: [('field_name', '=', value)]
        for old_name, new_name in field_changes.items():
            pattern = rf"\(\s*(['\"]){re.escape(old_name)}\1\s*,"
            if re.search(pattern, modified_content):
                replacement = rf"(\g<1>{new_name}\g<1>,"
                modified_content = re.sub(pattern, replacement, modified_content)
                applied_changes.append(f"Domain reference: {old_name} → {new_name}")

        # Method string references
        for old_name, new_name in method_changes.items():
            # Single quotes
            pattern = rf"'{re.escape(old_name)}'"
            if re.search(pattern, modified_content):
                modified_content = re.sub(pattern, f"'{new_name}'", modified_content)
                applied_changes.append(
                    f"Method string reference: '{old_name}' → '{new_name}'"
                )

            # Double quotes
            pattern = rf'"{re.escape(old_name)}"'
            if re.search(pattern, modified_content):
                modified_content = re.sub(pattern, f'"{new_name}"', modified_content)
                applied_changes.append(
                    f'Method string reference: "{old_name}" → "{new_name}"'
                )

        return modified_content, applied_changes

    def _filter_relevant_changes(
        self, file_path: Path, changes: list[FieldChange]
    ) -> list[FieldChange]:
        """
        Filter changes relevant to this Python file.

        Args:
            file_path: Path to the Python file
            changes: All changes to consider

        Returns:
            List of relevant changes
        """
        # For Python files, we need to read the content to determine which models are defined
        try:
            content = self._read_file_content(file_path)
            models_in_file = self._extract_models_from_python_file(content)

            # Filter changes for models that are defined or inherited in this file
            relevant_changes = []
            for change in changes:
                model_key = f"{change.module}.{change.model}"
                if model_key in models_in_file or change.model in models_in_file:
                    relevant_changes.append(change)
                    logger.debug(f"Relevant change for {file_path}: {change}")

            return relevant_changes

        except Exception as e:
            logger.warning(f"Could not filter changes for {file_path}: {e}")
            # If we can't determine, return all changes and let AST handle it
            return changes

    def _extract_models_from_python_file(self, content: str) -> set[str]:
        """
        Extract model names defined or inherited in a Python file.

        Args:
            content: Python file content

        Returns:
            Set of model names found in the file
        """
        models = set()

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Look for _name and _inherit attributes
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            targets = [
                                t.id for t in item.targets if isinstance(t, ast.Name)
                            ]

                            if "_name" in targets and isinstance(
                                item.value, ast.Constant
                            ):
                                models.add(item.value.value)
                            elif "_inherit" in targets:
                                if isinstance(item.value, ast.Constant):
                                    models.add(item.value.value)
                                elif isinstance(item.value, ast.List):
                                    for elt in item.value.elts:
                                        if isinstance(elt, ast.Constant):
                                            models.add(elt.value)

        except Exception as e:
            logger.debug(f"Error extracting models from Python content: {e}")

        return models

    def _validate_python_transformations(
        self, original_content: str, modified_content: str, changes: list[FieldChange]
    ) -> bool:
        """
        Validate that Python transformations were applied correctly.

        Args:
            original_content: Original file content
            modified_content: Modified file content
            changes: Changes that were supposed to be applied

        Returns:
            True if transformations appear correct
        """
        # Check that we haven't accidentally broken imports or basic structure
        try:
            original_tree = ast.parse(original_content)
            modified_tree = ast.parse(modified_content)

            # Count nodes to ensure structure is preserved
            original_nodes = len(list(ast.walk(original_tree)))
            modified_nodes = len(list(ast.walk(modified_tree)))

            # Allow for small differences due to AST normalization
            if abs(original_nodes - modified_nodes) > len(changes):
                logger.warning("Significant structural changes detected in AST")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating Python transformations: {e}")
            return False

    def get_file_analysis(self, file_path: Path) -> dict[str, any]:
        """
        Analyze a Python file to extract information about fields and methods.

        Args:
            file_path: Path to the Python file

        Returns:
            Dictionary with analysis results
        """
        try:
            content = self._read_file_content(file_path)
            tree = ast.parse(content)

            fields = []
            methods = []
            models = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Extract model information
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            targets = [
                                t.id for t in item.targets if isinstance(t, ast.Name)
                            ]

                            # Model names
                            if "_name" in targets and isinstance(
                                item.value, ast.Constant
                            ):
                                models.append(item.value.value)

                            # Field definitions
                            if (
                                len(item.targets) == 1
                                and isinstance(item.targets[0], ast.Name)
                                and self._is_fields_call_analysis(item.value)
                            ):
                                fields.append(item.targets[0].id)

                        # Method definitions
                        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            methods.append(item.name)

            return {
                "models": models,
                "fields": fields,
                "methods": methods,
                "total_lines": len(content.splitlines()),
                "file_size": len(content),
            }

        except Exception as e:
            logger.error(f"Error analyzing Python file {file_path}: {e}")
            return {"models": [], "fields": [], "methods": [], "error": str(e)}

    def _is_fields_call_analysis(self, node) -> bool:
        """Check if node is a fields.FieldType() call for analysis"""
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "fields"
        )
