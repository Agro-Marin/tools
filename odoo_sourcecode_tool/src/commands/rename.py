"""
Command module for applying field/method renames
"""

import ast
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from core.backup_manager import BackupManager
from core.base_processor import ProcessingStatus, ProcessResult
from core.config import Config
from core.odoo_module_utils import OdooModuleUtils

logger = logging.getLogger(__name__)


@dataclass
class FieldChange:
    """Data class for field/method changes from CSV"""

    old_name: str
    new_name: str
    item_type: str  # 'field' or 'method'
    module: str
    model: str
    confidence: float = 1.0

    @property
    def is_field(self) -> bool:
        return self.item_type == "field"

    @property
    def is_method(self) -> bool:
        return self.item_type == "method"


class RenameCommand:
    """Command handler for applying field/method renames"""

    def __init__(self, config: Config):
        """Initialize rename command with configuration"""
        self.config = config
        self.backup_manager = None

        if config.backup.enabled:
            self.backup_manager = BackupManager(
                backup_dir=config.backup.directory,
                compression=config.backup.compression,
                keep_sessions=config.backup.keep_sessions,
            )

    def execute(self, csv_file: Path) -> bool:
        """
        Execute renaming operation from CSV file

        Args:
            csv_file: Path to CSV file containing changes

        Returns:
            True if successful, False if errors occurred
        """
        try:
            # Load changes from CSV
            changes = self._load_changes(csv_file)
            if not changes:
                logger.info("No changes found in CSV")
                return True

            # Filter by modules if specified
            if self.config.modules:
                changes = [c for c in changes if c.module in self.config.modules]
                if not changes:
                    logger.info(f"No changes for modules: {self.config.modules}")
                    return True

            logger.info(f"Loaded {len(changes)} changes from {csv_file}")

            # Start backup session if enabled
            if self.backup_manager and not self.config.dry_run:
                self.backup_manager.start_session("field_method_renaming")

            # Group changes by module and model
            changes_by_model = self._group_changes(changes)

            # Find and process files
            results = self._process_changes(changes_by_model)

            # Finalize backup
            if self.backup_manager and not self.config.dry_run:
                self.backup_manager.finalize_session()

            # Report results
            success_count = sum(
                1 for r in results if r.status == ProcessingStatus.SUCCESS
            )
            error_count = sum(1 for r in results if r.status == ProcessingStatus.ERROR)

            logger.info(
                f"Processing complete: {success_count} files updated, {error_count} errors"
            )

            return error_count == 0

        except Exception as e:
            logger.error(f"Error during renaming: {e}")
            return False

    def _load_changes(self, csv_file: Path) -> list[FieldChange]:
        """Load changes from CSV file"""
        try:
            df = pd.read_csv(csv_file)
            changes = []

            for _, row in df.iterrows():
                item_type = row.get("item_type", "field")
                confidence = row.get("confidence", 1.0)

                # Apply confidence threshold if configured
                if confidence < self.config.detection.confidence_threshold:
                    logger.debug(
                        f"Skipping low confidence change: {row['old_name']} ({confidence})"
                    )
                    continue

                changes.append(
                    FieldChange(
                        old_name=row["old_name"],
                        new_name=row["new_name"],
                        item_type=item_type,
                        module=row["module"],
                        model=row["model"],
                        confidence=confidence,
                    )
                )

            # Interactive confirmation if enabled
            if self.config.interactive and changes:
                changes = self._interactive_confirm_changes(changes)

            return changes

        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return []

    def _interactive_confirm_changes(
        self, changes: list[FieldChange]
    ) -> list[FieldChange]:
        """Interactive confirmation of changes"""
        confirmed = []
        print(f"\n{len(changes)} changes to review:\n")

        for i, change in enumerate(changes, 1):
            print(
                f"[{i}/{len(changes)}] Module: {change.module}, Model: {change.model}"
            )
            print(
                f"  {change.item_type.capitalize()}: {change.old_name} -> {change.new_name}"
            )
            print(f"  Confidence: {change.confidence:.2%}")

            response = input("Apply this change? (y/n/a=apply all/q=quit): ").lower()

            if response == "a":
                confirmed.extend(changes[i - 1 :])
                break
            elif response == "q":
                break
            elif response == "y":
                confirmed.append(change)

        print(f"\nConfirmed {len(confirmed)} changes\n")
        return confirmed

    def _group_changes(
        self, changes: list[FieldChange]
    ) -> dict[str, list[FieldChange]]:
        """Group changes by module.model"""
        grouped = {}
        for change in changes:
            key = f"{change.module}.{change.model}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(change)
        return grouped

    def _process_changes(
        self, changes_by_model: dict[str, list[FieldChange]]
    ) -> list[ProcessResult]:
        """Process all changes grouped by model"""
        results = []
        repo_path = Path(self.config.repo_path)

        for model_key, model_changes in changes_by_model.items():
            module_name = model_key.split(".")[0]
            module_path = repo_path / module_name

            if not module_path.exists():
                logger.warning(f"Module path not found: {module_path}")
                continue

            # Find relevant files
            files = self._find_files_for_module(module_path)

            # Process each file
            for file_path in files:
                result = self._process_file(file_path, model_changes)
                results.append(result)

        return results

    def _find_files_for_module(self, module_path: Path) -> list[Path]:
        """Find all relevant files in a module"""
        include_python = (
            self.config.renaming.file_types
            and "python" in self.config.renaming.file_types
        )
        include_xml = (
            self.config.renaming.file_types and "xml" in self.config.renaming.file_types
        )

        odoo_files = OdooModuleUtils.find_odoo_files(
            module_path,
            include_python=include_python,
            include_xml=include_xml,
            include_data=False,
        )

        # Combine all file lists
        files = []
        if include_python:
            files.extend(odoo_files["models"])
            files.extend(odoo_files["wizards"])
        if include_xml:
            files.extend(odoo_files["views"])
            files.extend(odoo_files["data"])

        return files

    def _process_file(
        self, file_path: Path, changes: list[FieldChange]
    ) -> ProcessResult:
        """Process a single file with changes"""
        try:
            # Backup if needed
            if self.backup_manager and not self.config.dry_run:
                self.backup_manager.backup_file(file_path)

            # Process based on file type
            if file_path.suffix == ".py":
                return self._process_python_file(file_path, changes)
            elif file_path.suffix == ".xml":
                return self._process_xml_file(file_path, changes)
            else:
                return ProcessResult(
                    file_path=file_path,
                    status=ProcessingStatus.SKIPPED,
                    error_message="Unsupported file type",
                )

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return ProcessResult(
                file_path=file_path, status=ProcessingStatus.ERROR, error_message=str(e)
            )

    def _process_python_file(
        self, file_path: Path, changes: list[FieldChange]
    ) -> ProcessResult:
        """Process Python file for renames"""
        content = file_path.read_text(encoding="utf-8")

        # Separate field and method changes
        field_changes = {c.old_name: c.new_name for c in changes if c.is_field}
        method_changes = {c.old_name: c.new_name for c in changes if c.is_method}

        if not field_changes and not method_changes:
            return ProcessResult(
                file_path=file_path, status=ProcessingStatus.NO_CHANGES
            )

        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return ProcessResult(
                file_path=file_path,
                status=ProcessingStatus.ERROR,
                error_message=f"Syntax error: {e}",
            )

        # Apply transformations
        transformer = ASTRenameTransformer(field_changes, method_changes)
        new_tree = transformer.visit(tree)

        if not transformer.changes_made:
            return ProcessResult(
                file_path=file_path, status=ProcessingStatus.NO_CHANGES
            )

        # Convert back to source
        new_content = ast.unparse(new_tree)

        # Write if not dry run
        if not self.config.dry_run:
            file_path.write_text(new_content, encoding="utf-8")

        return ProcessResult(
            file_path=file_path,
            status=ProcessingStatus.SUCCESS,
            changes_applied=len(transformer.changes_made),
        )

    def _process_xml_file(
        self, file_path: Path, changes: list[FieldChange]
    ) -> ProcessResult:
        """Process XML file for field and method references"""
        field_changes = {c.old_name: c.new_name for c in changes if c.is_field}
        method_changes = {c.old_name: c.new_name for c in changes if c.is_method}

        if not field_changes and not method_changes:
            return ProcessResult(
                file_path=file_path, status=ProcessingStatus.NO_CHANGES
            )

        content = file_path.read_text(encoding="utf-8")
        original_content = content
        changes_made = []

        # Apply safe text replacements to preserve formatting
        # This approach is more robust than parsing and rewriting XML

        # Process field changes
        for old_name, new_name in field_changes.items():
            # Safe patterns for field references
            safe_patterns = [
                (f'name="{old_name}"', f'name="{new_name}"'),
                (f"name='{old_name}'", f"name='{new_name}'"),
                (f'ref="{old_name}"', f'ref="{new_name}"'),
                (f"ref='{old_name}'", f"ref='{new_name}'"),
            ]

            for old_pattern, new_pattern in safe_patterns:
                if old_pattern in content:
                    count = content.count(old_pattern)
                    content = content.replace(old_pattern, new_pattern)
                    if count > 0:
                        changes_made.append(
                            f"Field {old_name}->{new_name}: {count} refs"
                        )
                        logger.debug(
                            f"Replaced {old_pattern} with {new_pattern} ({count} times)"
                        )

        # Process method changes
        for old_name, new_name in method_changes.items():
            # Safe patterns for method references
            safe_patterns = [
                # Button names
                (f'<button name="{old_name}"', f'<button name="{new_name}"'),
                (f"<button name='{old_name}'", f"<button name='{new_name}'"),
                # Actions
                (f'action="{old_name}"', f'action="{new_name}"'),
                (f"action='{old_name}'", f"action='{new_name}'"),
                # Method calls in eval
                (f".{old_name}(", f".{new_name}("),
            ]

            for old_pattern, new_pattern in safe_patterns:
                if old_pattern in content:
                    count = content.count(old_pattern)
                    content = content.replace(old_pattern, new_pattern)
                    if count > 0:
                        changes_made.append(
                            f"Method {old_name}->{new_name}: {count} refs"
                        )
                        logger.debug(
                            f"Replaced {old_pattern} with {new_pattern} ({count} times)"
                        )

        if content != original_content and not self.config.dry_run:
            file_path.write_text(content, encoding="utf-8")

        return ProcessResult(
            file_path=file_path,
            status=(
                ProcessingStatus.SUCCESS
                if changes_made
                else ProcessingStatus.NO_CHANGES
            ),
            changes_applied=len(changes_made),
        )


