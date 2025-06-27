#!/usr/bin/env python3
"""
Odoo Source Code Reorganizer with Black Formatting

This tool reorganizes and formats Odoo Python source files for consistency in styling and semantics.
It follows Odoo development conventions and uses Black for code formatting.

Features:
- Reorganizes imports by category (stdlib, third-party, Odoo, relative)
- Sorts class methods following Odoo conventions
- Adds section headers (# FIELDS, # COMPUTE METHODS, etc.) for better code navigation
- Splits multiple classes into separate files for better organization
- Outputs all generated files to generated_files directory
- Preserves original file extensions
- Handles async functions and complex decorators
- Provides comprehensive error handling and logging
- Supports dry-run mode and backup creation
- Validates files before processing

Usage:
    python odoo_reorder.py file.py                    # Process single file
    python odoo_reorder.py directory/                 # Process directory
    python odoo_reorder.py directory/ --recursive     # Process recursively
    python odoo_reorder.py file.py --dry-run          # Preview changes
    python odoo_reorder.py file.py --check            # Check if needs formatting
    
Author: Agromarin Tools
Version: 1.1.0
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import argparse
import logging

try:
    import black
except ImportError:
    print("Error: Black is not installed. Please install it with: pip install black")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class OdooCodeReorganizer:
    """
    Reorganizes Odoo source code files for consistency.
    
    This class handles the reorganization of Python files following Odoo conventions:
    - Import grouping and sorting
    - Class method organization
    - Code formatting with Black
    - Error handling and validation
    """

    # Odoo import groups order
    IMPORT_GROUPS = {
        "python_stdlib": 0,
        "third_party": 1,
        "odoo": 2,
        "odoo_addons": 3,
        "relative": 4,
    }

    # Common Odoo decorators for method ordering
    ODOO_DECORATORS = [
        "@api.model",
        "@api.multi",
        "@api.one",
        "@api.depends",
        "@api.constrains",
        "@api.onchange",
        "@api.returns",
    ]

    def __init__(self, preserve_comments: bool = True, line_length: int = 88, add_section_headers: bool = True, split_classes: bool = False, output_dir: str = "generated_files"):
        self.preserve_comments = preserve_comments
        self.line_length = line_length
        self.add_section_headers = add_section_headers
        self.split_classes = split_classes
        self.output_dir = output_dir
        self.black_mode = black.Mode(
            target_versions={black.TargetVersion.PY38},
            line_length=line_length,
            string_normalization=True,
            is_pyi=False,
        )
        
        # Cache for stdlib modules to improve performance
        self._stdlib_cache = set()
        self._load_stdlib_cache()
        
        # Ensure output directory exists
        self._ensure_output_dir()
        
        # Track if current file was split
        self._file_was_split = False
        
        # Section headers configuration
        self.section_headers = {
            "model_attributes": "FIELDS",
            "fields": "FIELDS", 
            "constraint": "CONSTRAINTS",
            "compute": "COMPUTE METHODS",
            "onchange": "ONCHANGE METHODS", 
            "crud": "CRUD METHODS",
            "action": "ACTIONS",
            "search": "SEARCH METHODS",
            "other": "PUBLIC METHODS",
            "private": "PRIVATE METHODS",
            "helper": "HELPERS"
        }
    
    def _ensure_output_dir(self):
        """Ensure output directory exists."""
        import os
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")

    def _load_stdlib_cache(self):
        """Load standard library modules into cache for performance."""
        self._stdlib_cache = {
            "abc", "argparse", "ast", "asyncio", "base64", "builtins", "collections", 
            "contextlib", "copy", "csv", "datetime", "decimal", "enum", "functools", 
            "gc", "glob", "hashlib", "html", "http", "importlib", "inspect", "io", 
            "itertools", "json", "logging", "math", "operator", "os", "pathlib", 
            "pickle", "platform", "pprint", "re", "random", "shutil", "signal", 
            "socket", "sqlite3", "string", "struct", "subprocess", "sys", "tempfile", 
            "threading", "time", "traceback", "types", "typing", "unittest", "urllib", 
            "uuid", "warnings", "weakref", "xml", "zipfile", "zlib"
        }

    def _extract_header(self, content: str) -> List[str]:
        """Extract file header (shebang, encoding, copyright)."""
        lines = content.split("\n")
        header = []

        for line in lines:
            if (
                line.startswith("#!")
                or line.startswith("# -*-")
                or "copyright" in line.lower()
                or "license" in line.lower()
            ):
                header.append(line)
            elif line.strip() and not line.startswith("#"):
                break

        return header

    def _extract_module_docstring(self, tree: ast.Module) -> str:
        """Extract module-level docstring."""
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            return ast.get_docstring(tree, clean=False)
        return ""

    def _extract_imports(self, tree: ast.Module) -> List[ast.stmt]:
        """Extract all import statements."""
        return [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]

    def _extract_classes(self, tree: ast.Module) -> List[ast.ClassDef]:
        """Extract all class definitions."""
        return [node for node in tree.body if isinstance(node, ast.ClassDef)]

    def _extract_functions(self, tree: ast.Module) -> List[ast.FunctionDef]:
        """Extract all function definitions (including async)."""
        return [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]

    def _extract_other_statements(self, tree: ast.Module) -> List[ast.stmt]:
        """Extract statements that are not imports, classes, or functions."""
        other = []
        skip_first = False

        # Check if first statement is docstring
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            skip_first = True

        for i, node in enumerate(tree.body):
            if skip_first and i == 0:
                continue
            if not isinstance(
                node, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                other.append(node)

        return other

    def _import_sort_key(self, import_node: ast.stmt) -> Tuple:
        """Generate sort key for import statements."""
        if isinstance(import_node, ast.Import):
            # Sort by module name
            return (0, import_node.names[0].name.lower())
        else:  # ImportFrom
            # Sort by module name, then by imported names
            module = import_node.module or ""
            names = sorted([alias.name for alias in import_node.names])
            return (1, module.lower(), tuple(names))

    def _classify_import(self, import_node: ast.stmt) -> str:
        """Classify import into groups."""
        if isinstance(import_node, ast.Import):
            module = import_node.names[0].name
        else:  # ImportFrom
            module = import_node.module or ""

        # Relative imports
        if isinstance(import_node, ast.ImportFrom) and import_node.level > 0:
            return "relative"

        # Odoo imports
        if module.startswith("odoo.addons") or module.startswith("openerp.addons"):
            return "odoo_addons"
        elif module.startswith(("odoo", "openerp")):
            return "odoo"

        # Python standard library (use cached set)
        base_module = module.split(".")[0]
        if base_module in self._stdlib_cache:
            return "python_stdlib"

        # Everything else is third party
        return "third_party"

    def _classify_method(self, method: ast.FunctionDef) -> str:
        """Classify method type based on decorators and naming."""
        # Get decorator names
        decorator_names = []
        for decorator in method.decorator_list:
            if isinstance(decorator, ast.Name):
                decorator_names.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorator_names.append(decorator.attr)
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    decorator_names.append(decorator.func.id)
                elif isinstance(decorator.func, ast.Attribute):
                    decorator_names.append(decorator.func.attr)

        # Check decorators
        if "depends" in decorator_names or method.name.startswith("_compute_"):
            return "compute"
        elif "constrains" in decorator_names or method.name.startswith("_check_"):
            return "constraint"
        elif "onchange" in decorator_names or method.name.startswith("_onchange_"):
            return "onchange"

        # Check method names
        if method.name in ["create", "write", "unlink", "read", "copy", "default_get"]:
            return "crud"
        elif method.name.startswith("action_"):
            return "action"
        elif method.name.startswith("_search_"):
            return "search"
        elif method.name.startswith("_check_"):
            return "constraint"  # _check_ methods are constraints
        elif method.name.startswith("_get_") or method.name.startswith("_filter_") or method.name.startswith("_update_"):
            return "helper"
        elif method.name.startswith("_") and method.name not in ["__init__"]:
            return "private"

        return "other"

    def _organize_imports(self, imports: List[ast.stmt]) -> Dict[str, List[ast.stmt]]:
        """Organize imports by groups."""
        grouped = {key: [] for key in self.IMPORT_GROUPS.keys()}

        for imp in imports:
            group = self._classify_import(imp)
            grouped[group].append(imp)

        # Sort within each group
        for group in grouped:
            grouped[group].sort(key=self._import_sort_key)

        return grouped

    def _reorganize_class_methods(self, cls: ast.ClassDef):
        """Reorganize methods within a class following Odoo conventions."""
        # Categorize methods
        model_attributes = []  # _name, _inherit, etc.
        fields = []
        compute_methods = []
        constraint_methods = []
        onchange_methods = []
        crud_methods = []
        action_methods = []
        search_methods = []
        helper_methods = []
        private_methods = []
        other_methods = []
        other_statements = []

        for node in cls.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_type = self._classify_method(node)
                if method_type == "compute":
                    compute_methods.append(node)
                elif method_type == "constraint":
                    constraint_methods.append(node)
                elif method_type == "onchange":
                    onchange_methods.append(node)
                elif method_type == "crud":
                    crud_methods.append(node)
                elif method_type == "action":
                    action_methods.append(node)
                elif method_type == "search":
                    search_methods.append(node)
                elif method_type == "helper":
                    helper_methods.append(node)
                elif method_type == "private":
                    private_methods.append(node)
                else:
                    other_methods.append(node)
            elif isinstance(node, ast.Assign):
                # Check if it's a model attribute, SQL constraint, or field
                if self._is_model_attribute(node):
                    model_attributes.append(node)
                elif self._is_sql_constraint(node):
                    constraint_methods.append(node)  # SQL constraints go in constraints section
                else:
                    fields.append(node)
            else:
                other_statements.append(node)

        # Separate SQL constraints from constraint methods
        sql_constraints = [c for c in constraint_methods if isinstance(c, ast.Assign)]
        constraint_methods_only = [c for c in constraint_methods if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef))]
        
        # Sort methods within categories
        compute_methods.sort(key=lambda m: m.name)
        constraint_methods_only.sort(key=lambda m: m.name)
        onchange_methods.sort(key=lambda m: m.name)
        action_methods.sort(key=lambda m: m.name)
        search_methods.sort(key=lambda m: m.name)
        helper_methods.sort(key=lambda m: m.name)
        private_methods.sort(key=lambda m: m.name)
        
        # Sort model attributes by priority order
        model_attributes.sort(key=self._get_model_attribute_priority)

        # Reorder class body following Odoo conventions with section headers
        new_body = []
        
        # Store categorized sections for header insertion during reconstruction
        sections = []
        
        # Model attributes go first WITHOUT a header
        if model_attributes:
            sections.append(("MODEL_ATTRIBUTES", model_attributes))
            
        # Fields get their own FIELDS section  
        if fields:
            sections.append(("FIELDS", fields))
            
        # Constraints section: SQL constraints first, then constraint methods
        if sql_constraints or constraint_methods_only:
            all_constraints = sql_constraints + constraint_methods_only
            sections.append(("CONSTRAINTS", all_constraints))
        if crud_methods:
            sections.append(("CRUD METHODS", crud_methods))
        if compute_methods:
            sections.append(("COMPUTE METHODS", compute_methods))
        if onchange_methods:
            sections.append(("ONCHANGE METHODS", onchange_methods))
        if search_methods:
            sections.append(("SEARCH METHODS", search_methods))
        if action_methods:
            sections.append(("ACTIONS", action_methods))
        if other_methods:
            sections.append(("PUBLIC METHODS", other_methods))
        if helper_methods:
            sections.append(("HELPERS", helper_methods))
        if private_methods:
            sections.append(("PRIVATE METHODS", private_methods))
            
        # Store sections info for later header insertion
        cls._odoo_sections = sections
        cls._odoo_other_statements = other_statements
        
        # Rebuild class body without headers for now (headers added in reconstruction)
        cls.body = (
            model_attributes 
            + fields 
            + sql_constraints
            + constraint_methods_only 
            + crud_methods 
            + compute_methods 
            + onchange_methods 
            + search_methods 
            + action_methods 
            + other_methods 
            + helper_methods 
            + private_methods 
            + other_statements
        )

    def _create_section_header(self, section_name: str) -> str:
        """Create a section header with dashes like Odoo convention."""
        divider = "    # " + "-" * 60
        header = f"    # {section_name}"
        
        return f"\n{divider}\n{header}\n{divider}\n"

    def _generate_class_with_headers(self, cls: ast.ClassDef) -> str:
        """Generate class code with section headers."""
        # Start with class definition
        class_lines = [f"class {cls.name}"]
        
        # Add base classes
        if cls.bases:
            base_names = [ast.unparse(base) for base in cls.bases]
            class_lines[0] += f"({', '.join(base_names)})"
        
        class_lines[0] += ":"
        
        # Add docstring if exists
        if cls.body and isinstance(cls.body[0], ast.Expr) and isinstance(cls.body[0].value, ast.Constant):
            if isinstance(cls.body[0].value.value, str):
                docstring_line = ast.unparse(cls.body[0])
                class_lines.append(f"    {docstring_line}")
                class_lines.append("")
        
        # Add sections with headers
        if hasattr(cls, '_odoo_sections'):
            for section_name, section_items in cls._odoo_sections:
                if section_items:
                    # Model attributes don't get a header section
                    if section_name == "MODEL_ATTRIBUTES":
                        # Add section items without header
                        for item in section_items:
                            item_code = ast.unparse(item)
                            # Indent each line properly
                            for line in item_code.split('\n'):
                                if line.strip():
                                    class_lines.append(f"    {line}")
                                else:
                                    class_lines.append("")
                        class_lines.append("")  # Blank line after model attributes
                    else:
                        # Add section header for all other sections
                        divider = "    # " + "-" * 60
                        header = f"    # {section_name}"
                        class_lines.append(divider)
                        class_lines.append(header)
                        class_lines.append(divider)
                        class_lines.append("")
                        
                        # Add section items
                        for item in section_items:
                            item_code = ast.unparse(item)
                            # Indent each line properly
                            for line in item_code.split('\n'):
                                if line.strip():
                                    class_lines.append(f"    {line}")
                                else:
                                    class_lines.append("")
                        
                        class_lines.append("")  # Blank line after section
        
        # Add other statements
        if hasattr(cls, '_odoo_other_statements') and cls._odoo_other_statements:
            for stmt in cls._odoo_other_statements:
                stmt_code = ast.unparse(stmt)
                for line in stmt_code.split('\n'):
                    if line.strip():
                        class_lines.append(f"    {line}")
                    else:
                        class_lines.append("")
        
        # Remove trailing empty lines
        while class_lines and not class_lines[-1].strip():
            class_lines.pop()
            
        return '\n'.join(class_lines)

    def _organize_classes(
        self, classes: List[ast.ClassDef], original_content: str
    ) -> List[ast.ClassDef]:
        """Organize classes, preserving Odoo conventions."""
        # Sort classes: models first, then wizards, then others
        model_classes = []
        wizard_classes = []
        other_classes = []

        for cls in classes:
            if self._is_odoo_model(cls):
                model_classes.append(cls)
            elif self._is_odoo_wizard(cls):
                wizard_classes.append(cls)
            else:
                other_classes.append(cls)

        # Reorganize methods within each class
        for cls in classes:
            self._reorganize_class_methods(cls)

        return model_classes + wizard_classes + other_classes

    def _organize_functions(
        self, functions: List[ast.FunctionDef]
    ) -> List[ast.FunctionDef]:
        """Organize module-level functions."""
        # Sort: public functions first, then private
        public = [f for f in functions if not f.name.startswith("_")]
        private = [f for f in functions if f.name.startswith("_")]

        public.sort(key=lambda f: f.name.lower())
        private.sort(key=lambda f: f.name.lower())

        return public + private

    def _reconstruct_file(
        self,
        header: List[str],
        docstring: str,
        imports: Dict[str, List[ast.stmt]],
        functions: List[ast.FunctionDef],
        classes: List[ast.ClassDef],
        other: List[ast.stmt],
        original_content: str,
    ) -> str:
        """Reconstruct the file with reorganized components."""
        lines = []

        # Add header
        if header:
            lines.extend(header)
            if not header[-1].strip():
                lines.append("")

        # Add module docstring
        if docstring:
            lines.append('"""' + docstring + '"""')
            lines.append("")

        # Add imports by groups with proper spacing
        import_added = False
        for group_name in [
            "python_stdlib",
            "third_party",
            "odoo",
            "odoo_addons",
            "relative",
        ]:
            group_imports = imports.get(group_name, [])
            if group_imports:
                if import_added:
                    lines.append("")  # Add blank line between import groups
                for imp in group_imports:
                    lines.append(ast.unparse(imp))
                import_added = True

        if import_added:
            lines.append("")
            lines.append("")  # Two blank lines after imports

        # Add module-level constants and variables
        module_vars = [stmt for stmt in other if isinstance(stmt, ast.Assign)]
        if module_vars:
            for var in module_vars:
                lines.append(ast.unparse(var))
            lines.append("")
            lines.append("")

        # Add functions
        if functions:
            for i, func in enumerate(functions):
                if i > 0:
                    lines.append("")
                    lines.append("")
                lines.append(ast.unparse(func))

        if functions and classes:
            lines.append("")
            lines.append("")

        # Add classes with section headers
        if classes:
            for i, cls in enumerate(classes):
                if i > 0:
                    lines.append("")
                    lines.append("")
                
                # Generate class code with section headers if enabled
                if self.add_section_headers and hasattr(cls, '_odoo_sections'):
                    class_code = self._generate_class_with_headers(cls)
                    lines.append(class_code)
                else:
                    lines.append(ast.unparse(cls))

        # Add remaining other statements
        remaining_other = [stmt for stmt in other if not isinstance(stmt, ast.Assign)]
        if remaining_other:
            lines.append("")
            lines.append("")
            for stmt in remaining_other:
                lines.append(ast.unparse(stmt))

        return "\n".join(lines)

    def reorganize_file(self, filepath: str, dry_run: bool = False) -> str:
        """Reorganize a single Python file."""
        # Reset split flag for each file
        self._file_was_split = False
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if not filepath.endswith('.py'):
            raise ValueError(f"Not a Python file: {filepath}")
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError as e:
            logger.error(f"Failed to read {filepath}: {e}")
            raise
        
        if not content.strip():
            logger.warning(f"Empty file: {filepath}")
            return content

        try:
            # First, format with Black to normalize the code
            try:
                content = black.format_str(content, mode=self.black_mode)
            except black.InvalidInput:
                logger.warning(
                    f"Black could not format {filepath}, continuing with original"
                )

            tree = ast.parse(content)

            # Extract components
            imports = self._extract_imports(tree)
            classes = self._extract_classes(tree)
            functions = self._extract_functions(tree)
            other_statements = self._extract_other_statements(tree)

            # Get file header (shebang, encoding, copyright)
            header = self._extract_header(content)

            # Get module docstring
            module_docstring = self._extract_module_docstring(tree)

            # Reorganize imports
            organized_imports = self._organize_imports(imports)

            # Reorganize classes
            organized_classes = self._organize_classes(classes, content)

            # Reorganize functions
            organized_functions = self._organize_functions(functions)

            # Reconstruct file
            new_content = self._reconstruct_file(
                header,
                module_docstring,
                organized_imports,
                organized_functions,
                organized_classes,
                other_statements,
                content,
            )

            # Format the final result with Black
            try:
                new_content = black.format_str(new_content, mode=self.black_mode)
            except black.InvalidInput as e:
                logger.error(f"Black formatting failed for reorganized content: {e}")
                # Return the reorganized but unformatted content
                pass

            # Handle class splitting if enabled and multiple classes exist
            if self.split_classes and len(organized_classes) > 1:
                if dry_run:
                    logger.info(f"Would split {len(organized_classes)} classes from {filepath}")
                    for i, cls in enumerate(organized_classes):
                        if i == 0:
                            logger.info(f"Would keep class {cls.name} in main file: {filepath}")
                        else:
                            class_filename = self._generate_class_filename(cls.name, os.path.splitext(os.path.basename(filepath))[0])
                            logger.info(f"Would create new file: {class_filename}.py for class {cls.name}")
                else:
                    self._split_classes_into_files(
                        filepath, header, module_docstring, organized_imports, 
                        organized_functions, organized_classes, other_statements, content
                    )
                    self._file_was_split = True
                return content  # Return original content as main file will be updated separately
                
            return new_content

        except SyntaxError as e:
            logger.error(f"Syntax error in {filepath}: {e}")
            return content
        except Exception as e:
            logger.error(f"Unexpected error processing {filepath}: {e}")
            return content

    def _split_classes_into_files(
        self, 
        original_filepath: str,
        header: List[str],
        module_docstring: str,
        imports: Dict[str, List[ast.stmt]],
        functions: List[ast.FunctionDef],
        classes: List[ast.ClassDef],
        other_statements: List[ast.stmt],
        original_content: str
    ):
        """Split multiple classes into separate files."""
        from pathlib import Path
        
        original_path = Path(original_filepath)
        base_name = original_path.stem
        file_extension = original_path.suffix
        
        # Use output directory for all generated files
        output_dir = Path(self.output_dir)
        
        # Keep the first (main) class in the original file
        main_class = classes[0]
        additional_classes = classes[1:]
        
        # Create content for main file with first class only
        main_content = self._reconstruct_file(
            header, module_docstring, imports, functions, [main_class], other_statements, original_content
        )
        
        # Format main content
        try:
            main_content = black.format_str(main_content, mode=self.black_mode)
        except black.InvalidInput:
            logger.warning(f"Black could not format main file content")
        
        # Write main file to output directory
        main_output_path = output_dir / f"{base_name}{file_extension}"
        with open(main_output_path, 'w', encoding='utf-8') as f:
            f.write(main_content)
        logger.info(f"Updated main file: {main_output_path}")
        
        # Create separate files for additional classes
        for cls in additional_classes:
            # Generate filename based on class name
            class_filename = self._generate_class_filename(cls.name, base_name)
            class_filepath = output_dir / f"{class_filename}{file_extension}"
            
            # Avoid overwriting existing files
            counter = 1
            while class_filepath.exists():
                class_filepath = output_dir / f"{class_filename}_{counter}{file_extension}"
                counter += 1
            
            # Create content for this class file
            class_content = self._reconstruct_file(
                header, module_docstring, imports, [], [cls], [], original_content
            )
            
            # Format class content
            try:
                class_content = black.format_str(class_content, mode=self.black_mode)
            except black.InvalidInput:
                logger.warning(f"Black could not format class file content for {cls.name}")
            
            # Write class file
            with open(class_filepath, 'w', encoding='utf-8') as f:
                f.write(class_content)
            logger.info(f"Created new file: {class_filepath} for class {cls.name}")
    
    def _generate_class_filename(self, class_name: str, base_name: str) -> str:
        """Generate appropriate filename for a class."""
        # Convert CamelCase to snake_case
        import re
        
        # Handle common Odoo class patterns
        if class_name.endswith('Line'):
            return f"{base_name}_line"
        elif class_name.endswith('Report'):
            return f"{base_name}_report"
        elif class_name.endswith('Wizard'):
            return f"{base_name}_wizard"
        elif 'Custom' in class_name and 'Value' in class_name:
            return f"{base_name}_custom_value"
        elif 'Attribute' in class_name:
            return f"{base_name}_attribute"
        
        # Generic conversion: CamelCase to snake_case
        snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', class_name).lower()
        return snake_case

    def process_directory(
        self,
        directory: str,
        recursive: bool = True,
        dry_run: bool = False,
        no_backup: bool = False,
    ):
        """Process all Python files in a directory."""
        path = Path(directory)
        if not path.exists():
            logger.error(f"Directory {directory} does not exist")
            return
        
        if not path.is_dir():
            logger.error(f"{directory} is not a directory")
            return
            
        pattern = "**/*.py" if recursive else "*.py"
        processed_count = 0
        changed_count = 0
        error_count = 0

        for filepath in path.glob(pattern):
            if filepath.name.startswith("."):
                continue

            # Skip __pycache__ directories and other irrelevant files
            if any(part in ["__pycache__", ".git", ".tox", "venv", "env"] for part in filepath.parts):
                continue
                
            # Skip test files if they follow different conventions
            if filepath.name.startswith("test_") or "test" in filepath.parts:
                logger.debug(f"Skipping test file: {filepath}")
                continue

            logger.info(f"Processing {filepath}")
            processed_count += 1

            try:
                new_content = self.reorganize_file(str(filepath), dry_run=dry_run)

                if dry_run:
                    logger.info(f"Would reorganize {filepath}")
                    print(f"\n--- Preview for {filepath} ---")
                    print(
                        new_content[:500] + "..."
                        if len(new_content) > 500
                        else new_content
                    )
                else:
                    # Read original content for comparison
                    with open(filepath, "r", encoding="utf-8") as f:
                        original_content = f.read()

                    # Only write if content changed
                    if original_content != new_content:
                        # Determine output path
                        output_path = Path(self.output_dir) / filepath.name
                        
                        # Backup original if needed (copy, don't move)
                        if not no_backup:
                            backup_path = filepath.with_suffix(filepath.suffix + ".bak")
                            if backup_path.exists():
                                backup_path.unlink()  # Remove existing backup
                            import shutil
                            shutil.copy2(filepath, backup_path)
                            logger.info(f"Created backup: {backup_path}")

                        # Write reorganized content to output directory (only if not split)
                        if not (self.split_classes and self._file_was_split):
                            output_path.write_text(new_content, encoding="utf-8")
                            logger.info(f"Successfully reorganized: {filepath} -> {output_path}")
                            changed_count += 1
                    else:
                        logger.info(f"No changes needed for {filepath}")

            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")
                error_count += 1
                # Restore from backup if exists
                if not dry_run and not no_backup:
                    backup_path = filepath.with_suffix(".py.bak")
                    if backup_path.exists():
                        try:
                            backup_path.rename(filepath)
                            logger.info(f"Restored {filepath} from backup")
                        except Exception as restore_error:
                            logger.error(f"Failed to restore {filepath}: {restore_error}")
                            
        logger.info(f"Processing complete: {processed_count} files processed, {changed_count} files changed, {error_count} errors")

    def _is_model_attribute(self, node: ast.Assign) -> bool:
        """Check if assignment is a model attribute like _name, _inherit."""
        if not node.targets:
            return False

        target = node.targets[0]
        if isinstance(target, ast.Name):
            return target.id.startswith("_") and target.id in [
                "_name",
                "_description", 
                "_inherit",
                "_inherits",
                "_table",
                "_order",
                "_rec_name",
                "_rec_names_search",
                "_fold_name",
                "_date_name",
                "_parent_name",
                "_parent_store",
                "_log_access",
                "_auto",
                "_register",
                "_abstract",
                "_transient",
                "_custom",
                "_sequence",
                "_sql_constraints",
                "_mail_thread_customer",
                "_check_company_auto",
                "_check_company_domain",
            ]
        return False
    
    def _get_model_attribute_priority(self, node: ast.Assign) -> int:
        """Get priority for model attribute ordering."""
        if not node.targets:
            return 999
            
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            return 999
            
        # Define specific order for model attributes
        priority_order = {
            "_name": 0,
            "_inherit": 1,
            "_inherits": 2,
            "_description": 3,
            "_mail_thread_customer": 4,
            "_order": 5,
            "_rec_name": 6,
            "_rec_names_search": 7,
            "_check_company_auto": 8,
            "_check_company_domain": 9,
            "_table": 10,
            "_fold_name": 11,
            "_date_name": 12,
            "_parent_name": 13,
            "_parent_store": 14,
            "_log_access": 15,
            "_auto": 16,
            "_register": 17,
            "_abstract": 18,
            "_transient": 19,
            "_custom": 20,
            "_sequence": 21,
            "_sql_constraints": 22,
        }
        
        return priority_order.get(target.id, 999)
    
    def _is_sql_constraint(self, node: ast.Assign) -> bool:
        """Check if assignment is a SQL constraint using models.Constraint."""
        if not node.targets:
            return False
            
        # Check if the value is a models.Constraint call
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Attribute):
                # Check for models.Constraint
                if (isinstance(node.value.func.value, ast.Name) 
                    and node.value.func.value.id == "models" 
                    and node.value.func.attr == "Constraint"):
                    return True
            elif isinstance(node.value.func, ast.Name):
                # Check for direct Constraint call (if imported directly)
                if node.value.func.id == "Constraint":
                    return True
        
        return False

    def _is_odoo_model(self, cls: ast.ClassDef) -> bool:
        """Check if class is an Odoo model."""
        for base in cls.bases:
            if isinstance(base, ast.Attribute):
                if base.attr in ["Model", "AbstractModel"]:
                    return True

            elif isinstance(base, ast.Name):
                if base.id in ["Model", "AbstractModel"]:
                    return True

        return False

    def _is_odoo_wizard(self, cls: ast.ClassDef) -> bool:
        """Check if class is an Odoo wizard."""
        for base in cls.bases:
            if isinstance(base, ast.Attribute):
                if base.attr == "TransientModel":
                    return True
            elif isinstance(base, ast.Name):
                if base.id == "TransientModel":
                    return True
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Reorganize Odoo source code for consistency using Black formatting",
        epilog="""
