#!/usr/bin/env python3
"""
Ordering functions and patterns for code elements.

This module combines pattern definitions, classification and sorting operations
for code elements. Patterns define the rules and constants, classification
determines the category of an element, and sorting orders elements based on
their categories. These operations form a natural pipeline for code organization.

The module provides:
- Pattern definitions for Odoo-specific code organization
- Field classification and sorting (semantic, type-based, strict)
- Method classification and sorting (by category)
- Import classification and sorting (by group)
- Utility functions for element analysis
- AST parsing and inventory extraction (consolidated from ast_parser.py)
"""

import ast
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import black
import isort
from blueprint.blueprint import (
    FIELD_ATTRIBUTE_GENERIC,
    FIELD_TYPE_ATTRIBUTES,
    METHOD_ORDER,
    MODEL_ATTRIBUTES,
    SECTION_HEADERS,
    XML_ATTRIBUTE_ORDER,
)
from core.base_processor import ProcessingStatus, ProcessResult
from core.classification_rule_field import (
    ClassificationRuleField,
    get_default_field_rules,
)
from core.classification_rule_method import (
    ClassificationRuleMethod,
    get_default_method_rules,
)
from core.config import Config
from core.path_analyzer import FileType, PathAnalysis, path_analyzer

logger = logging.getLogger(__name__)