class ASTRenameTransformer(ast.NodeTransformer):
    """AST transformer for renaming fields and methods"""

    def __init__(self, field_changes: dict[str, str], method_changes: dict[str, str]):
        self.field_changes = field_changes
        self.method_changes = method_changes
        self.changes_made = []
        self.in_class = False

    def visit_ClassDef(self, node):
        """Track when we're inside a class definition"""
        old_in_class = self.in_class
        self.in_class = True
        node = self.generic_visit(node)
        self.in_class = old_in_class
        return node

    def visit_Assign(self, node):
        """Visit assignment nodes for field definitions"""
        # Check if this is a field definition (assignment with fields.* call)
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and self._is_fields_call(node.value)
        ):

            name = node.targets[0].id
            if name in self.field_changes:
                node.targets[0].id = self.field_changes[name]
                self.changes_made.append(
                    f"field_def:{name}->{self.field_changes[name]}"
                )
                logger.debug(
                    f"Renamed field definition: {name} -> {self.field_changes[name]}"
                )

        return self.generic_visit(node)

    def _is_fields_call(self, node) -> bool:
        """Check if node is a fields.* call"""
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "fields"
        )

    def visit_FunctionDef(self, node):
        """Visit function definitions for method renames"""
        if self.in_class and node.name in self.method_changes:
            old_name = node.name
            new_name = self.method_changes[old_name]
            node.name = new_name
            self.changes_made.append(f"method_def:{old_name}->{new_name}")
            logger.debug(f"Renamed method definition: {old_name} -> {new_name}")
        return self.generic_visit(node)

    def visit_Attribute(self, node):
        """Visit attribute access for field/method references"""
        # Handle self.field_name references
        if isinstance(node.value, ast.Name) and node.value.id in (
            "self",
            "rec",
            "record",
        ):

            if node.attr in self.field_changes:
                old_attr = node.attr
                node.attr = self.field_changes[old_attr]
                self.changes_made.append(f"field_ref:{old_attr}")
                logger.debug(f"Renamed field reference: {old_attr} -> {node.attr}")
            elif node.attr in self.method_changes:
                old_attr = node.attr
                node.attr = self.method_changes[old_attr]
                self.changes_made.append(f"method_ref:{old_attr}")
                logger.debug(f"Renamed method reference: {old_attr} -> {node.attr}")

        return self.generic_visit(node)

    def visit_Constant(self, node):
        """Visit string constants for field name references"""
        if isinstance(node.value, str):
            # Only replace in contexts where field names appear as strings
            # (e.g., in domain expressions, depends decorators, etc.)
            if node.value in self.field_changes:
                old_value = node.value
                node.value = self.field_changes[old_value]
                self.changes_made.append(f"field_str:{old_value}")
                logger.debug(f"Renamed field string: {old_value} -> {node.value}")
        return self.generic_visit(node)

    def visit_Call(self, node):
        """Visit function calls to handle super() method calls"""
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Call)
            and isinstance(node.func.value.func, ast.Name)
            and node.func.value.func.id == "super"
        ):

            if node.func.attr in self.method_changes:
                old_method = node.func.attr
                node.func.attr = self.method_changes[old_method]
                self.changes_made.append(f"super_call:{old_method}")
                logger.debug(
                    f"Renamed super() method call: {old_method} -> {node.func.attr}"
                )

        return self.generic_visit(node)
