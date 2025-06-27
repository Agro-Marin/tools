#!/usr/bin/env python3
"""
Odoo Source Code Reorganizer with Black Formatting
Reorders and organizes Odoo Python source files for consistency in styling and semantics.
Uses Black for code formatting.
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
    """Reorganizes Odoo source code files for consistency."""

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

    def __init__(self, preserve_comments: bool = True, line_length: int = 88):
        self.preserve_comments = preserve_comments
        self.line_length = line_length
        self.black_mode = black.Mode(
            target_versions={black.TargetVersion.PY38},
            line_length=line_length,
            string_normalization=True,
            is_pyi=False,
        )

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
            and isinstance(tree.body[0].value, (ast.Str, ast.Constant))
        ):
            return ast.get_docstring(tree, clean=False)
        return ""

    def _extract_imports(self, tree: ast.Module) -> List[ast.stmt]:
        """Extract all import statements."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                # Only get top-level imports
                for parent in ast.walk(tree):
                    if hasattr(parent, "body") and node in parent.body:
                        if isinstance(parent, ast.Module):
                            imports.append(node)
                        break
        return imports

    def _extract_classes(self, tree: ast.Module) -> List[ast.ClassDef]:
        """Extract all class definitions."""
        return [node for node in tree.body if isinstance(node, ast.ClassDef)]

    def _extract_functions(self, tree: ast.Module) -> List[ast.FunctionDef]:
        """Extract all function definitions."""
        return [node for node in tree.body if isinstance(node, ast.FunctionDef)]

    def _extract_other_statements(self, tree: ast.Module) -> List[ast.stmt]:
        """Extract statements that are not imports, classes, or functions."""
        other = []
        skip_first = False

        # Check if first statement is docstring
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, (ast.Str, ast.Constant))
        ):
            skip_first = True

        for i, node in enumerate(tree.body):
            if skip_first and i == 0:
                continue
            if not isinstance(
                node, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.FunctionDef)
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
        if module.startswith("odoo.addons"):
            return "odoo_addons"

        elif module.startswith("odoo") or module.startswith("openerp"):
            return "odoo"

        # Python standard library (expanded list)
        stdlib_modules = {
            "abc",
            "argparse",
            "ast",
            "asyncio",
            "base64",
            "builtins",
            "collections",
            "contextlib",
            "copy",
            "csv",
            "datetime",
            "decimal",
            "enum",
            "functools",
            "gc",
            "glob",
            "hashlib",
            "html",
            "http",
            "importlib",
            "inspect",
            "io",
            "itertools",
            "json",
            "logging",
            "math",
            "operator",
            "os",
            "pathlib",
            "pickle",
            "platform",
            "pprint",
            "re",
            "random",
            "shutil",
            "signal",
            "socket",
            "sqlite3",
            "string",
            "struct",
            "subprocess",
            "sys",
            "tempfile",
            "threading",
            "time",
            "traceback",
            "types",
            "typing",
            "unittest",
            "urllib",
            "uuid",
            "warnings",
            "weakref",
            "xml",
            "zipfile",
            "zlib",
        }

        base_module = module.split(".")[0]
        if base_module in stdlib_modules:
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
        private_methods = []
        other_methods = []
        other_statements = []

        for node in cls.body:
            if isinstance(node, ast.FunctionDef):
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
                elif method_type == "private":
                    private_methods.append(node)
                else:
                    other_methods.append(node)
            elif isinstance(node, ast.Assign):
                # Check if it's a model attribute or field
                if self._is_model_attribute(node):
                    model_attributes.append(node)
                else:
                    fields.append(node)
            else:
                other_statements.append(node)

        # Sort methods within categories
        compute_methods.sort(key=lambda m: m.name)
        constraint_methods.sort(key=lambda m: m.name)
        onchange_methods.sort(key=lambda m: m.name)
        action_methods.sort(key=lambda m: m.name)
        private_methods.sort(key=lambda m: m.name)

        # Reorder class body following Odoo conventions
        cls.body = (
            model_attributes  # _name, _description, etc.
            + fields  # field declarations
            + constraint_methods  # @api.constrains methods
            + crud_methods  # create, write, unlink
            + compute_methods  # @api.depends methods
            + onchange_methods  # @api.onchange methods
            + action_methods  # action_* methods
            + other_methods  # other public methods
            + private_methods  # private methods
            + other_statements  # any other statements
        )

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

        # Add classes
        if classes:
            for i, cls in enumerate(classes):
                if i > 0:
                    lines.append("")
                    lines.append("")
                lines.append(ast.unparse(cls))

        # Add remaining other statements
        remaining_other = [stmt for stmt in other if not isinstance(stmt, ast.Assign)]
        if remaining_other:
            lines.append("")
            lines.append("")
            for stmt in remaining_other:
                lines.append(ast.unparse(stmt))

        return "\n".join(lines)

    def reorganize_file(self, filepath: str) -> str:
        """Reorganize a single Python file."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

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

            return new_content

        except SyntaxError as e:
            logger.error(f"Syntax error in {filepath}: {e}")
            return content

    def process_directory(
        self,
        directory: str,
        recursive: bool = True,
        dry_run: bool = False,
        no_backup: bool = False,
    ):
        """Process all Python files in a directory."""
        path = Path(directory)
        pattern = "**/*.py" if recursive else "*.py"

        for filepath in path.glob(pattern):
            if filepath.name.startswith("."):
                continue

            # Skip __pycache__ directories
            if "__pycache__" in filepath.parts:
                continue

            logger.info(f"Processing {filepath}")

            try:
                new_content = self.reorganize_file(str(filepath))

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
                        # Backup original
                        if not no_backup:
                            backup_path = filepath.with_suffix(".py.bak")
                            filepath.rename(backup_path)
                            filepath = backup_path.with_suffix(".py")

                        # Write reorganized content
                        filepath.write_text(new_content, encoding="utf-8")
                        logger.info(f"Successfully reorganized {filepath}")
                    else:
                        logger.info(f"No changes needed for {filepath}")

            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")
                # Restore from backup if exists
                if not dry_run and not no_backup:
                    backup_path = filepath.with_suffix(".py.bak")
                    if backup_path.exists():
                        backup_path.rename(filepath)

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
            ]
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
        description="Reorganize Odoo source code for consistency using Black formatting"
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

    args = parser.parse_args()

    reorganizer = OdooCodeReorganizer(line_length=args.line_length)

    if os.path.isfile(args.path):
        if args.check:
            original_content = Path(args.path).read_text(encoding="utf-8")
            result = reorganizer.reorganize_file(args.path)
            if original_content != result:
                logger.info(f"{args.path} would be reformatted")
                sys.exit(1)
            else:
                logger.info(f"{args.path} is already well organized")
                sys.exit(0)
        elif args.dry_run:
            logger.info(f"Would process: {args.path}")
            result = reorganizer.reorganize_file(args.path)
            print("--- Result preview ---")
            print(result[:1000] + "..." if len(result) > 1000 else result)
        else:
            result = reorganizer.reorganize_file(args.path)
            if not args.no_backup:
                backup_path = args.path + ".bak"
                os.rename(args.path, backup_path)
            with open(args.path, "w", encoding="utf-8") as f:
                f.write(result)
            logger.info(f"Reorganized {args.path}")
    else:
        reorganizer.process_directory(
            args.path,
            recursive=args.recursive,
            dry_run=args.dry_run or args.check,
            no_backup=args.no_backup,
        )


if __name__ == "__main__":
    main()