class Order:
    """Python/AST-specific ordering and reorganization logic for Odoo files."""

    def __init__(self, config=None):
        """Initialize Ordering with configuration.

        Args:
            config: Configuration object with add_section_headers, etc.
        """
        if config is None:
            config = Config()

        self.config = config
        self._method_rules = get_default_method_rules()
        self._field_rules = get_default_field_rules()
        self.attribute_orders = XML_ATTRIBUTE_ORDER
        self._register_handlers()

    def _register_handlers(self):
        """Register file type handlers with the registry"""
        # Register Python handlers
        path_analyzer.register_handler(
            FileType.PYTHON,
            "order",
            self._process_single_python_file,
        )
        path_analyzer.register_handler(
            FileType.PYTHON,
            "order_attributes",
            self._process_python_attributes_only,
        )

        # Register XML handlers
        path_analyzer.register_handler(
            FileType.XML,
            "order",
            self._process_single_xml_file,
        )
        path_analyzer.register_handler(
            FileType.XML,
            "order_attributes",
            self._process_xml_attributes_only,
        )

    # ========================================================================
    # MAIN ENTRY POINTS - Called by CLI via getattr
    # ========================================================================

    def process_python(
        self,
        path: Path,
        path_info: PathAnalysis | dict = None,
        mode: str | list[str] = "module",
        **options,
    ) -> ProcessResult:
        """Process Python files with specified reordering mode(s).

        Args:
            path: Path to file or directory
            path_info: PathAnalysis object or dict with path information
            mode: Processing mode(s) - 'module', 'field_attributes', or list of both
                  'module' - Full module structural reorganization with formatting
                  'field_attributes' - Only reorder field attributes
            **options: Additional processing options

        Returns:
            ProcessResult with status and changes applied
        """
        if not path_info:
            logger.error("Path analysis required. Please use CLI interface.")
            return ProcessResult(
                file_path=path,
                status=ProcessingStatus.ERROR,
                error_message="Path analysis required",
            )

        # Normalize mode to list
        modes = [mode] if isinstance(mode, str) else mode

        # Handle both PathAnalysis objects and dicts
        if isinstance(path_info, PathAnalysis):
            is_file = path_info.is_file
            python_files = path_info.python_files
        else:
            is_file = path_info.get("is_file", False)
            python_files = path_info.get("python_files", [])

        if is_file:
            return self._process_single_python_file(
                path,
                modes,
            )
        elif python_files:
            return self._process_file_list(
                python_files,
                lambda f: self._process_single_python_file(f, modes),
            )
        else:
            return ProcessResult(
                file_path=path,
                status=ProcessingStatus.SUCCESS,
                changes_applied=0,
            )

    def process_xml(
        self,
        path: Path,
        path_info: PathAnalysis | dict = None,
        mode: str | list[str] = "structure",
        **options,
    ) -> ProcessResult:
        """Process XML files with specified reordering mode(s).

        Args:
            path: Path to file or directory
            path_info: PathAnalysis object or dict with path information
            mode: Processing mode(s) - 'structure', 'attributes', or list of both
                  'structure' - Full XML structural reorganization
                  'attributes' - Only reorder element attributes
            **options: Additional processing options

        Returns:
            ProcessResult with status and changes applied
        """
        if not path_info:
            logger.error("Path analysis required. Please use CLI interface.")
            return ProcessResult(
                file_path=path,
                status=ProcessingStatus.ERROR,
                error_message="Path analysis required",
            )

        # Normalize mode to list
        modes = [mode] if isinstance(mode, str) else mode

        # Handle both PathAnalysis objects and dicts
        if isinstance(path_info, PathAnalysis):
            is_file = path_info.is_file
            xml_files = path_info.xml_files
        else:
            is_file = path_info.get("is_file", False)
            xml_files = path_info.get("xml_files", [])

        if is_file:
            return self._process_single_xml_file(path, modes)
        elif xml_files:
            return self._process_file_list(
                xml_files, lambda f: self._process_single_xml_file(f, modes)
            )
        else:
            return ProcessResult(
                file_path=path,
                status=ProcessingStatus.SUCCESS,
                changes_applied=0,
            )

    def process_all(
        self,
        path: Path,
        path_info: PathAnalysis | dict = None,
        **options,
    ) -> ProcessResult:
        """Process all types of files (Python and XML)"""
        if not path_info:
            logger.error("Path analysis required. Please use CLI interface.")
            return ProcessResult(
                file_path=path,
                status=ProcessingStatus.ERROR,
                error_message="Path analysis required",
            )

        results = []

        # Process Python (both field attributes and module structure)
        logger.info("Reordering Python files...")
        python_result = self.process_python(
            path, path_info, mode=["field_attributes", "module"], **options
        )
        results.append(("Python", python_result.status == ProcessingStatus.SUCCESS))

        # Finally process XML (both structure and attributes)
        logger.info("Reordering XML...")
        xml_result = self.process_xml(
            path, path_info, mode=["structure", "attributes"], **options
        )
        results.append(("XML", xml_result.status == ProcessingStatus.SUCCESS))

        # Print summary
        self._print_summary(results)

        # Return aggregate result
        success = all(r[1] for r in results)
        return ProcessResult(
            file_path=path,
            status=ProcessingStatus.SUCCESS if success else ProcessingStatus.ERROR,
            changes_applied=len(results) if success else 0,
        )

    # ========================================================================
    # FILE PROCESSING LOGIC
    # ========================================================================

    def _process_single_python_file(
        self,
        file_path: Path,
        modes: list[str],
    ) -> ProcessResult:
        """Process a single Python file with specified modes.

        Args:
            file_path: Path to the Python file
            modes: List of processing modes to apply

        Returns:
            ProcessResult with status and changes
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content
            ordered_content = content
            changes_made = []

            # Apply each mode in sequence
            for mode in modes:
                if mode == "field_attributes":
                    # Field attributes only
                    ordered_content = self.reorganize_node(
                        ordered_content, level="field_attributes"
                    )
                    if ordered_content != content:
                        changes_made.append("field_attributes")
                        content = ordered_content
                elif mode == "module":
                    # Full module reorganization
                    ordered_content = self.reorganize_node(
                        ordered_content, level="module"
                    )
                    if ordered_content != content:
                        changes_made.append("module")
                        content = ordered_content

                    # Apply formatting if configured (only for module level)
                    if getattr(self.config, "use_black", True):
                        try:
                            mode_obj = black.Mode(line_length=88, target_versions=set())
                            ordered_content = black.format_str(
                                ordered_content, mode=mode_obj
                            )
                        except Exception as e:
                            logger.warning(f"Black formatting failed: {e}")

                    if getattr(self.config, "use_isort", True):
                        try:
                            ordered_content = isort.code(ordered_content)
                        except Exception as e:
                            logger.warning(f"isort formatting failed: {e}")
                else:
                    logger.warning(f"Unknown Python processing mode: {mode}")

            # Check if content changed
            if ordered_content == original_content:
                logger.info(f"No changes needed for {file_path}")
                return ProcessResult(
                    status=ProcessingStatus.SUCCESS,
                    file_path=file_path,
                )

            # Save or preview changes
            if self.config.dry_run:
                modes_str = " and ".join(changes_made) if changes_made else "formatting"
                logger.info(f"[DRY RUN] Would reorder {modes_str} in {file_path}")
            else:
                file_path.write_text(ordered_content, encoding="utf-8")
                modes_str = " and ".join(changes_made) if changes_made else "formatting"
                logger.info(f"Reordered {modes_str} in {file_path}")

            return ProcessResult(
                status=ProcessingStatus.SUCCESS,
                file_path=file_path,
                changes_applied=len(changes_made) if changes_made else 1,
            )

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return ProcessResult(
                status=ProcessingStatus.ERROR,
                file_path=file_path,
                error_message=str(e),
            )

    def _process_single_xml_file(
        self,
        file_path: Path,
        modes: list[str],
    ) -> ProcessResult:
        """Process a single XML file with specified modes.

        Args:
            file_path: Path to the XML file
            modes: List of processing modes to apply

        Returns:
            ProcessResult with status and changes
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content
            ordered_content = content
            changes_made = []

            # Apply each mode in sequence
            for mode in modes:
                if mode == "structure":
                    # Full structural reorganization
                    ordered_content = self.reorganize_xml(file_path, "structure")
                    if ordered_content != content:
                        changes_made.append("structure")
                        content = ordered_content
                elif mode == "attributes":
                    # Attribute-only reordering
                    ordered_content = self.reorganize_xml(file_path, "attributes")
                    if ordered_content != content:
                        changes_made.append("attributes")
                        content = ordered_content
                else:
                    logger.warning(f"Unknown XML processing mode: {mode}")

            if ordered_content == original_content:
                logger.info(f"No changes needed for {file_path}")
                return ProcessResult(
                    status=ProcessingStatus.SUCCESS,
                    file_path=file_path,
                )

            # Save or preview changes
            if self.config.dry_run:
                modes_str = " and ".join(changes_made)
                logger.info(f"[DRY RUN] Would reorder {modes_str} in {file_path}")
            else:
                file_path.write_text(ordered_content, encoding="utf-8")
                modes_str = " and ".join(changes_made)
                logger.info(f"Reordered {modes_str} in {file_path}")

            return ProcessResult(
                status=ProcessingStatus.SUCCESS,
                file_path=file_path,
                changes_applied=len(changes_made),
            )

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return ProcessResult(
                status=ProcessingStatus.ERROR,
                file_path=file_path,
                error_message=str(e),
            )

    def _process_python_attributes_only(
        self,
        file_path: Path,
        modes: list[str] = None,
    ) -> ProcessResult:
        """Process only field attributes in a Python file.

        Args:
            file_path: Path to the Python file
            modes: Unused, kept for interface consistency

        Returns:
            ProcessResult with status and changes
        """
        return self._process_single_python_file(file_path, ["field_attributes"])

    def _process_xml_attributes_only(
        self,
        file_path: Path,
        modes: list[str] = None,
    ) -> ProcessResult:
        """Process only XML attributes in an XML file.

        Args:
            file_path: Path to the XML file
            modes: Unused, kept for interface consistency

        Returns:
            ProcessResult with status and changes
        """
        return self._process_single_xml_file(file_path, ["attributes"])

    def _process_file_list(
        self,
        file_list: list[Path],
        processor_func=None,
        action: str = "order",
    ) -> ProcessResult:
        """Process a list of files using the registry or specified processor"""
        success_count = 0
        error_count = 0
        skipped_count = 0

        for file_path in file_list:
            # Use registry if no processor specified
            if processor_func is None:
                file_type = path_analyzer.get_file_type(file_path)
                if file_type == FileType.UNKNOWN:
                    logger.debug(f"Skipping unknown file type: {file_path}")
                    skipped_count += 1
                    continue

                handler = path_analyzer.get_handler(file_type, action)
                if not handler:
                    logger.debug(f"No handler for {file_type.value}:{action}")
                    skipped_count += 1
                    continue

                result = handler(file_path)
            else:
                result = processor_func(file_path)

            if result.status == ProcessingStatus.SUCCESS:
                success_count += 1
            elif result.status == ProcessingStatus.ERROR:
                error_count += 1

        logger.info(
            f"Processed {success_count} files successfully, "
            f"{error_count} errors, {skipped_count} skipped"
        )

        return ProcessResult(
            file_path=Path("."),
            status=(
                ProcessingStatus.SUCCESS if error_count == 0 else ProcessingStatus.ERROR
            ),
            changes_applied=success_count,
        )

    def _print_summary(
        self,
        results: list[tuple[str, bool]],
    ) -> None:
        """Print summary of all operations"""
        print("\n" + "=" * 60)
        print("REORDERING SUMMARY")
        print("=" * 60)

        for name, success in results:
            status = "✓" if success else "✗"
            print(f"{status} {name}: {'Success' if success else 'Failed'}")

        print("=" * 60)

        total = len(results)
        successful = sum(1 for _, s in results if s)

        if successful == total:
            print(f"✓ All {total} operations completed successfully!")
        else:
            print(f"⚠ {successful}/{total} operations succeeded")

    # ============================================================
    # PATTERNS
    # ============================================================

    # ============================================================
    # PARSING & EXTRACTION
    # ============================================================

    def extract_imports(
        self,
        tree: ast.Module,
    ) -> list[ast.stmt]:
        """Extract all import statements from the module.

        Args:
            tree: Parsed AST tree

        Returns:
            list[ast.stmt]: List of Import and ImportFrom nodes
        """
        imports = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)
        return imports

    def extract_assignments(
        self,
        tree: ast.Module,
    ) -> list[ast.Assign]:
        """Extract all top-level assignments (module-level variables).

        Args:
            tree: Parsed AST tree

        Returns:
            list[ast.Assign]: List of assignment nodes at module level
        """
        assignments = []
        for node in tree.body:
            if isinstance(node, (ast.Assign)):
                assignments.append(node)
        return assignments

    def extract_functions(
        self,
        tree: ast.Module,
    ) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
        """Extract all top-level function definitions.

        Only returns functions at module level, not methods inside classes.

        Args:
            tree: Parsed AST tree

        Returns:
            list[Union[ast.FunctionDef, ast.AsyncFunctionDef]]: Module-level functions
        """
        functions = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node)
        return functions

    def extract_classes(
        self,
        tree: ast.Module,
    ) -> list[ast.ClassDef]:
        """Extract all top-level class definitions.

        Args:
            tree: Parsed AST tree

        Returns:
            list[ast.ClassDef]: List of class definition nodes
        """
        classes = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes.append(node)
        return classes

    def extract_class_bases(
        self,
        class_node: ast.ClassDef,
    ) -> list:
        """Extract base classes from a class definition.

        Args:
            class_node: AST ClassDef node

        Returns:
            list: List of base class AST nodes, or ['models.Model'] as fallback
        """
        if not class_node.bases:
            return ["models.Model"]  # Fallback for Odoo
        bases = []
        for base in class_node.bases:
            bases.append(base)
        return bases

    def extract_class_elements(
        self,
        class_node: ast.ClassDef,
    ) -> dict[str, list[ast.AST] | dict[str, ast.AST]]:
        """Extract and categorize all elements from a class definition.

        Processes the class body to identify and categorize different types
        of class members including methods, fields, properties, and nested classes.

        Args:
            class_node: AST ClassDef node to analyze

        Returns:
            dict[str, list[ast.AST]]: Dictionary with keys:
                - 'decorators': Class decorators
                - 'docstring': Class docstring
                - 'model_attrs': Model attributes
                - 'properties': Property-decorated methods
                - 'class_vars': Nested classes
                - 'fields': Field assignments and annotated assignments
                - 'methods': Regular methods
                - 'class_bases': Base classes
        """
        elements = {
            "decorators": [],
            "class_bases": [],
            "docstring": [],
            "model_attrs": [],
            "class_vars": [],
            "properties": [],
            "fields": [],
            "methods": [],
        }

        elements["decorators"] = class_node.decorator_list
        elements["class_bases"] = self.extract_class_bases(class_node)

        if ast.get_docstring(class_node):
            for node in class_node.body:
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                    elements["docstring"].append(node)
                    break

        for node in class_node.body:
            if isinstance(node, (ast.ClassDef,)):
                # Nested classes
                elements["class_vars"].append(node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check if it's a property
                if self._is_property(node):
                    elements["properties"].append(node)
                else:
                    elements["methods"].append(node)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                if hasattr(node, "targets") and node.targets:
                    if isinstance(node.targets[0], ast.Name):
                        name = node.targets[0].id
                        if name in MODEL_ATTRIBUTES:
                            elements["model_attrs"].append(node)
                        else:
                            reordered_node = self.sort_field_attributes(node)
                            elements["fields"].append(
                                reordered_node if reordered_node else node
                            )

        if elements["fields"]:
            elements["fields"] = self.group_fields_by_category(elements["fields"])

        if elements["methods"]:
            elements["methods"] = self.group_methods_by_category(elements["methods"])

        return elements

    def extract_decorators(
        self,
        node: ast.FunctionDef,
    ) -> list[str]:
        """Extract decorator names from a method node.

        Args:
            node: AST FunctionDef node

        Returns:
            List of decorator names with @ prefix
        """
        decorators = []
        for decorator in node.decorator_list:
            decorator_name = self.get_decorator_name(decorator)
            if decorator_name:
                decorators.append(f"@{decorator_name}")
        return decorators

    def extract_elements(
        self,
        tree: ast.Module,
    ) -> dict[str, list[ast.AST]]:
        """
        Extract all elements from the module, organized by type.

        Args:
            tree: Parsed AST tree

        Returns:
            Dictionary with keys:
            - 'imports': Import and ImportFrom nodes
            - 'module_vars': Top-level Assign nodes
            - 'functions': FunctionDef and AsyncFunctionDef nodes
            - 'classes': ClassDef nodes
        """
        elements = {
            "imports": [],
            "module_vars": [],
            "functions": [],
            "classes": [],
        }

        # Extract imports
        elements["imports"] = self.extract_imports(tree)

        # Extract module-level variables
        elements["module_vars"] = self.extract_assignments(tree)

        # Extract top-level functions
        elements["functions"] = self.extract_functions(tree)

        # Extract classes
        elements["classes"] = self.extract_classes(tree)

        return elements

    # ============================================================
    # CLASSIFICATION FUNCTIONS
    # ============================================================

    def classify_model_element(
        self,
        node: ast.AST,
    ) -> str:
        """
        Classify a model-level element.

        Args:
            node: AST node

        Returns:
            Element type
        """
        if isinstance(node, ast.Assign):
            # Check for model attributes
            if any(isinstance(target, ast.Name) for target in node.targets):
                target_name = (
                    node.targets[0].id if isinstance(node.targets[0], ast.Name) else ""
                )
                if target_name.startswith("_"):
                    if target_name == "_sql_constraints":
                        return "sql_constraint"
                    return "model_attribute"
                return "field"

        elif isinstance(node, ast.FunctionDef):
            return "method"

        elif isinstance(node, ast.ClassDef):
            return "class"

        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            # Docstring
            return "docstring"

        return "unknown"

    def classify_field(
        self,
        node: ast.Assign | ast.AnnAssign,
    ) -> str:
        """
        Classify a field using the rule-based system.

        Args:
            node: AST node of the field

        Returns:
            Field category as string
        """
        field_info = self.get_field_info(node)

        # Check rules in priority order (they're already sorted)
        for rule in self._field_rules:
            if rule.matches(field_info["field_name"], field_info):
                return rule.category

        # This should never happen if rules are complete
        return "UNCATEGORIZED"

    def classify_method(
        self,
        node: ast.FunctionDef,
    ) -> str:
        """
        Classify a method using the rule-based system.

        Args:
            node: AST node of the method

        Returns:
            Method category as string
        """
        method_name = self.get_node_name(node)
        decorators = self.extract_decorators(node)

        # Check rules in priority order (they're already sorted)
        for rule in self._method_rules:
            if rule.matches(method_name, decorators):
                return rule.category

        # This should never happen if rules are complete
        return "UNCATEGORIZED"

    def group_fields_by_category(
        self,
        fields: list[ast.Assign | ast.AnnAssign],
    ) -> dict[str, list]:
        """Group fields by their category based on name and attributes.

        Uses classify_field() to determine each fields's category, then
        groups them into a dictionary.

        Args:
            fields: List of AST ast.Assign or ast.AnnAssign nodes

        Returns:
            dict[str, list]: Dictionary mapping category names to lists of fields
        """
        groups = {}

        for field in fields:
            category = self.classify_field(field)
            # Add to appropriate group
            if category not in groups:
                groups[category] = []
            groups[category].append(field)

        return groups

    def group_methods_by_category(
        self,
        methods: list[ast.FunctionDef],
    ) -> dict[str, list]:
        """Group methods by their category based on name and decorators.

        Uses classify_method() to determine each method's category, then
        groups them into a dictionary.

        Args:
            methods: List of AST FunctionDef nodes

        Returns:
            dict[str, list]: Dictionary mapping category names to lists of methods
        """
        groups = {}

        for method in methods:
            category = self.classify_method(method)
            # Add to appropriate group
            if category not in groups:
                groups[category] = []
            groups[category].append(method)

        return groups

    # ============================================================
    # SORTING FUNCTIONS
    # ============================================================

    def sort_imports(
        self,
        imports: list[str],
    ) -> list[str]:
        """Sort import statements using isort with Odoo conventions.

        Uses isort to organize imports into proper groups with Odoo-specific
        sections (stdlib, third-party, odoo, odoo.addons, relative).

        Args:
            imports: List of import statement strings

        Returns:
            list[str]: Sorted imports with proper grouping and spacing
        """
        if not imports:
            return []

        # Join imports into a single string
        import_str = "\n".join(imports)

        # Use isort to sort with configuration from config
        sorted_import_str = isort.code(
            import_str, **self.config.ordering.get_isort_config()
        )

        # Split back into lines
        return sorted_import_str.split("\n") if sorted_import_str else []

    def sort_model_attributes(
        self,
        attributes: list[str],
        order: list[str],
    ) -> list[str]:
        """Sort Odoo model attributes according to conventions.

        Orders model meta-attributes like _name, _inherit, _description
        in the conventional order used in Odoo models.

        Args:
            attributes: List of attribute assignment strings (e.g., '_name = "model.name"')
            order: Ordered list of attribute names defining sort priority
                (e.g., ['_name', '_inherit', '_description'])

        Returns:
            list[str]: Attributes sorted by the defined order.
                    Unknown attributes get lowest priority.
        """

        def get_attr_priority(attr: str) -> tuple[int, str]:
            # Extract attribute name
            attr_name = attr.split("=")[0].strip()

            try:
                priority = order.index(attr_name)
            except ValueError:
                priority = 99

            return (priority, attr_name)

        return sorted(attributes, key=get_attr_priority)

    def sort_topological(
        self,
        graph: dict[str, list[str]],
    ) -> list[str]:
        """Perform topological sort on a dependency graph.

        Implements Kahn's algorithm for topological sorting, which ensures
        that dependencies come before their dependents. Handles cycles
        gracefully by adding remaining nodes at the end.

        Args:
            graph: Dictionary mapping node names to lists of their dependencies.
                For example: {'A': ['B', 'C'], 'B': ['C']} means A depends on B and C.

        Returns:
            list[str]: Nodes in topologically sorted order. Nodes with no dependencies
                    come first, followed by nodes whose dependencies have been satisfied.
                    Provides stable sorting by sorting the queue at each step.
        """
        # Calculate in-degree for each node
        in_degree = {node: 0 for node in graph}
        for deps in graph.values():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1

        # Queue for nodes with no dependencies
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Sort queue for stable ordering
            queue.sort()
            node = queue.pop(0)
            result.append(node)

            # Reduce in-degree for dependent nodes
            for dep in graph.get(node, []):
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)

        # Add any remaining nodes (cycles or disconnected)
        for node in graph:
            if node not in result:
                result.append(node)

        return result

    def sort_field_attributes(
        self,
        node: ast.Assign,
    ) -> ast.Assign | None:
        """Reorder attributes in Odoo field declarations using field-type specific ordering.

        Each field type has its own optimal attribute order. For example:
        - Many2one: comodel_name comes first, then string, required, domain, etc.
        - Char: string comes first, then size, required, translate, etc.
        - Selection: selection comes first, then string, required, etc.

        Args:
            node: AST Assign node containing a field declaration

        Returns:
            ast.Assign: Node with reordered field attributes based on field type
        """
        # Detect the field type
        field_type = self.get_field_type(node)
        if not field_type:
            return None

        # Get the appropriate attribute order for this field type
        attribute_order = self.get_field_attribute_order(field_type)

        # Create mapping of attribute names to their positions
        order_map = {attr: i for i, attr in enumerate(attribute_order)}

        # Separate positional args and keyword args
        positional_args = []
        keyword_args = []

        for arg in node.value.args:
            positional_args.append(arg)

        for keyword in node.value.keywords:
            keyword_args.append(keyword)

        # Sort keyword arguments by field-type specific order
        def get_sort_key(keyword):
            if keyword.arg in order_map:
                return (0, order_map[keyword.arg])  # Known attributes in defined order
            else:
                # Unknown attributes go last, sorted alphabetically
                return (1, keyword.arg or "")

        sorted_keywords = sorted(keyword_args, key=get_sort_key)

        # Rebuild the Call node with sorted arguments
        new_call = ast.Call(
            func=node.value.func, args=positional_args, keywords=sorted_keywords
        )

        # Create new Assign node with the reordered call
        new_node = ast.Assign(
            targets=node.targets,
            value=new_call,
            type_comment=getattr(node, "type_comment", None),
        )

        # Copy location info to preserve formatting
        ast.copy_location(new_node, node)
        ast.copy_location(new_call, node.value)

        return new_node

    def sort_methods_with_dependencies(
        self,
        methods: list[dict[str, Any]],
        dependencies: dict[str, list[str]],
    ) -> list[dict[str, Any]]:
        """Sort methods considering their dependency relationships.

        Uses topological sorting to ensure methods that depend on others
        come after their dependencies. Useful for compute methods that
        call other compute methods.

        Args:
            methods: List of method dictionaries, each containing:
                    - 'name': Method name (must match keys in dependencies)
            dependencies: Dictionary mapping method names to lists of methods
                        they depend on

        Returns:
            list[dict[str, Any]]: Methods sorted topologically by dependencies.
                                Methods not in dependency graph are added at the end.
        """
        # Get topological order
        sorted_names = self.sort_topological(dependencies)

        # Create method lookup
        method_lookup = {m.get("name", ""): m for m in methods}

        # Build sorted list
        result = []
        for name in sorted_names:
            if name in method_lookup:
                result.append(method_lookup[name])

        # Add any methods not in dependencies
        for method in methods:
            if method not in result:
                result.append(method)

        return result

    # ============================================================
    # HELPERS
    # ============================================================

    def add_method_classification_rule(
        self,
        rule: ClassificationRuleMethod,
    ):
        """
        Add a custom method classification rule.
        Allows users to extend classification without modifying code.

        Args:
            rule: ClassificationRuleMethod to add
        """
        self._method_rules.append(rule)
        self._method_rules.sort(key=lambda r: r.priority)

    def add_field_classification_rule(
        self,
        rule: ClassificationRuleField,
    ):
        """
        Add a custom field classification rule.
        Allows users to extend field classification without modifying code.

        Args:
            rule: ClassificationRuleField to add
        """
        self._field_rules.append(rule)
        self._field_rules.sort(key=lambda r: r.priority)

    @staticmethod
    def get_decorator_name(
        decorator: ast.expr,
    ) -> str | None:
        """Extract the name from a decorator node.

        Handles various decorator forms: @name, @module.name, @name(...)

        Args:
            decorator: AST decorator expression

        Returns:
            str | None: Decorator name or None if not extractable
        """
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        return None

    def get_field_attribute_order(
        self,
        field_type: str,
    ) -> list[str]:
        """Get the optimal attribute order for a specific field type.

        Args:
            field_type: The Odoo field type (e.g., 'Char', 'Many2one')

        Returns:
            list[str]: Ordered list of attribute names for this field type
        """
        # Check if we have specific ordering for this field type
        if field_type in FIELD_TYPE_ATTRIBUTES:
            return FIELD_TYPE_ATTRIBUTES[field_type]

        # Fall back to generic ordering
        return FIELD_ATTRIBUTE_GENERIC

    def get_field_info(
        self,
        node: ast.Assign | ast.AnnAssign,
    ) -> dict[str, Any]:
        """
        Extract field information from an AST node.

        Args:
            node: AST node representing a field assignment

        Returns:
            Dictionary with field_name, field_type, is_computed, is_related
        """
        info = {
            "field_name": None,
            "field_type": None,
            "is_computed": False,
            "is_related": False,
            "related_field_base": None,
        }

        info["field_name"] = self.get_node_name(node)

        if isinstance(node, ast.Assign):
            info["field_type"] = self.get_field_type(node)
            # Get field attributes
            if node.value and isinstance(node.value, ast.Call):
                # Check for special attributes
                for keyword in node.value.keywords:
                    if keyword.arg == "compute":
                        info["is_computed"] = True
                    if keyword.arg == "related":
                        info["is_related"] = True

                        related_path = None
                        if isinstance(keyword.value, ast.Constant):
                            related_path = keyword.value.value
                        # Extract the base field (first part before '.')
                        if related_path and "." in related_path:
                            info["related_field_base"] = related_path.split(".")[0]
                        elif related_path:
                            info["related_field_base"] = related_path

        return info

    def get_field_type(
        self,
        node: ast.Assign,
    ) -> str | None:
        """Detect the Odoo field type from an AST node.

        Args:
            node: AST Assign node containing a field declaration

        Returns:
            str: Field type name (e.g., 'Char', 'Many2one') or None if not a field
        """
        if not isinstance(node.value, ast.Call):
            return None

        if not (
            isinstance(node.value.func, ast.Attribute)
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == "fields"
        ):
            return None

        # Extract field type from fields.FieldType
        return node.value.func.attr

    def get_line_range(
        self,
        node: ast.AST,
    ) -> tuple[int, int]:
        """Get the line range for an AST node.

        Args:
            node: AST node to get line range for

        Returns:
            tuple[int, int]: (start_line, end_line) or (0, 0) if not available
        """
        if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
            return (node.lineno, node.end_lineno or node.lineno)
        elif hasattr(node, "lineno"):
            return (node.lineno, node.lineno)
        return (0, 0)

    @staticmethod
    def get_node_name(
        node: ast.AST,
    ) -> str | None:
        """Extract the identifying name from various AST node types.

        Handles different node types:
        - Nodes with 'name' attribute (ClassDef, FunctionDef)
        - Assignment nodes (extracts target names)
        - Annotated assignments

        Args:
            node: AST node to get name from

        Returns:
            str | None: The node's name or None if not applicable
        """
        if hasattr(node, "name"):
            return node.name
        if isinstance(node, ast.Assign):
            targets = []
            for target in node.targets:
                if isinstance(target, ast.Name):
                    targets.append(target.id)
                elif isinstance(target, ast.Tuple):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            targets.append(elt.id)
            return ", ".join(targets) if targets else None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            return node.target.id
        return None

    def is_odoo_field(
        self,
        node: ast.Assign,
    ) -> bool:
        """Check if an assignment node is an Odoo field declaration.

        Args:
            node: AST Assign node to check

        Returns:
            bool: True if this is an Odoo field declaration
        """
        if not isinstance(node, ast.Assign):
            return False
        if not isinstance(node.value, ast.Call):
            return False
        if not (
            isinstance(node.value.func, ast.Attribute)
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == "fields"
        ):
            return False
        return True

    def _is_property(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> bool:
        """Check if a function is decorated as a property.

        Args:
            node: Function definition to check

        Returns:
            bool: True if the function has a property decorator
        """
        for decorator in node.decorator_list:
            decorator_name = self.get_decorator_name(decorator)
            if decorator_name and "property" in decorator_name:
                return True
        return False

    # ============================================================
    # REORGANIZER
    # ============================================================

    def unparse_node(
        self,
        node: ast.AST,
        indent: str = "",
        prefix: str = "",
    ) -> str:
        """Convert an AST node back to Python source code.

        Args:
            node: AST node to unparse
            indent: String to prepend to each line for indentation
            prefix: String to prepend to the result (e.g., '@' for decorators)

        Returns:
            str: Python source code representation of the node, with indentation
                and prefix applied. Returns placeholder comment if unparsing fails.
        """
        try:
            unparsed = ast.unparse(node)
            if prefix:
                unparsed = prefix + unparsed.lstrip("@")
            if indent:
                # Add indent to each line
                lines = unparsed.split("\n")
                unparsed = "\n".join(indent + line if line else line for line in lines)
            return unparsed
        except Exception as e:
            logger.debug(f"Failed to unparse node: {e}")
            return f"{indent}# [unparseable node]"

    def reorganize_node(
        self,
        node: ast.AST | str = None,
        level: str = "module",
    ) -> str | list[str]:
        """
        Reorganize any AST node (module or class) or content string according to Odoo conventions.

        Args:
            node: AST node to reorganize (Module or ClassDef) or string content
            level: "module", "class", or "field_attributes" to determine organization rules

        Returns:
            str: Reorganized source code (for module level or field_attributes)
            list[str]: Reorganized lines (for class level, to be integrated)
        """
        # Handle field_attributes level
        if level == "field_attributes":
            if isinstance(node, str):
                content = node
            else:
                content = self.unparse_node(node)

            # Parse the content
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return content

            # Create a transformer to reorder field attributes
            class FieldAttributeReorderer(ast.NodeTransformer):
                def __init__(self, ordering):
                    self.ordering = ordering

                def visit_Assign(self, node):
                    if self.ordering.is_odoo_field(node):
                        reordered = self.ordering.sort_field_attributes(node)
                        if reordered:
                            return reordered
                    return node

            # Apply the transformer
            transformer = FieldAttributeReorderer(self)
            tree = transformer.visit(tree)

            # Return the unparsed tree
            return self.unparse_node(tree)

        # Handle string content for module level
        if isinstance(node, str):
            # Parse the string content
            try:
                parsed_tree = ast.parse(node)
                # Call recursively with the parsed tree
                return self.reorganize_node(parsed_tree, level=level)
            except SyntaxError as e:
                logger.error(f"Failed to parse content: {e}")
                return node

        result_lines = []

        # Extract elements based on node type
        if isinstance(node, ast.Module):
            elements = self.extract_elements(node)
            indent = ""
            return_as_string = True
        elif isinstance(node, ast.ClassDef):
            elements = self.extract_class_elements(node)
            indent = "    "
            return_as_string = False
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")

        # 1. Docstring (both module and class have docstrings)
        if ast.get_docstring(node) and node.body:
            first_node = node.body[0]
            if isinstance(first_node, ast.Expr) and isinstance(
                first_node.value, ast.Constant
            ):
                result_lines.append(self.unparse_node(first_node, indent=indent))
                result_lines.append("")

        # 2. Module-specific: Imports and constants
        if level == "module":
            if elements.get("imports"):
                import_strs = [self.unparse_node(imp) for imp in elements["imports"]]
                sorted_imports = self.sort_imports(import_strs)
                result_lines.extend(sorted_imports)
                result_lines.append("")

            if elements.get("module_vars"):
                for var in elements["module_vars"]:
                    result_lines.append(self.unparse_node(var))
                result_lines.append("")

        # 3. Class-specific: Meta attributes and properties
        if level == "class":
            # Model attributes (_name, _description, etc.)
            if elements.get("model_attrs"):
                # Sort model attributes in Odoo convention order

                def get_attr_priority(attr):
                    if isinstance(attr, ast.Assign) and attr.targets:
                        name = getattr(attr.targets[0], "id", "")
                        try:
                            return MODEL_ATTRIBUTES.index(name)
                        except ValueError:
                            return len(MODEL_ATTRIBUTES)
                    return len(MODEL_ATTRIBUTES)

                sorted_attrs = sorted(elements["model_attrs"], key=get_attr_priority)
                for attr in sorted_attrs:
                    result_lines.append(self.unparse_node(attr, indent=indent))
                result_lines.append("")

            # Properties
            if elements.get("properties"):
                for prop in elements["properties"]:
                    result_lines.append(self.unparse_node(prop, indent=indent))
                result_lines.append("")

        # 4. Fields (class level only)
        if level == "class" and elements.get("fields"):
            if self.config.ordering.add_section_headers:
                result_lines.extend(self.format_section_header("FIELDS"))

            # Handle both dict (already grouped) and list formats
            if isinstance(elements["fields"], dict):
                for category, fields in elements["fields"].items():
                    for field in fields:
                        result_lines.append(self.unparse_node(field, indent=indent))
            else:
                for field in elements["fields"]:
                    result_lines.append(self.unparse_node(field, indent=indent))
            result_lines.append("")

        # 5. Methods (both module functions and class methods)
        method_key = "functions" if level == "module" else "methods"
        if elements.get(method_key):
            methods = elements[method_key]

            # Handle both dict (already grouped) and list formats
            if not isinstance(methods, dict):
                methods = (
                    self.group_methods_by_category(methods)
                    if level == "class"
                    else {"functions": methods}  # Module functions don't need grouping
                )

            # Output in order
            if level == "module":
                # For module level, just output all functions
                if "functions" in methods:
                    for function in methods["functions"]:
                        result_lines.append(self.unparse_node(function, indent=indent))
                        result_lines.append("")
            else:
                # For class level, output by category
                for category in METHOD_ORDER:
                    if category in methods:
                        if self.config.ordering.add_section_headers:
                            result_lines.extend(
                                self.format_section_header(f"{category} METHODS")
                            )

                        for method in methods[category]:
                            result_lines.append(
                                self.unparse_node(method, indent=indent)
                            )
                            result_lines.append("")

        # 6. Classes (module level only)
        if level == "module" and elements.get("classes"):
            for class_node in elements["classes"]:
                # Build class definition line
                class_def_parts = []

                # Add decorators if any
                for decorator in class_node.decorator_list:
                    class_def_parts.append(self.unparse_node(decorator))

                # Build class line
                class_line = f"class {class_node.name}"
                if class_node.bases:
                    bases = ", ".join(
                        self.unparse_node(base) for base in class_node.bases
                    )
                    class_line += f"({bases}):"
                else:
                    class_line += ":"

                class_def_parts.append(class_line)
                result_lines.extend(class_def_parts)

                # Recursively reorganize class body
                class_lines = self.reorganize_node(class_node, level="class")
                result_lines.extend(class_lines)
                result_lines.append("")

        # Return based on level
        if return_as_string:
            # Return as string for module level
            return "\n".join(result_lines)
        else:
            return result_lines

    def reorganize_xml(
        self,
        file_path: Path,
        level: str = "attributes",
    ) -> str:
        """Main entry point for XML reorganization.

        Args:
            file_path: Path to XML file
            level: "attributes" (just reorder attrs) or "structure" (full reorganization)

        Returns:
            Reorganized XML content as string
        """
        tree = ET.parse(file_path)
        root = tree.getroot()

        if level == "structure":
            # Full structural reorganization
            view_type = self.detect_view_type(root)

            if view_type == "form":
                root = self.reorganize_form_view(root)
            elif view_type == "tree":
                root = self.reorganize_tree_view(root)
            elif view_type == "search":
                root = self.reorganize_search_view(root)
            elif view_type == "kanban":
                root = self.reorganize_kanban_view(root)
            else:
                # Unknown type - just reorder attributes
                self.reorder_element_attributes(root)
        else:
            # Attributes only
            self.reorder_element_attributes(root)

        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def reorder_element_attributes(
        self,
        element: ET.Element,
    ) -> None:
        """Recursively reorder attributes in XML element and its children.

        Args:
            element: XML element to process (modified in-place)
        """
        # Get the attribute order for this element type
        tag_name = element.tag
        attribute_order = self.attribute_orders.get(
            tag_name, self.attribute_orders["_default"]
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

        # Process children recursively
        for child in element:
            self.reorder_element_attributes(child)

    def detect_view_type(
        self,
        root: ET.Element,
    ) -> str | None:
        """Detect the type of Odoo view from XML root.

        Args:
            root: Root element of XML tree

        Returns:
            View type string ('form', 'tree', 'search', 'kanban', etc.) or None
        """
        # Check for explicit view type in record/field structure
        for record in root.findall(".//record"):
            for field in record.findall("field[@name='arch']"):
                # The first child of arch field is usually the view type
                if len(field) > 0:
                    return field[0].tag

        # Check for direct view elements
        if root.tag in [
            "form",
            "tree",
            "search",
            "kanban",
            "calendar",
            "graph",
            "pivot",
            "qweb",
        ]:
            return root.tag

        # Check first child
        if len(root) > 0 and root[0].tag in ["form", "tree", "search", "kanban"]:
            return root[0].tag

        return None

    def reorganize_form_view(
        self,
        root: ET.Element,
    ) -> ET.Element:
        """Reorganize form view according to Odoo conventions.

        Standard form view structure:
        1. Header (buttons, statusbar)
        2. Sheet
           - Title elements (h1, h2, div with classes)
           - Main content groups
           - Notebook with pages
        3. Chatter (mail.chatter widget)

        Args:
            root: Root element of form view

        Returns:
            Reorganized form view element
        """
        new_root = ET.Element(root.tag, root.attrib)

        # Extract and categorize elements
        elements = self._categorize_form_elements(root)

        # 1. Add header if exists
        if elements["header"]:
            for elem in elements["header"]:
                new_root.append(elem)

        # 2. Add sheet content
        if elements["sheet"] or elements["groups"] or elements["notebook"]:
            sheet = ET.SubElement(new_root, "sheet")

            # Add title elements
            for elem in elements["titles"]:
                sheet.append(elem)

            # Add main groups
            for elem in elements["groups"]:
                sheet.append(elem)

            # Add notebook
            for elem in elements["notebook"]:
                sheet.append(elem)

            # Add other sheet elements
            for elem in elements["sheet"]:
                if elem.tag not in ["header", "div", "group", "notebook"]:
                    sheet.append(elem)

        # 3. Add chatter/footer elements
        for elem in elements["chatter"]:
            new_root.append(elem)

        # Apply attribute reordering recursively
        self.reorder_element_attributes(new_root)

        return new_root

    def reorganize_tree_view(
        self,
        root: ET.Element,
    ) -> ET.Element:
        """Reorganize tree view according to conventions.

        Tree view element order:
        1. Control elements
        2. Button columns
        3. Regular field columns
        4. Widget field columns

        Args:
            root: Root element of tree view

        Returns:
            Reorganized tree view element
        """
        new_root = ET.Element(root.tag, root.attrib)

        # Categorize elements
        buttons = []
        fields = []
        widget_fields = []
        control_elements = []

        for elem in root:
            if elem.tag == "button":
                buttons.append(elem)
            elif elem.tag == "field":
                if elem.get("widget"):
                    widget_fields.append(elem)
                else:
                    fields.append(elem)
            elif elem.tag == "control":
                control_elements.append(elem)
            else:
                control_elements.append(elem)

        # Add in order: control elements, buttons, regular fields, widget fields
        for elem in control_elements + buttons + fields + widget_fields:
            new_root.append(elem)

        # Apply attribute reordering
        self.reorder_element_attributes(new_root)

        return new_root

    def reorganize_search_view(
        self,
        root: ET.Element,
    ) -> ET.Element:
        """Reorganize search view according to conventions.

        Search view element order:
        1. Search fields
        2. Filter elements
        3. Separator elements
        4. Group by filters

        Args:
            root: Root element of search view

        Returns:
            Reorganized search view element
        """
        new_root = ET.Element(root.tag, root.attrib)

        # Categorize elements
        fields = []
        filters = []
        separators = []
        groups = []

        for elem in root:
            if elem.tag == "field":
                fields.append(elem)
            elif elem.tag == "filter":
                # Check if it's a group-by filter
                if elem.get("context") and "group_by" in elem.get("context", ""):
                    groups.append(elem)
                else:
                    filters.append(elem)
            elif elem.tag == "separator":
                separators.append(elem)
            elif elem.tag == "group":
                groups.append(elem)

        # Add in order: fields, filters, separator, groups
        for elem in fields + filters + separators + groups:
            new_root.append(elem)

        # Apply attribute reordering
        self.reorder_element_attributes(new_root)

        return new_root

    def reorganize_kanban_view(
        self,
        root: ET.Element,
    ) -> ET.Element:
        """Reorganize kanban view according to conventions.

        Kanban view element order:
        1. Progressbar
        2. Field declarations
        3. Control elements
        4. Templates

        Args:
            root: Root element of kanban view

        Returns:
            Reorganized kanban view element
        """
        new_root = ET.Element(root.tag, root.attrib)

        # Categorize elements
        fields = []
        templates = []
        progressbar = []
        control = []

        for elem in root:
            if elem.tag == "field":
                fields.append(elem)
            elif elem.tag == "templates":
                templates.append(elem)
            elif elem.tag == "progressbar":
                progressbar.append(elem)
            elif elem.tag == "control":
                control.append(elem)
            else:
                control.append(elem)

        # Add in order: progressbar, fields, control elements, templates
        for elem in progressbar + fields + control + templates:
            new_root.append(elem)

        # Apply attribute reordering
        self.reorder_element_attributes(new_root)

        return new_root

    def _categorize_form_elements(
        self,
        root: ET.Element,
    ) -> dict[str, list]:
        """Categorize form view elements by type.

        Args:
            root: Root element of form view

        Returns:
            Dictionary with categorized elements
        """
        elements = {
            "header": [],
            "titles": [],
            "sheet": [],
            "groups": [],
            "notebook": [],
            "chatter": [],
        }

        for elem in root:
            if elem.tag == "header":
                elements["header"].append(elem)
            elif elem.tag == "sheet":
                # Process sheet children
                for child in elem:
                    if child.tag in ["h1", "h2", "h3"]:
                        elements["titles"].append(child)
                    elif child.tag == "div" and "oe_title" in child.get("class", ""):
                        elements["titles"].append(child)
                    elif child.tag == "group":
                        elements["groups"].append(child)
                    elif child.tag == "notebook":
                        elements["notebook"].append(child)
                    else:
                        elements["sheet"].append(child)
            elif elem.tag == "div" and "oe_chatter" in elem.get("class", ""):
                elements["chatter"].append(elem)
            elif elem.tag == "group":
                elements["groups"].append(elem)
            elif elem.tag == "notebook":
                elements["notebook"].append(elem)
            elif elem.tag in ["h1", "h2", "h3"]:
                elements["titles"].append(elem)
            else:
                # Check if it's a chatter-related element
                if elem.tag == "field" and elem.get("name") in [
                    "message_follower_ids",
                    "activity_ids",
                    "message_ids",
                ]:
                    elements["chatter"].append(elem)
                else:
                    elements["sheet"].append(elem)

        return elements

    # ============================================================
    # FORMATTING UTILITIES
    # ============================================================

    def format_section_header(
        self,
        title: str,
        separator: str = "=",
        length: int = 80,
    ) -> list[str]:
        """Format a prominent section header with separator lines.

        Creates a three-line header comment block for visually separating
        major sections in the code (e.g., FIELDS, CRUD METHODS).

        Args:
            title: Section title to display
            separator: Character to use for separator lines (default '=')
            length: Total length of separator lines (default 77)

        Returns:
            list[str]: Four lines - separator, title, separator, blank line

        Example:
            >>> format_section_header("FIELDS")
            ['    # =====================================================',
             '    # FIELDS',
             '    # =====================================================',
             '']
        """
        sep_line = separator * length
        return [
            f"    # {sep_line}",
            f"    # {title}",
            f"    # {sep_line}",
            "",
        ]

    # ============================================================
    # AST PARSER COMPATIBILITY
    # ============================================================

    def extract_value(
        self,
        node: ast.AST,
    ) -> Any:
        """Extract value from an AST node (more comprehensive than inline logic).

        Args:
            node: AST node containing a value

        Returns:
            Extracted Python value
        """
        # ast.Constant handles all constant values since Python 3.8
        # (replaces ast.Str, ast.Num, ast.NameConstant, ast.Bytes, ast.Ellipsis)
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.List):
            return [self.extract_value(elt) for elt in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self.extract_value(elt) for elt in node.elts)
        elif isinstance(node, ast.Dict):
            return {
                self.extract_value(k): self.extract_value(v)
                for k, v in zip(node.keys, node.values)
                if k is not None
            }
        elif isinstance(node, ast.Attribute):
            return f"{self.get_node_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            # For function calls, return a representation
            func_name = self.get_node_name(node.func)
            return f"{func_name}(...)"
        elif isinstance(node, ast.Lambda):
            return "lambda"
        elif isinstance(node, ast.BinOp):
            # For binary operations
            left = self.extract_value(node.left)
            right = self.extract_value(node.right)
            return f"{left} op {right}"
        else:
            return None

    def get_inventory(
        self,
        content: str,
        filename: str = "<string>",
    ) -> dict[str, Any]:
        """Get inventory of fields and methods (compatible with old ast_parser).

        This method provides backward compatibility with the ASTParser.get_inventory()
        method that was used by detect.py for analyzing changes between commits.

        Args:
            content: Python source code
            filename: Optional filename for error reporting

        Returns:
            Dictionary with 'fields', 'methods', and 'classes' lists
        """
        inventory = {"fields": [], "methods": [], "classes": []}

        try:
            tree = ast.parse(content, filename)
        except SyntaxError as e:
            logger.error(f"Syntax error in {filename}: {e}")
            return inventory

        # Extract all class definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Get class info
                class_info = {
                    "name": node.name,
                    "model": None,
                    "inherit": None,
                }

                # Extract class elements
                elements = self.extract_class_elements(node)

                # Find model attributes
                for attr_node in elements.get("model_attrs", []):
                    if isinstance(attr_node, ast.Assign):
                        for target in attr_node.targets:
                            if isinstance(target, ast.Name):
                                attr_name = target.id
                                attr_value = self.extract_value(attr_node.value)

                                if attr_name == "_name":
                                    class_info["model"] = attr_value
                                elif attr_name == "_inherit":
                                    if isinstance(attr_value, list):
                                        class_info["inherit"] = attr_value
                                    else:
                                        class_info["inherit"] = [attr_value]

                inventory["classes"].append(class_info)

                # Extract fields - handle both dict (grouped) and list formats
                fields_data = elements.get("fields", [])
                if isinstance(fields_data, dict):
                    # Fields are grouped by category
                    for category, field_list in fields_data.items():
                        for field_node in field_list:
                            if isinstance(field_node, ast.Assign):
                                field_info = self.get_field_info(field_node)
                                if field_info and field_info.get("field_name"):
                                    # Extract attributes from the field call
                                    attrs = {}
                                    if hasattr(field_node.value, "keywords"):
                                        for kw in field_node.value.keywords:
                                            if kw.arg:
                                                attrs[kw.arg] = self.extract_value(
                                                    kw.value
                                                )

                                    inventory["fields"].append(
                                        {
                                            "name": field_info["field_name"],
                                            "type": field_info.get("field_type", ""),
                                            "class": node.name,
                                            "line": field_node.lineno,
                                            "attributes": attrs,
                                        }
                                    )
                else:
                    # Fields are a flat list
                    for field_node in fields_data:
                        if isinstance(field_node, ast.Assign):
                            field_info = self.get_field_info(field_node)
                            if field_info and field_info.get("field_name"):
                                # Extract attributes from the field call
                                attrs = {}
                                if hasattr(field_node.value, "keywords"):
                                    for kw in field_node.value.keywords:
                                        if kw.arg:
                                            attrs[kw.arg] = self.extract_value(kw.value)

                                inventory["fields"].append(
                                    {
                                        "name": field_info["field_name"],
                                        "type": field_info.get("field_type", ""),
                                        "class": node.name,
                                        "line": field_node.lineno,
                                        "attributes": attrs,
                                    }
                                )

                # Extract methods
                for category, methods in elements.get("methods", {}).items():
                    for method_node in methods:
                        if isinstance(method_node, ast.FunctionDef):
                            # Determine method type from decorators and category
                            method_type = None
                            decorators = self.extract_decorators(method_node)

                            # Map categories to method types
                            category_map = {
                                "COMPUTE": "compute",
                                "CONSTRAINT": "constraint",
                                "ONCHANGE": "onchange",
                                "CRUD": "crud",
                                "API_MODEL": "model",
                            }

                            if category in category_map:
                                method_type = category_map[category]

                            inventory["methods"].append(
                                {
                                    "name": method_node.name,
                                    "class": node.name,
                                    "line": method_node.lineno,
                                    "type": method_type,
                                    "decorators": decorators,
                                }
                            )

        return inventory
