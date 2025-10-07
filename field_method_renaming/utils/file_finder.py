"""
File Finder with OCA Naming Conventions
=======================================

Locates files in Odoo modules following OCA naming conventions for
efficient processing of field and method renaming operations.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


# Mapeo de relaciones modelo-hijo → modelo-padre
# Cuando se buscan archivos para el hijo, también se buscan archivos del padre
# Ejemplo: stock.move tiene campos en stock_picking_views.xml (via move_ids)
# También usado para cross-module: stock.move fields en mrp.production (via move_raw_ids)
MODEL_PARENT_RELATIONSHIPS = {
    'stock.move': ['stock.picking', 'mrp.production'],  # move_ids in stock.picking, move_raw_ids in mrp.production
    'stock.move.line': ['stock.picking'],      # move_line_ids en stock.picking views
    'sale.order.line': ['sale.order'],         # order_line en sale.order views
    'purchase.order.line': ['purchase.order'], # order_line en purchase.order views
    'account.move.line': ['account.move'],     # line_ids en account.move views
    'product.product': ['product.template'],   # product_variant_ids en product.template views
    'mrp.bom.line': ['mrp.bom'],              # bom_line_ids en mrp.bom views
    'stock.quant': ['stock.quant.package'],    # quant_ids en package views
}


@dataclass
class FileSet:
    """Container for different types of files found for a model"""

    python_files: list[Path]
    view_files: list[Path]
    data_files: list[Path]
    demo_files: list[Path]
    template_files: list[Path]
    report_files: list[Path]
    security_files: list[Path]

    @property
    def all_files(self) -> list[Path]:
        """Get all files in a single list"""
        return (
            self.python_files
            + self.view_files
            + self.data_files
            + self.demo_files
            + self.template_files
            + self.report_files
            + self.security_files
        )

    @property
    def xml_files(self) -> list[Path]:
        """Get all XML files"""
        return (
            self.view_files
            + self.data_files
            + self.demo_files
            + self.template_files
            + self.report_files
            + self.security_files
        )

    def __len__(self) -> int:
        """Total number of files"""
        return len(self.all_files)

    def is_empty(self) -> bool:
        """Check if no files were found"""
        return len(self) == 0


class FileFinder:
    """Finder for files following OCA naming conventions"""

    # OCA naming patterns
    OCA_DIRECTORIES = {
        "python": ["models", "controllers", "wizards", "wizard"],
        "view": ["views", "wizards", "wizard"],  # Wizards can contain XML views
        "data": ["data"],
        "demo": ["demo"],
        "template": ["templates"],
        "report": ["reports"],
        "security": ["security"],
    }

    # File extensions
    PYTHON_EXTENSIONS = [".py"]
    XML_EXTENSIONS = [".xml"]

    def __init__(self, repo_path: str):
        """
        Initialize file finder.

        Args:
            repo_path: Path to the Odoo repository root
        """
        self.repo_path = Path(repo_path)
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repo_path}")

        logger.debug(f"Initialized FileFinder for repository: {self.repo_path}")

    def find_files_for_model(self, module: str, model: str) -> FileSet:
        """
        Find all files related to a specific model following OCA conventions.

        Args:
            module: Module name (e.g., 'sale')
            model: Model name (e.g., 'sale.order')

        Returns:
            FileSet with categorized files
        """
        module_path = self.repo_path / module

        if not module_path.exists():
            logger.warning(f"Module directory not found: {module_path}")
            return FileSet([], [], [], [], [], [], [])

        logger.debug(f"Searching files for model {model} in module {module}")

        # Generate file patterns based on model name
        patterns = self._build_file_patterns(model)

        # Search using OCA conventions
        file_set = self._search_oca_conventions(module_path, patterns)

        # If model has parent relationships, also search in parent model files
        # Example: stock.move fields can appear in stock_picking_views.xml (via move_ids)
        # Also: stock.move fields used in mrp_production.py decorators (cross-module)
        if model in MODEL_PARENT_RELATIONSHIPS:
            logger.debug(f"Model {model} has parent relationships: {MODEL_PARENT_RELATIONSHIPS[model]}")
            for parent_model in MODEL_PARENT_RELATIONSHIPS[model]:
                parent_patterns = self._build_file_patterns(parent_model)
                parent_file_set = self._search_oca_conventions(module_path, parent_patterns)

                # Add both XML and Python files from parent
                # XML: for inline field edits in parent views
                # Python: for cross-module references in @api.depends decorators
                file_set.python_files.extend(parent_file_set.python_files)
                file_set.view_files.extend(parent_file_set.view_files)
                file_set.data_files.extend(parent_file_set.data_files)
                file_set.demo_files.extend(parent_file_set.demo_files)
                file_set.template_files.extend(parent_file_set.template_files)
                file_set.report_files.extend(parent_file_set.report_files)

                logger.debug(f"Added {len(parent_file_set.python_files)} python files and {len(parent_file_set.view_files)} view files from parent model {parent_model}")

        # Remove duplicates and sort
        self._deduplicate_and_sort_fileset(file_set)

        # If still no files found, try recursive search
        if file_set.is_empty():
            logger.info(
                f"No files found with OCA conventions for {model}, trying recursive search..."
            )
            file_set = self._search_recursive_fallback(module_path, model)

        logger.info(f"Found {len(file_set)} files for {module}.{model}")
        self._log_file_summary(file_set, model)

        return file_set

    def _build_file_patterns(self, model: str) -> dict[str, list[str]]:
        """
        Build file patterns based on model name following OCA conventions.

        Args:
            model: Model name (e.g., 'sale.order', 'res.partner')

        Returns:
            Dictionary with file patterns for each file type
        """
        # Convert model name to file name patterns
        # Examples:
        # 'sale.order' -> 'sale_order'
        # 'res.partner' -> 'res_partner'
        # 'account.move.line' -> 'account_move_line'

        base_name = model.replace(".", "_")

        # Also try abbreviated versions for common models
        abbreviated_patterns = self._get_abbreviated_patterns(model)

        patterns = {
            "python": [
                f"{base_name}.py",
                f"{base_name}_*.py",
                f"{base_name}_wizard.py",  # wizard files pattern
                *[f"{abbrev}.py" for abbrev in abbreviated_patterns],
                *[f"{abbrev}_*.py" for abbrev in abbreviated_patterns],
                *[f"{abbrev}_wizard.py" for abbrev in abbreviated_patterns],
            ],
            "xml": [
                f"{base_name}_views.xml",
                f"{base_name}_view.xml",  # singular variant
                f"{base_name}_data.xml",
                f"{base_name}_demo.xml",
                f"{base_name}_templates.xml",
                f"{base_name}_template.xml",  # singular variant
                f"{base_name}_reports.xml",
                f"{base_name}_report.xml",  # singular variant
                f"{base_name}_security.xml",
                f"{base_name}.xml",
                *[f"{abbrev}_views.xml" for abbrev in abbreviated_patterns],
                *[f"{abbrev}_view.xml" for abbrev in abbreviated_patterns],  # singular
                *[f"{abbrev}_data.xml" for abbrev in abbreviated_patterns],
                *[f"{abbrev}_demo.xml" for abbrev in abbreviated_patterns],
                *[f"{abbrev}_templates.xml" for abbrev in abbreviated_patterns],
                *[f"{abbrev}_template.xml" for abbrev in abbreviated_patterns],  # singular
                *[f"{abbrev}_reports.xml" for abbrev in abbreviated_patterns],
                *[f"{abbrev}_report.xml" for abbrev in abbreviated_patterns],  # singular
                *[f"{abbrev}_security.xml" for abbrev in abbreviated_patterns],
                *[f"{abbrev}.xml" for abbrev in abbreviated_patterns],
            ],
        }

        logger.debug(f"Generated patterns for {model}: {patterns}")
        return patterns

    def _get_abbreviated_patterns(self, model: str) -> list[str]:
        """
        Get abbreviated patterns for common models.

        Args:
            model: Full model name

        Returns:
            List of abbreviated names
        """
        abbreviations = []

        # Common abbreviations
        common_abbrev = {
            "sale.order": ["sale"],
            "sale.order.line": ["sale"],
            "purchase.order": ["purchase"],
            "purchase.order.line": ["purchase"],
            "account.move": ["account"],
            "account.move.line": ["account"],
            "res.partner": ["partner"],
            "product.product": ["product"],
            "product.template": ["product"],
            "stock.picking": ["stock"],
            "stock.move": ["stock"],
            "crm.lead": ["crm"],
            "project.project": ["project"],
            "hr.employee": ["hr"],
        }

        if model in common_abbrev:
            abbreviations.extend(common_abbrev[model])

        # Extract first part of model name
        first_part = model.split(".")[0]
        if first_part not in abbreviations:
            abbreviations.append(first_part)

        return abbreviations

    def _search_oca_conventions(
        self, module_path: Path, patterns: dict[str, list[str]]
    ) -> FileSet:
        """
        Search files using OCA naming conventions.

        Args:
            module_path: Path to the module directory
            patterns: File patterns to search for

        Returns:
            FileSet with found files
        """
        file_set = FileSet([], [], [], [], [], [], [])

        # Search Python files
        for directory in self.OCA_DIRECTORIES["python"]:
            dir_path = module_path / directory
            if dir_path.exists():
                for pattern in patterns["python"]:
                    files = list(dir_path.glob(pattern))
                    file_set.python_files.extend(files)

        # Search XML files by type
        for file_type, directories in self.OCA_DIRECTORIES.items():
            if file_type == "python":  # Already handled above
                continue

            file_list = getattr(file_set, f"{file_type}_files")

            for directory in directories:
                dir_path = module_path / directory
                if dir_path.exists():
                    for pattern in patterns["xml"]:
                        # Filter patterns by file type
                        if self._pattern_matches_type(pattern, file_type):
                            files = list(dir_path.glob(pattern))
                            file_list.extend(files)

        # Remove duplicates and sort
        self._deduplicate_and_sort_fileset(file_set)

        return file_set

    def _pattern_matches_type(self, pattern: str, file_type: str) -> bool:
        """
        Check if a pattern is appropriate for a specific file type.

        Args:
            pattern: File pattern
            file_type: Type of file (views, data, demo, etc.)

        Returns:
            True if pattern matches the file type
        """
        if file_type == "views":
            return "_views.xml" in pattern or "_view.xml" in pattern or (
                not any(
                    suffix in pattern
                    for suffix in [
                        "_data.xml",
                        "_demo.xml",
                        "_templates.xml",
                        "_template.xml",
                        "_reports.xml",
                        "_report.xml",
                        "_security.xml",
                    ]
                )
            )
        elif file_type == "data":
            return "_data.xml" in pattern
        elif file_type == "demo":
            return "_demo.xml" in pattern
        elif file_type == "templates":
            return "_templates.xml" in pattern or "_template.xml" in pattern
        elif file_type == "reports":
            return "_reports.xml" in pattern or "_report.xml" in pattern
        elif file_type == "security":
            return "_security.xml" in pattern

        return True

    def _search_recursive_fallback(self, module_path: Path, model: str) -> FileSet:
        """
        Fallback recursive search when OCA conventions don't match.

        Args:
            module_path: Path to the module directory
            model: Model name to search for

        Returns:
            FileSet with found files
        """
        logger.debug(f"Performing recursive search for model {model}")

        file_set = FileSet([], [], [], [], [], [], [])

        # Create search patterns
        search_terms = self._create_search_terms(model)

        # Search all Python files
        for py_file in module_path.rglob("*.py"):
            if self._should_exclude_path(py_file):
                continue

            if self._file_contains_model(py_file, search_terms):
                file_set.python_files.append(py_file)

        # Search all XML files
        for xml_file in module_path.rglob("*.xml"):
            if self._should_exclude_path(xml_file):
                continue

            if self._file_contains_model_reference(xml_file, search_terms):
                # Categorize XML file by directory
                self._categorize_xml_file(xml_file, file_set)

        # Remove duplicates and sort
        self._deduplicate_and_sort_fileset(file_set)

        logger.debug(f"Recursive search found {len(file_set)} files")

        return file_set

    def _create_search_terms(self, model: str) -> list[str]:
        """
        Create search terms for a model.

        Args:
            model: Model name

        Returns:
            List of search terms
        """
        terms = [
            model,  # 'sale.order'
            model.replace(".", "_"),  # 'sale_order'
            f"'{model}'",  # quoted version
            f'"{model}"',  # double quoted version
        ]

        # Add class name variations
        class_name_variations = self._model_to_class_names(model)
        terms.extend(class_name_variations)

        return terms

    def _model_to_class_names(self, model: str) -> list[str]:
        """
        Convert model name to possible class names.

        Args:
            model: Model name (e.g., 'sale.order')

        Returns:
            List of possible class names
        """
        # Convert to CamelCase variations
        parts = model.split(".")

        variations = []

        # CamelCase each part and join
        camel_parts = [part.capitalize() for part in parts]
        variations.append("".join(camel_parts))  # 'SaleOrder'

        # All parts combined with underscores, then CamelCase
        underscore_name = "_".join(parts)
        camel_underscore = "".join(
            word.capitalize() for word in underscore_name.split("_")
        )
        if camel_underscore not in variations:
            variations.append(camel_underscore)

        return variations

    def _should_exclude_path(self, file_path: Path) -> bool:
        """
        Check if a file path should be excluded from search.

        Args:
            file_path: Path to check

        Returns:
            True if should be excluded
        """
        exclude_patterns = [
            "__pycache__",
            ".git",
            ".pytest_cache",
            "migrations",
            ".pyc",
            "tests",  # Often test files don't need renaming
        ]

        path_str = str(file_path)
        return any(pattern in path_str for pattern in exclude_patterns)

    def _file_contains_model(self, file_path: Path, search_terms: list[str]) -> bool:
        """
        Check if a Python file contains references to the model.

        Args:
            file_path: Path to Python file
            search_terms: Terms to search for

        Returns:
            True if file contains model references
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Look for model references
            for term in search_terms:
                if term in content:
                    # Additional validation for Python files
                    if self._validate_python_model_reference(content, term):
                        return True

            return False

        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return False

    def _validate_python_model_reference(self, content: str, term: str) -> bool:
        """
        Validate that a term in Python content is actually a model reference.

        Args:
            content: File content
            term: Search term found

        Returns:
            True if it's a valid model reference
        """
        # Look for common Odoo patterns
        patterns = [
            rf"_name\s*=\s*['\"]?{re.escape(term)}['\"]?",  # _name = 'model.name'
            rf"_inherit\s*=\s*['\"]?{re.escape(term)}['\"]?",  # _inherit = 'model.name'
            rf"class\s+{re.escape(term)}",  # class ModelName
            rf"model\s*=\s*['\"]?{re.escape(term)}['\"]?",  # model = 'model.name'
        ]

        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False

    def _file_contains_model_reference(
        self, file_path: Path, search_terms: list[str]
    ) -> bool:
        """
        Check if an XML file contains references to the model.

        Args:
            file_path: Path to XML file
            search_terms: Terms to search for

        Returns:
            True if file contains model references
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Look for model references in XML
            for term in search_terms:
                if term in content:
                    return True

            return False

        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return False

    def _categorize_xml_file(self, xml_file: Path, file_set: FileSet):
        """
        Categorize an XML file into the appropriate list in FileSet.

        Args:
            xml_file: Path to XML file
            file_set: FileSet to add the file to
        """
        file_name = xml_file.name.lower()
        parent_dir = xml_file.parent.name.lower()

        # Categorize by directory name first
        if parent_dir == "views":
            file_set.view_files.append(xml_file)
        elif parent_dir == "data":
            file_set.data_files.append(xml_file)
        elif parent_dir == "demo":
            file_set.demo_files.append(xml_file)
        elif parent_dir == "templates":
            file_set.template_files.append(xml_file)
        elif parent_dir == "reports":
            file_set.report_files.append(xml_file)
        elif parent_dir == "security":
            file_set.security_files.append(xml_file)
        # Categorize by file name patterns (including singular variants)
        elif "_views.xml" in file_name or "_view.xml" in file_name or "view" in file_name:
            file_set.view_files.append(xml_file)
        elif "_data.xml" in file_name or "data" in file_name:
            file_set.data_files.append(xml_file)
        elif "_demo.xml" in file_name or "demo" in file_name:
            file_set.demo_files.append(xml_file)
        elif "_templates.xml" in file_name or "_template.xml" in file_name or "template" in file_name:
            file_set.template_files.append(xml_file)
        elif "_reports.xml" in file_name or "_report.xml" in file_name or "report" in file_name:
            file_set.report_files.append(xml_file)
        elif "security" in file_name:
            file_set.security_files.append(xml_file)
        else:
            # Default to views if uncertain
            file_set.view_files.append(xml_file)

    def _deduplicate_and_sort_fileset(self, file_set: FileSet):
        """
        Remove duplicates and sort files in FileSet.

        Args:
            file_set: FileSet to process
        """
        # Remove duplicates and sort each list
        file_set.python_files = sorted(list(set(file_set.python_files)))
        file_set.view_files = sorted(list(set(file_set.view_files)))
        file_set.data_files = sorted(list(set(file_set.data_files)))
        file_set.demo_files = sorted(list(set(file_set.demo_files)))
        file_set.template_files = sorted(list(set(file_set.template_files)))
        file_set.report_files = sorted(list(set(file_set.report_files)))
        file_set.security_files = sorted(list(set(file_set.security_files)))

    def _log_file_summary(self, file_set: FileSet, model: str):
        """
        Log summary of found files.

        Args:
            file_set: FileSet with found files
            model: Model name for context
        """
        if file_set.is_empty():
            logger.warning(f"No files found for model {model}")
            return

        summary = []
        if file_set.python_files:
            summary.append(f"Python: {len(file_set.python_files)}")
        if file_set.view_files:
            summary.append(f"Views: {len(file_set.view_files)}")
        if file_set.data_files:
            summary.append(f"Data: {len(file_set.data_files)}")
        if file_set.demo_files:
            summary.append(f"Demo: {len(file_set.demo_files)}")
        if file_set.template_files:
            summary.append(f"Templates: {len(file_set.template_files)}")
        if file_set.report_files:
            summary.append(f"Reports: {len(file_set.report_files)}")
        if file_set.security_files:
            summary.append(f"Security: {len(file_set.security_files)}")

        logger.debug(f"Files for {model}: {', '.join(summary)}")

    def get_module_list(self) -> list[str]:
        """
        Get list of available modules in the repository.

        Returns:
            List of module names
        """
        modules = []

        for item in self.repo_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                # Check if it's an Odoo module (has __manifest__.py or __openerp__.py)
                if (item / "__manifest__.py").exists() or (
                    item / "__openerp__.py"
                ).exists():
                    modules.append(item.name)

        return sorted(modules)

    def validate_module_exists(self, module: str) -> bool:
        """
        Validate that a module exists in the repository.

        Args:
            module: Module name to validate

        Returns:
            True if module exists
        """
        module_path = self.repo_path / module
        return module_path.exists() and (
            (module_path / "__manifest__.py").exists()
            or (module_path / "__openerp__.py").exists()
        )