Examples:
  %(prog)s models/product.py                    # Reorganize single file (output to generated_files/)
  %(prog)s models/ --recursive                  # Reorganize all Python files recursively
  %(prog)s models/product.py --dry-run          # Preview changes without modifying
  %(prog)s models/product.py --check             # Check if file needs reorganization
  %(prog)s models/ --line-length 120            # Use custom line length
  %(prog)s models/product.py --no-section-headers  # Reorganize without adding section headers
  %(prog)s models/product.py --split-classes   # Split multiple classes into separate files
  %(prog)s models/product.py --output-dir my_output  # Use custom output directory
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("path", help="File or directory to process")
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Process directories recursively"
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Do not create backup files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "-l",
        "--line-length",
        type=int,
        default=88,
        help="Line length for Black formatting (default: 88)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if files need reorganization without modifying them",
    )
    parser.add_argument(
        "--no-section-headers",
        action="store_true",
        help="Disable adding Odoo-style section headers (# FIELDS, # COMPUTE METHODS, etc.)",
    )
    parser.add_argument(
        "--split-classes",
        action="store_true",
        help="Split multiple classes in a file into separate files",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="generated_files",
        help="Directory for output files (default: generated_files)",
    )

    args = parser.parse_args()

    reorganizer = OdooCodeReorganizer(
        line_length=args.line_length, 
        add_section_headers=not args.no_section_headers,
        split_classes=args.split_classes,
        output_dir=args.output_dir
    )

    if os.path.isfile(args.path):
        if args.check:
            original_content = Path(args.path).read_text(encoding="utf-8")
            result = reorganizer.reorganize_file(args.path, dry_run=True)
            if original_content != result:
                logger.info(f"{args.path} would be reformatted")
                sys.exit(1)
            else:
                logger.info(f"{args.path} is already well organized")
                sys.exit(0)
        elif args.dry_run:
            logger.info(f"Would process: {args.path}")
            result = reorganizer.reorganize_file(args.path, dry_run=True)
            print("--- Result preview ---")
            print(result[:1000] + "..." if len(result) > 1000 else result)
        else:
            # Create backup first before processing
            backup_path = None
            if not args.no_backup and os.path.exists(args.path):
                backup_path = args.path + ".bak"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                # Copy original file to backup (don't move)
                import shutil
                shutil.copy2(args.path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Process file
            result = reorganizer.reorganize_file(args.path)
            
            # Determine output file path
            original_path = Path(args.path)
            output_path = Path(reorganizer.output_dir) / original_path.name
            
            # Write reorganized content to output directory (only if not already handled by split_classes)
            if not (reorganizer.split_classes and reorganizer._file_was_split):
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result)
                logger.info(f"Reorganized file written to: {output_path}")
    else:
        reorganizer.process_directory(
            args.path,
            recursive=args.recursive,
            dry_run=args.dry_run or args.check,
            no_backup=args.no_backup,
        )


if __name__ == "__main__":
    main()
