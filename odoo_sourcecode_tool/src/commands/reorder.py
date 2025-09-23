"""
Unified reordering command for all reordering operations
Consolidates code, attributes, and XML reordering into a single module
"""

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import black
import isort
from core.backup_manager import BackupManager
from core.base_processor import ProcessingStatus, ProcessResult
from core.config import Config
from core.ordering import Ordering

logger = logging.getLogger(__name__)


class ReorderCommand:
    """Unified command handler for all reordering operations"""

    def __init__(self, config: Config):
        """Initialize unified reorder command with configuration"""
        self.config = config
        self.backup_manager = None
        if config.backup.enabled:
            self.backup_manager = BackupManager(
                backup_dir=config.backup.directory,
                compression=config.backup.compression,
                keep_sessions=config.backup.keep_sessions,
            )

    def execute(
        self,
        target: str,
        path: Path,
        recursive: bool = False,
        **options,
    ) -> ProcessResult:
        """
        Execute reordering operation based on target type

        Args:
            target: 'code', 'attributes', 'xml', or 'all'
            path: File or directory to process
            recursive: Process directories recursively
            **options: Additional options

        Returns:
            ProcessResult with status and details
        """
        try:
            # Start backup session if needed
            if self.backup_manager and not self.config.dry_run:
                session_type = f"reorder_{target}"
                self.backup_manager.start_session(session_type)

            # Execute based on target
            if target == "all":
                results = []

                # Reorder only Odoo field's attributes
                logger.info("Reordering field attributes...")
                attr_result = self._execute_field_attr_reorder(path, recursive)
                results.append(
                    ("Attributes", attr_result.status == ProcessingStatus.SUCCESS)
                )

                # Reorder all Python code including field attributes
                logger.info("Reordering code...")
                code_result = self._execute_python_reorder(path, recursive, **options)
                results.append(("Code", code_result.status == ProcessingStatus.SUCCESS))

                # Reorder only XML node attributes
                logger.info("Reordering XML attributes...")
                xml_result = self._execute_xml_reorder(path, recursive)
                results.append(("XML", xml_result.status == ProcessingStatus.SUCCESS))

                # Summary
                self._print_summary(results)

                # Finalize backup
                if self.backup_manager and not self.config.dry_run:
                    self.backup_manager.finalize_session()

                # Return success if all operations succeeded
                success = all(r[1] for r in results)
                return ProcessResult(
                    file_path=path,
                    status=(
                        ProcessingStatus.SUCCESS if success else ProcessingStatus.ERROR
                    ),
                    message=f"Processed {len(results)} targets",
                )

            elif target == "python_code":
                result = self._execute_python_reorder(path, recursive, **options)
            elif target == "python_field_attr":
                result = self._execute_field_attr_reorder(path, recursive)
            elif target == "xml_code":
                result = self._execute_xml_reorder(path, recursive)
            elif target == "xml_node_attr":
                # TODO: Implement XML node attribute reordering
                logger.error(f"Target '{target}' not yet implemented")
                return ProcessResult(
                    file_path=path,
                    status=ProcessingStatus.ERROR,
                    error_message=f"Target '{target}' not yet implemented",
                )
            else:
                logger.error(f"Unknown target: {target}")
                return ProcessResult(
                    file_path=path,
                    status=ProcessingStatus.ERROR,
                    error_message=f"Unknown target: {target}",
                )

            # Finalize backup for single operations
            if self.backup_manager and not self.config.dry_run:
                self.backup_manager.finalize_session()

            return result

        except Exception as e:
            logger.error(f"Error during reordering: {e}")
            return ProcessResult(
                file_path=path, status=ProcessingStatus.ERROR, error_message=str(e)
            )

    # ========================================================================
    # CODE REORDERING
    # ========================================================================

    def _execute_python_reorder(
        self,
        path: Path,
        recursive: bool,
        **options,
    ) -> ProcessResult:
        """Execute code reordering operation on path"""

        # Process path
        if path.is_file():
            return self._process_code_file(path)
        elif path.is_directory():
            success = self._process_code_directory(path, recursive)
            return ProcessResult(
                file_path=path,
                status=ProcessingStatus.SUCCESS if success else ProcessingStatus.ERROR,
                message=f"Directory processing {'completed' if success else 'failed'}",
            )
        else:
            logger.error(f"Invalid path: {path}")
            return ProcessResult(
                file_path=path,
                status=ProcessingStatus.ERROR,
                error_message=f"Invalid path: {path}",
            )

    def _process_code_file(
        self,
        file_path: Path,
    ) -> ProcessResult:
        """Process single Python file for code reordering"""
        if not file_path.suffix == ".py":
            return ProcessResult(
                status=ProcessingStatus.SKIPPED,
                file_path=file_path,
                message="Not a Python file",
            )

        try:
            # Read file content
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Create ordering instance with config and content
            ordering = Ordering(self.config, content, file_path)

            # Order the code
            ordered_content = ordering.order_code(content)

            # Apply Black formatting if configured
            if self.config.formatting.use_black:
                try:
                    mode = black.Mode(
                        line_length=self.config.formatting.black_line_length,
                        target_versions=set(),
                    )
                    ordered_content = black.format_str(ordered_content, mode=mode)
                except Exception as e:
                    logger.warning(f"Black formatting failed: {e}")

            # Apply isort if configured
            if self.config.formatting.use_isort:
                try:
                    ordered_content = isort.code(ordered_content)
                except Exception as e:
                    logger.warning(f"isort formatting failed: {e}")

            # Check if content changed
            if ordered_content == original_content:
                logger.info(f"No changes needed for {file_path}")
                return ProcessResult(
                    status=ProcessingStatus.SUCCESS,
                    file_path=file_path,
                    message="No changes needed",
                )

            # Save or preview changes
            if self.config.dry_run:
                logger.info(f"[DRY RUN] Would reorder {file_path}")
                # Could show diff here
            else:
                # Backup if needed
                if self.backup_manager:
                    self.backup_manager.backup_file(file_path)

                # Write ordered content
                file_path.write_text(ordered_content, encoding="utf-8")
                logger.info(f"Reordered {file_path}")

            return ProcessResult(
                status=ProcessingStatus.SUCCESS,
                file_path=file_path,
                message="File reordered successfully",
            )

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return ProcessResult(
                status=ProcessingStatus.ERROR,
                file_path=file_path,
                message=str(e),
            )

    def _process_code_directory(self, dir_path: Path, recursive: bool) -> bool:
        """Process directory for code reordering"""
        success_count = 0
        error_count = 0

        # Find Python files
        pattern = "**/*.py" if recursive else "*.py"
        for py_file in dir_path.glob(pattern):
            result = self._process_code_file(py_file)
            if result.status == ProcessingStatus.SUCCESS:
                success_count += 1
            elif result.status == ProcessingStatus.ERROR:
                error_count += 1

        logger.info(
            f"Processed {success_count} files successfully, {error_count} errors"
        )
        return error_count == 0

    # ========================================================================
    # ATTRIBUTES REORDERING (from reorder_attributes.py)
    # ========================================================================

    def _execute_field_attr_reorder(self, path: Path, recursive: bool) -> ProcessResult:
        """Execute attribute reordering operation on path"""
        if path.is_file():
            return self._process_attributes_file(path)
        elif path.is_directory():
            success = self._process_attributes_directory(path, recursive)
            return ProcessResult(
                file_path=path,
                status=ProcessingStatus.SUCCESS if success else ProcessingStatus.ERROR,
                message=f"Attribute reordering {'completed' if success else 'failed'}",
            )
        else:
            logger.error(f"Invalid path: {path}")
            return ProcessResult(
                file_path=path,
                status=ProcessingStatus.ERROR,
                error_message=f"Invalid path: {path}",
            )

    def _process_attributes_file(self, file_path: Path) -> ProcessResult:
        """Process single Python file for attribute reordering"""
        if not file_path.suffix == ".py":
            return ProcessResult(
                status=ProcessingStatus.SKIPPED,
                file_path=file_path,
                message="Not a Python file",
            )

        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Process field definitions
            modified_content = self._reorder_field_attributes(content)

            if modified_content == original_content:
                logger.info(f"No changes needed for {file_path}")
                return ProcessResult(
                    status=ProcessingStatus.SUCCESS,
                    file_path=file_path,
                    message="No changes needed",
                )

            # Save or preview changes
            if self.config.dry_run:
                logger.info(f"[DRY RUN] Would reorder attributes in {file_path}")
            else:
                if self.backup_manager:
                    self.backup_manager.backup_file(file_path)
                file_path.write_text(modified_content, encoding="utf-8")
                logger.info(f"Reordered attributes in {file_path}")

            return ProcessResult(
                status=ProcessingStatus.SUCCESS,
                file_path=file_path,
                message="Attributes reordered successfully",
            )

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return ProcessResult(
                status=ProcessingStatus.ERROR,
                file_path=file_path,
                message=str(e),
            )

    def _process_attributes_directory(self, dir_path: Path, recursive: bool) -> bool:
        """Process directory for attribute reordering"""
        success_count = 0
        error_count = 0

        pattern = "**/*.py" if recursive else "*.py"
        for py_file in dir_path.glob(pattern):
            result = self._process_attributes_file(py_file)
            if result.status == ProcessingStatus.SUCCESS:
                success_count += 1
            elif result.status == ProcessingStatus.ERROR:
                error_count += 1

        logger.info(
            f"Processed {success_count} files successfully, {error_count} errors"
        )
        return error_count == 0

    def _reorder_field_attributes(self, content: str) -> str:
        """Reorder field attributes within field definitions"""
        lines = content.splitlines(keepends=True)
        modified_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this line contains a field definition
            if "fields." in line and "=" in line:
                field_start = i
                field_lines = [line]

                # Collect all lines that are part of this field definition
                i += 1
                while i < len(lines):
                    if lines[i].strip() and not lines[i].strip().startswith(")"):
                        field_lines.append(lines[i])
                        i += 1
                    elif lines[i].strip().startswith(")"):
                        field_lines.append(lines[i])
                        i += 1
                        break
                    else:
                        break

                # Process the field definition
                field_text = "".join(field_lines)
                reordered = self._reorder_single_field_attributes(field_text)
                modified_lines.append(reordered)
            else:
                modified_lines.append(line)
                i += 1

        return "".join(modified_lines)

    def _reorder_single_field_attributes(self, field_def: str) -> str:
        """Reorder attributes in a single field definition"""
        # Extract field type and parameters
        match = re.match(
            r"(\s*)(\w+)\s*=\s*fields\.(\w+)\((.*)\)", field_def, re.DOTALL
        )
        if not match:
            return field_def

        indent, field_name, field_type, params = match.groups()

        if not params.strip():
            return field_def

        # Parse parameters
        param_dict = self._parse_field_parameters(params)
        if not param_dict:
            return field_def

        # Define attribute order from config
        attribute_order = self.config.ordering.field_attribute_order

        # Build ordered parameters
        ordered_params = []
        for attr in attribute_order:
            if attr in param_dict:
                ordered_params.append(f"{attr}={param_dict[attr]}")

        # Add any remaining parameters not in the order
        for key, value in param_dict.items():
            param_str = f"{key}={value}" if key else value
            if param_str not in ordered_params:
                ordered_params.append(param_str)

        # Reconstruct field definition
        if len(ordered_params) <= 2:
            # Single line
            return f"{indent}{field_name} = fields.{field_type}({', '.join(ordered_params)})\n"
        else:
            # Multi-line
            param_lines = [f"\n{indent}    {param}," for param in ordered_params]
            return f"{indent}{field_name} = fields.{field_type}({''.join(param_lines)}\n{indent})\n"

    def _parse_field_parameters(self, params_str: str) -> dict[str, str]:
        """Parse field parameters string into a dictionary"""
        # Simple parameter parsing - handles most common cases
        params = {}
        param_pattern = r"(\w+)\s*=\s*([^,]+(?:\([^)]*\)[^,]*)?)"

        for match in re.finditer(param_pattern, params_str):
            key = match.group(1)
            value = match.group(2).strip()
            params[key] = value

        # Handle positional parameters (like string as first param)
        if params_str.strip() and not params:
            # Might be just a string literal
            if params_str.strip()[0] in ('"', "'"):
                params["string"] = params_str.strip()

        return params

    # ========================================================================
    # XML REORDERING (from reorder_xml.py)
    # ========================================================================

    def _execute_xml_reorder(self, path: Path, recursive: bool) -> ProcessResult:
        """Execute XML reordering operation on path"""
        if path.is_file():
            return self._process_xml_file(path)
        elif path.is_directory():
            success = self._process_xml_directory(path, recursive)
            return ProcessResult(
                file_path=path,
                status=ProcessingStatus.SUCCESS if success else ProcessingStatus.ERROR,
                message=f"XML reordering {'completed' if success else 'failed'}",
            )
        else:
            logger.error(f"Invalid path: {path}")
            return ProcessResult(
                file_path=path,
                status=ProcessingStatus.ERROR,
                error_message=f"Invalid path: {path}",
            )

    def _process_xml_file(self, file_path: Path) -> ProcessResult:
        """Process single XML file for attribute reordering"""
        if not file_path.suffix == ".xml":
            return ProcessResult(
                status=ProcessingStatus.SKIPPED,
                file_path=file_path,
                message="Not an XML file",
            )

        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Parse and reorder XML
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Reorder attributes in all elements
            self._reorder_element_attributes(root)

            # Convert back to string
            modified_content = ET.tostring(
                root, encoding="unicode", xml_declaration=True
            )

            # Preserve original formatting style
            if "<?xml" not in original_content:
                modified_content = modified_content.replace(
                    "<?xml version='1.0' encoding='us-ascii'?>\n", ""
                )

            if modified_content == original_content:
                logger.info(f"No changes needed for {file_path}")
                return ProcessResult(
                    status=ProcessingStatus.SUCCESS,
                    file_path=file_path,
                    message="No changes needed",
                )

            # Save or preview changes
            if self.config.dry_run:
                logger.info(f"[DRY RUN] Would reorder XML attributes in {file_path}")
            else:
                if self.backup_manager:
                    self.backup_manager.backup_file(file_path)
                file_path.write_text(modified_content, encoding="utf-8")
                logger.info(f"Reordered XML attributes in {file_path}")

            return ProcessResult(
                status=ProcessingStatus.SUCCESS,
                file_path=file_path,
                message="XML attributes reordered successfully",
            )

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return ProcessResult(
                status=ProcessingStatus.ERROR,
                file_path=file_path,
                message=str(e),
            )

    def _process_xml_directory(self, dir_path: Path, recursive: bool) -> bool:
        """Process directory for XML reordering"""
        success_count = 0
        error_count = 0

        pattern = "**/*.xml" if recursive else "*.xml"
        for xml_file in dir_path.glob(pattern):
            result = self._process_xml_file(xml_file)
            if result.status == ProcessingStatus.SUCCESS:
                success_count += 1
            elif result.status == ProcessingStatus.ERROR:
                error_count += 1

        logger.info(
            f"Processed {success_count} files successfully, {error_count} errors"
        )
        return error_count == 0

    def _reorder_element_attributes(self, element: ET.Element) -> None:
        """Recursively reorder attributes in XML element and its children"""
        # Get the attribute order for this element type
        tag_name = element.tag
        attribute_order = self.xml_attribute_orders.get(
            tag_name, self.xml_attribute_orders["_default"]
        )

        # Get current attributes
        current_attrs = element.attrib.copy()

        # Clear and reorder attributes
        element.attrib.clear()

        # Add attributes in order
        for attr in attribute_order:
            if attr in current_attrs:
                element.set(attr, current_attrs.pop(attr))

        # Add remaining attributes
        for attr, value in current_attrs.items():
            element.set(attr, value)

        # Process children
        for child in element:
            self._reorder_element_attributes(child)

    def _init_xml_attribute_orders(self) -> dict[str, list[str]]:
        """Initialize XML attribute orders for different element types"""
        return {
            # Default order for any element
            "_default": [
                "id",
                "name",
                "model",
                "string",
                "type",
                "class",
                "position",
                "attrs",
                "states",
                "invisible",
                "readonly",
                "required",
            ],
            # Specific orders for Odoo XML elements
            "record": ["id", "model", "forcecreate"],
            "field": [
                "name",
                "type",
                "string",
                "widget",
                "required",
                "readonly",
                "invisible",
                "attrs",
                "states",
                "help",
                "placeholder",
            ],
            "button": [
                "name",
                "string",
                "type",
                "class",
                "icon",
                "states",
                "attrs",
                "invisible",
                "confirm",
                "context",
            ],
            "tree": [
                "string",
                "default_order",
                "create",
                "edit",
                "delete",
                "duplicate",
                "import",
                "export_xlsx",
                "multi_edit",
                "sample",
            ],
            "form": ["string", "create", "edit", "delete", "duplicate"],
            "kanban": [
                "default_group_by",
                "class",
                "sample",
                "quick_create",
                "quick_create_view",
            ],
            "search": ["string"],
            "group": ["name", "string", "col", "colspan", "attrs", "invisible"],
            "notebook": ["colspan", "attrs", "invisible"],
            "page": ["name", "string", "attrs", "invisible"],
            "xpath": ["expr", "position"],
            "attribute": ["name"],
            "div": ["class", "attrs", "invisible"],
            "span": ["class", "attrs", "invisible"],
            "t": [
                "t-if",
                "t-elif",
                "t-else",
                "t-foreach",
                "t-as",
                "t-esc",
                "t-raw",
                "t-field",
                "t-options",
                "t-set",
                "t-value",
                "t-call",
                "t-call-assets",
            ],
            "template": ["id", "name", "inherit_id", "priority"],
            "menuitem": ["id", "name", "parent", "sequence", "action", "groups"],
            "act_window": ["id", "name", "model", "view_mode", "domain", "context"],
        }

    def _print_summary(self, results: list[tuple[str, bool]]) -> None:
        """Print summary of all operations"""
        print("\n" + "=" * 60)
        print("REORDERING SUMMARY")
        print("=" * 60)

        for name, success in results:
            status = "✓" if success else "✗"
            print(f"{status} {name} reordering: {'Success' if success else 'Failed'}")

        print("=" * 60)

        total = len(results)
        successful = sum(1 for _, s in results if s)

        if successful == total:
            print(f"✓ All {total} operations completed successfully!")
        else:
            print(f"⚠ {successful}/{total} operations succeeded")
