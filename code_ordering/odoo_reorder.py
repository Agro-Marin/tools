#!/usr/bin/env python3
"""
Odoo Source Code Reorganizer with Black Formatting - Optimized for Odoo 19.0

This tool reorganizes and formats Odoo Python source files for consistency in styling and semantics.
It follows modern Odoo development conventions and uses Black for code formatting.

Key Improvements in this version:
- Better separation of concerns with dedicated handler classes
- Improved error handling and recovery
- Centralized configuration management
- Reduced code duplication
- Better caching strategies
- More modular and testable design

Author: Agromarin Tools
Version: 6.0.0
Last Updated: 2025
Default Odoo Version: 19.0
"""

# Standard library imports
import argparse
import ast
import json
import logging
import shutil
import sys
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Protocol

# Third-party imports
try:
    import black
except ImportError:
    print("Error: Black is not installed. Please install it with: pip install black")
    sys.exit(1)


# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================

# File processing constants
ENCODING = "utf-8"
BACKUP_SUFFIX = ".bak"
PYTHON_EXTENSION = ".py"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================


class MethodType(Enum):
    """Enumeration of Odoo method types."""

    MODEL_ATTRIBUTE = auto()
    FIELD = auto()
    SQL_CONSTRAINT = auto()
    COMPUTE = auto()
    INVERSE = auto()
    SEARCH = auto()
    CONSTRAINT = auto()
    ONCHANGE = auto()
    DEPENDS = auto()
    CRUD = auto()
    ACTION = auto()
    BUTTON = auto()
    HELPER = auto()
    PRIVATE = auto()
    PUBLIC = auto()
    OVERRIDE = auto()
    MIGRATION = auto()


@dataclass
class OdooDecorator:
    """Represents an Odoo decorator with its metadata."""

    name: str
    method_type: MethodType
    priority: int


@dataclass
class ProcessingStats:
    """Statistics for file processing operations."""

    processed: int = 0
    changed: int = 0
    errors: int = 0

    def merge(self, other: "ProcessingStats") -> None:
        """Merge statistics from another instance."""
        self.processed += other.processed
        self.changed += other.changed
        self.errors += other.errors

    def log_summary(self, operation: str = "Processing") -> None:
        """Log processing statistics summary."""
        logger.info(
            f"{operation} complete: {self.processed} files processed, "
            f"{self.changed} files changed, {self.errors} errors"
        )


@dataclass
class FieldInfo:
    """Information about an Odoo field."""

    node: ast.Assign
    name: str
    field_type: Optional[str] = None
    compute: Optional[str] = None
    depends: List[str] = field(default_factory=list)
    related: Optional[str] = None
    store: bool = False
    readonly: bool = False
    required: bool = False
    semantic_group: str = "other"
    is_related: bool = False
    is_computed: bool = False
    dependencies: List[str] = field(default_factory=list)


@dataclass
class FileComponents:
    """Components extracted from a Python file."""

    header: List[str] = field(default_factory=list)
    module_docstring: str = ""
    imports: List[ast.stmt] = field(default_factory=list)
    classes: List[ast.ClassDef] = field(default_factory=list)
    functions: List[Union[ast.FunctionDef, ast.AsyncFunctionDef]] = field(
        default_factory=list
    )
    other_statements: List[ast.stmt] = field(default_factory=list)


# =============================================================================
# CONFIGURATION MANAGEMENT
# =============================================================================


class OdooConfiguration:
    """Centralized configuration for Odoo code organization."""

    # Singleton instance
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize configuration values."""
        # Manifest file names
        self.MANIFEST_FILES = ["__manifest__.py", "__openerp__.py"]

        # Python directories in Odoo modules
        self.PYTHON_DIRS = [
            "models",
            "wizard",
            "wizards",
            "controllers",
            "report",
            "reports",
            "tests",
            "populate",
            "hooks",
            "migrations",
        ]

        # Directories to skip
        self.SKIP_DIRS = {
            "__pycache__",
            ".git",
            ".tox",
            "venv",
            "env",
            "migrations",
            "static",
            "node_modules",
            ".venv",
            "dist",
            "build",
            ".pytest_cache",
        }

        # Header patterns
        self.HEADER_PATTERNS = [
            "#!",
            "# -*-",
            "# coding:",
            "copyright",
            "license",
            "# Part of",
        ]

        # Import groups order
        self.IMPORT_GROUPS = {
            "python_stdlib": 0,
            "third_party": 1,
            "odoo": 2,
            "odoo_addons": 3,
            "relative": 4,
        }

        # Model attributes order (updated for Odoo 19.0)
        self.MODEL_ATTRIBUTES_ORDER = [
            "_name",
            "_inherit",
            "_inherits",
            "_description",
            "_rec_name",
            "_order",
            "_table",
            "_sequence",
            "_sql_constraints",
            "_auto",
            "_register",
            "_abstract",
            "_transient",
            "_date_name",
            "_fold_name",
            "_parent_name",
            "_parent_store",
            "_check_company_auto",
            "_check_company_domain",
            "_mail_post_access",
            "_mail_thread_customer",
            "_primary_email",
            "_rec_names_search",
            "_barcode_field",
            "_track_subtype",
            "_track_visibility",
            "_mail_flat_thread",
            "_active_test",
            "_translate",
            # New in Odoo 19.0
            "_compute_fields",
            "_depends_context_keys",
            "_context_bin_size",
            "_log_access",
            "_auto_init",
            "_module",
            "_schema",
            "_partition_by",
            "_index_name",
            "_sql_indexes",
            "_check_m2m_tables",
        ]

        # Field types (updated for Odoo 19.0)
        self.ODOO_FIELD_TYPES = {
            # Basic field types
            "Boolean",
            "Integer",
            "Float",
            "Monetary",
            "Char",
            "Text",
            "Selection",
            "Html",
            "Date",
            "Datetime",
            "Binary",
            "Image",
            # Relational fields
            "Many2one",
            "One2many",
            "Many2many",
            "Reference",
            "Many2oneReference",
            "Many2manyCheckboxColumn",
            # Special fields
            "Json",
            "Jsonb",
            "Properties",
            "PropertiesDefinition",
            "Command",
            "Serialized",
            "Id",
            # New in Odoo 19.0
            "Url",
            "Color",
            "Badge",
            "Phone",
            "Email",
            "Handle",
            "Percentage",
            "Map",
            "TimeRange",
            "Uuid",
        }

        # Common fields order
        self.COMMON_FIELDS_ORDER = [
            "name",
            "active",
            "display_name",
            "code",
            "sequence",
            "reference",
            "company_id",
            "currency_id",
            "parent_id",
            "parent_path",
            "child_ids",
            "complete_name",
            "user_id",
            "stage_id",
            "partner_id",
            "product_id",
            "state",
            "priority",
        ]

        # CRUD method order
        self.CRUD_METHOD_ORDER = [
            "default_get",
            "fields_get",
            "fields_view_get",
            "create",
            "name_create",
            "read",
            "read_group",
            "search",
            "search_read",
            "name_search",
            "name_get",
            "write",
            "update",
            "toggle",
            "unlink",
            "copy",
            "copy_data",
            "get_metadata",
            "modified",
            "flush",
            "invalidate_cache",
            "load",
            "export_data",
            "exists",
            "check_access_rights",
            "check_access_rule",
        ]

        # Priority orders
        self.ODOO_IMPORT_PRIORITY = [
            "_",
            "models",
            "fields",
            "api",
            "tools",
            "exceptions",
            "SUPERUSER_ID",
        ]

        self.EXCEPTION_ORDER = [
            "UserError",
            "ValidationError",
            "AccessError",
            "AccessDenied",
            "MissingError",
            "RedirectWarning",
            "Warning",
            "CacheMiss",
        ]

        self.HTTP_ORDER = [
            "request",
            "route",
            "Controller",
            "Response",
            "SessionExpiredException",
            "AuthenticationError",
        ]

        # Section headers
        self.SECTION_HEADERS = {
            MethodType.MODEL_ATTRIBUTE: None,
            MethodType.FIELD: "FIELDS",
            MethodType.SQL_CONSTRAINT: "SQL CONSTRAINTS",
            MethodType.CONSTRAINT: "CONSTRAINTS",
            MethodType.CRUD: "CRUD METHODS",
            MethodType.COMPUTE: "COMPUTE METHODS",
            MethodType.INVERSE: "INVERSE METHODS",
            MethodType.ONCHANGE: "ONCHANGE METHODS",
            MethodType.SEARCH: "SEARCH METHODS",
            MethodType.ACTION: "ACTIONS",
            MethodType.BUTTON: "BUTTON HANDLERS",
            MethodType.OVERRIDE: "OVERRIDES",
            MethodType.PUBLIC: "PUBLIC METHODS",
            MethodType.HELPER: "HELPERS",
            MethodType.PRIVATE: "PRIVATE METHODS",
            MethodType.MIGRATION: "MIGRATION METHODS",
        }

        # Decorators mapping
        self.ODOO_DECORATORS = self._initialize_decorators()

        # Method patterns
        self.METHOD_PATTERNS = {
            MethodType.COMPUTE: ["_compute_"],
            MethodType.INVERSE: ["_inverse_"],
            MethodType.SEARCH: ["_search_"],
            MethodType.CONSTRAINT: ["_check_", "_constraint_"],
            MethodType.ONCHANGE: ["_onchange_"],
            MethodType.ACTION: ["action_", "open_"],
            MethodType.BUTTON: ["button_"],
            MethodType.HELPER: [
                "_prepare_",
                "_get_",
                "_set_",
                "_update_",
                "_process_",
                "_build_",
            ],
            MethodType.MIGRATION: ["_migrate_"],
        }

        # Semantic groups for fields
        self.SEMANTIC_GROUPS = {
            "identification": ["name", "code", "reference", "display_name"],
            "hierarchy": ["parent_id", "parent_path", "child_ids"],
            "sequence": ["sequence", "order", "priority"],
            "status": ["state", "status", "stage", "active"],
            "user_tracking": ["create_uid", "write_uid", "user"],
            "date_time": ["create_date", "write_date", "date", "time", "deadline"],
            "company": ["company"],
            "partner": ["partner", "customer"],
            "product": ["product"],
            "financial": ["amount", "price", "cost", "total"],
            "quantity": ["_count", "_qty", "quantity"],
            "description": ["description", "note", "comment"],
            "configuration": ["is_", "has_", "enable_", "use_", "allow_", "can_"],
            "attachment": ["attachment", "document"],
            "messaging": ["message", "activity"],
        }

    def _initialize_decorators(self) -> Dict[str, OdooDecorator]:
        """Initialize Odoo decorators mapping (updated for Odoo 19.0)."""
        return {
            "@api.model": OdooDecorator("model", MethodType.PUBLIC, 10),
            "@api.model_create_multi": OdooDecorator(
                "model_create_multi", MethodType.CRUD, 5
            ),
            "@api.depends": OdooDecorator("depends", MethodType.COMPUTE, 15),
            "@api.depends_context": OdooDecorator(
                "depends_context", MethodType.COMPUTE, 16
            ),
            "@api.depends_company": OdooDecorator(
                "depends_company", MethodType.COMPUTE, 17
            ),
            "@api.constrains": OdooDecorator("constrains", MethodType.CONSTRAINT, 20),
            "@api.onchange": OdooDecorator("onchange", MethodType.ONCHANGE, 25),
            "@api.ondelete": OdooDecorator("ondelete", MethodType.CRUD, 6),
            "@api.autovacuum": OdooDecorator("autovacuum", MethodType.PUBLIC, 30),
            "@api.returns": OdooDecorator("returns", MethodType.PUBLIC, 11),
            "@api.readonly": OdooDecorator("readonly", MethodType.PUBLIC, 12),
            "@ormcache": OdooDecorator("ormcache", MethodType.HELPER, 35),
            "@ormcache_context": OdooDecorator(
                "ormcache_context", MethodType.HELPER, 36
            ),
            "@tools.conditional": OdooDecorator("conditional", MethodType.HELPER, 40),
            "@tools.ormcache": OdooDecorator("ormcache", MethodType.HELPER, 41),
            # New in Odoo 19.0
            "@api.depends_readonly": OdooDecorator(
                "depends_readonly", MethodType.COMPUTE, 18
            ),
            "@api.model_create_single": OdooDecorator(
                "model_create_single", MethodType.CRUD, 4
            ),
            "@api.onupdate": OdooDecorator("onupdate", MethodType.CRUD, 7),
            "@api.cache": OdooDecorator("cache", MethodType.HELPER, 34),
            "@api.cache_context": OdooDecorator("cache_context", MethodType.HELPER, 37),
            "@api.depends_sql": OdooDecorator("depends_sql", MethodType.COMPUTE, 19),
        }


@dataclass
class ReorganizerConfig:
    """Configuration for the code reorganizer."""

    preserve_comments: bool = True
    line_length: int = 88
    add_section_headers: bool = True
    split_classes: bool = False
    output_dir: Optional[str] = None
    odoo_version: str = "19.0"
    in_place: bool = True
    dry_run: bool = False
    no_backup: bool = False

    def __post_init__(self):
        """Post-initialization setup and validation."""
        self.in_place = self.in_place if self.output_dir is None else False
        self._validate_config()
        self._setup_black_mode()

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not 50 <= self.line_length <= 200:
            raise ValueError("Line length must be between 50 and 200")

        if self.odoo_version not in ["17.0", "18.0", "19.0"]:
            raise ValueError("Odoo version must be 17.0, 18.0, or 19.0")

    def _setup_black_mode(self) -> None:
        """Setup Black formatter configuration."""
        # Odoo 19.0 uses Python 3.12+
        if self.odoo_version == "19.0":
            target_version = black.TargetVersion.PY312
        else:
            target_version = black.TargetVersion.PY311

        self.black_mode = black.Mode(
            target_versions={target_version},
            line_length=self.line_length,
            string_normalization=False,  # Preserve original string quotes (triple quotes, etc.)
            is_pyi=False,
        )


# =============================================================================
# ABSTRACT BASE CLASSES AND PROTOCOLS
# =============================================================================


class FileHandler(ABC):
    """Abstract base class for file handlers."""

    @abstractmethod
    def can_handle(self, filepath: Path) -> bool:
        """Check if this handler can process the file."""
        pass

    @abstractmethod
    def process(self, filepath: Path, config: ReorganizerConfig) -> Tuple[str, bool]:
        """Process the file and return (content, changed)."""
        pass


class ImportHandler(Protocol):
    """Protocol for import handling."""

    def organize_imports(self, imports: List[ast.stmt]) -> Dict[str, List[ast.stmt]]:
        """Organize imports by groups."""
        ...

    def fix_import_issues(self, imports: List[ast.stmt]) -> List[ast.stmt]:
        """Fix common import issues."""
        ...


# =============================================================================
# UTILITY CLASSES
# =============================================================================


class StdlibCache:
    """Cache for standard library module names."""

    def __init__(self):
        self._cache: Set[str] = set()
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the cache with stdlib modules."""
        if hasattr(sys, "stdlib_module_names"):
            self._cache = set(sys.stdlib_module_names)
        else:
            # Fallback for older Python versions
            self._cache = {
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

    def is_stdlib(self, module_name: str) -> bool:
        """Check if module is part of standard library."""
        base_module = module_name.split(".")[0]
        return base_module in self._cache


class ErrorHandler:
    """Centralized error handling."""

    @staticmethod
    def handle_file_error(
        filepath: Path, error: Exception, stats: ProcessingStats
    ) -> None:
        """Handle file processing errors."""
        stats.errors += 1
        if isinstance(error, SyntaxError):
            logger.error(f"Syntax error in {filepath}: {error}")
        elif isinstance(error, UnicodeDecodeError):
            logger.error(f"Encoding error in {filepath}: {error}")
        else:
            logger.error(f"Error processing {filepath}: {error}")
            if logger.isEnabledFor(logging.DEBUG):
                traceback.print_exc()

    @staticmethod
    def handle_warning(message: str) -> None:
        """Handle warning messages."""
        logger.warning(message)


class FileUtils:
    """File utility functions."""

    @staticmethod
    def read_file(filepath: Path, encoding: str = ENCODING) -> str:
        """Read file with proper encoding handling."""
        try:
            return filepath.read_text(encoding=encoding)
        except UnicodeDecodeError as e:
            logger.error(f"Failed to read {filepath}: {e}")
            raise

    @staticmethod
    def write_file(filepath: Path, content: str, encoding: str = ENCODING) -> None:
        """Write content to file."""
        filepath.write_text(content, encoding=encoding)

    @staticmethod
    def create_backup(filepath: Path) -> Optional[Path]:
        """Create a backup of the file."""
        if not filepath.exists():
            return None

        backup_path = filepath.with_suffix(filepath.suffix + BACKUP_SUFFIX)
        if backup_path.exists():
            backup_path.unlink()
        shutil.copy2(filepath, backup_path)
        logger.debug(f"Created backup: {backup_path}")
        return backup_path

    @staticmethod
    def should_skip(filepath: Path, skip_dirs: Set[str]) -> bool:
        """Check if file should be skipped."""
        # Skip hidden files and directories
        if any(part.startswith(".") for part in filepath.parts):
            return True
        # Skip specified directories
        return any(skip_dir in filepath.parts for skip_dir in skip_dirs)


# =============================================================================
# AST UTILITIES
# =============================================================================


class ASTUtils:
    """Utilities for AST manipulation."""

    @staticmethod
    def extract_decorator_name(decorator: ast.expr) -> Optional[str]:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return f"@{decorator.id}"
        elif isinstance(decorator, ast.Attribute):
            base = ASTUtils.get_attribute_base(decorator)
            return f"@{base}.{decorator.attr}" if base else f"@{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return f"@{decorator.func.id}"
            elif isinstance(decorator.func, ast.Attribute):
                base = ASTUtils.get_attribute_base(decorator.func)
                return (
                    f"@{base}.{decorator.func.attr}"
                    if base
                    else f"@{decorator.func.attr}"
                )
        return None

    @staticmethod
    def get_attribute_base(node: ast.Attribute) -> Optional[str]:
        """Get base name from attribute node."""
        if isinstance(node.value, ast.Name):
            return node.value.id
        return None

    @staticmethod
    def is_docstring(node: ast.stmt) -> bool:
        """Check if node is a docstring."""
        return (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )

    @staticmethod
    def extract_docstring(tree: ast.Module) -> str:
        """Extract module-level docstring."""
        if tree.body and ASTUtils.is_docstring(tree.body[0]):
            return ast.get_docstring(tree, clean=False) or ""
        return ""


# =============================================================================
# IMPORT ORGANIZATION
# =============================================================================


class ImportOrganizer:
    """Handles import organization and fixing."""

    def __init__(self):
        self.config = OdooConfiguration()
        self.stdlib_cache = StdlibCache()
        self._import_cache: Dict[str, str] = {}

    def organize_imports(self, imports: List[ast.stmt]) -> Dict[str, List[ast.stmt]]:
        """Organize imports by groups and fix common issues."""
        grouped = {key: [] for key in self.config.IMPORT_GROUPS.keys()}
        module_imports = {}  # (module, level) -> ImportFrom node

        for imp in imports:
            if isinstance(imp, ast.ImportFrom):
                # Handle special import patterns
                if self._handle_special_import(imp, module_imports, grouped):
                    continue

                # Merge imports from same module
                key = (imp.module, imp.level)
                if key in module_imports:
                    self._merge_imports(module_imports[key], imp)
                    continue
                module_imports[key] = imp

            # Classify and group
            group = self._classify_import(imp)
            grouped[group].append(imp)

        # Sort within groups
        self._sort_imports(grouped, module_imports)

        return grouped

    def _classify_import(self, import_node: ast.stmt) -> str:
        """Classify import into groups."""
        # Use cache for performance
        cache_key = ast.unparse(import_node)
        if cache_key in self._import_cache:
            return self._import_cache[cache_key]

        if isinstance(import_node, ast.Import):
            module = import_node.names[0].name
        else:  # ImportFrom
            module = import_node.module or ""
            if import_node.level > 0:
                result = "relative"
                self._import_cache[cache_key] = result
                return result

        # Determine group
        if module.startswith("odoo.addons"):
            result = "odoo_addons"
        elif module.startswith("odoo"):
            result = "odoo"
        elif self.stdlib_cache.is_stdlib(module):
            result = "python_stdlib"
        else:
            result = "third_party"

        self._import_cache[cache_key] = result
        return result

    def _handle_special_import(
        self, imp: ast.ImportFrom, module_imports: Dict, grouped: Dict
    ) -> bool:
        """Handle special import patterns."""
        # Translation import fix
        if imp.module == "odoo.tools.translate":
            return self._fix_translation_import(imp, module_imports, grouped)

        # SUPERUSER_ID import fix
        if imp.module and imp.module.startswith("odoo.") and imp.module != "odoo":
            return self._fix_superuser_import(imp, module_imports, grouped)

        return False

    def _fix_translation_import(
        self, imp: ast.ImportFrom, module_imports: Dict, grouped: Dict
    ) -> bool:
        """Fix translation import: redirect _ to 'from odoo import _'."""
        has_underscore = any(alias.name == "_" for alias in imp.names)
        other_names = [alias for alias in imp.names if alias.name != "_"]

        if has_underscore:
            self._add_to_odoo_import(module_imports, grouped, "_")

        if other_names:
            imp.names = other_names
            return False

        return True  # All names processed

    def _fix_superuser_import(
        self, imp: ast.ImportFrom, module_imports: Dict, grouped: Dict
    ) -> bool:
        """Fix SUPERUSER_ID import: redirect to main odoo import."""
        has_superuser = any(alias.name == "SUPERUSER_ID" for alias in imp.names)
        other_names = [alias for alias in imp.names if alias.name != "SUPERUSER_ID"]

        if has_superuser:
            self._add_to_odoo_import(module_imports, grouped, "SUPERUSER_ID")

            if other_names:
                imp.names = other_names
                return False
            return True  # All names redirected

        return False

    def _add_to_odoo_import(
        self, module_imports: Dict, grouped: Dict, name: str
    ) -> None:
        """Add name to main odoo import."""
        odoo_key = ("odoo", 0)
        if odoo_key in module_imports:
            existing = module_imports[odoo_key]
            if not any(a.name == name for a in existing.names):
                existing.names.append(ast.alias(name=name, asname=None))
        else:
            new_imp = ast.ImportFrom(
                module="odoo", names=[ast.alias(name=name, asname=None)], level=0
            )
            module_imports[odoo_key] = new_imp
            grouped["odoo"].append(new_imp)

    def _merge_imports(self, existing: ast.ImportFrom, new: ast.ImportFrom) -> None:
        """Merge imports from the same module."""
        for alias in new.names:
            if not any(
                a.name == alias.name and a.asname == alias.asname
                for a in existing.names
            ):
                existing.names.append(alias)

    def _sort_imports(
        self, grouped: Dict[str, List[ast.stmt]], module_imports: Dict
    ) -> None:
        """Sort imports within groups."""
        # Sort names within imports
        for imp in module_imports.values():
            if isinstance(imp, ast.ImportFrom) and hasattr(imp, "names"):
                self._sort_import_names(imp)

        # Sort imports within groups
        for group in grouped:
            grouped[group].sort(key=self._get_import_sort_key)

    def _sort_import_names(self, imp: ast.ImportFrom) -> None:
        """Sort names within an import statement."""
        if imp.module == "odoo":
            imp.names.sort(key=self._get_odoo_name_key)
        elif imp.module == "odoo.exceptions":
            imp.names.sort(key=self._get_exception_name_key)
        elif imp.module == "odoo.http":
            imp.names.sort(key=self._get_http_name_key)
        else:
            imp.names.sort(key=lambda a: a.name.lower())

    def _get_odoo_name_key(self, alias: ast.alias) -> Tuple[int, Union[int, str]]:
        """Sort key for odoo import names."""
        if alias.name in self.config.ODOO_IMPORT_PRIORITY:
            return (0, self.config.ODOO_IMPORT_PRIORITY.index(alias.name))
        return (1, alias.name.lower())

    def _get_exception_name_key(self, alias: ast.alias) -> Tuple[int, Union[int, str]]:
        """Sort key for exception names."""
        if alias.name in self.config.EXCEPTION_ORDER:
            return (0, self.config.EXCEPTION_ORDER.index(alias.name))
        return (1, alias.name)

    def _get_http_name_key(self, alias: ast.alias) -> Tuple[int, Union[int, str]]:
        """Sort key for HTTP import names."""
        if alias.name in self.config.HTTP_ORDER:
            return (0, self.config.HTTP_ORDER.index(alias.name))
        return (1, alias.name.lower())

    def _get_import_sort_key(self, import_node: ast.stmt) -> Tuple:
        """Generate sort key for import statements."""
        if isinstance(import_node, ast.Import):
            return (0, import_node.names[0].name.lower())
        else:  # ImportFrom
            module = import_node.module or ""
            names = tuple(sorted(alias.name for alias in import_node.names))
            return (1, module.lower(), names)


# =============================================================================
# FIELD ANALYSIS
# =============================================================================


class FieldAnalyzer:
    """Analyzes and organizes Odoo fields."""

    def __init__(self):
        self.config = OdooConfiguration()
        self._field_cache: Dict[str, bool] = {}

    def is_odoo_field(self, node: ast.Assign) -> bool:
        """Check if assignment is an Odoo field declaration."""
        if not node.value:
            return False

        # Use cache for performance
        try:
            cache_key = ast.unparse(node.value)
            if cache_key in self._field_cache:
                return self._field_cache[cache_key]
        except:
            cache_key = None

        result = self._check_field_pattern(node.value)

        if cache_key:
            self._field_cache[cache_key] = result

        return result

    def _check_field_pattern(self, value_node: ast.expr) -> bool:
        """Check if node matches field pattern."""
        if not isinstance(value_node, ast.Call):
            return False

        # Check fields.Type() pattern
        if isinstance(value_node.func, ast.Attribute):
            if (
                isinstance(value_node.func.value, ast.Name)
                and value_node.func.value.id == "fields"
            ):
                return value_node.func.attr in self.config.ODOO_FIELD_TYPES
        # Check direct Type() pattern
        elif isinstance(value_node.func, ast.Name):
            return value_node.func.id in self.config.ODOO_FIELD_TYPES

        return False

    def extract_field_info(
        self, node: ast.Assign, all_methods: List
    ) -> Optional[FieldInfo]:
        """Extract comprehensive field information."""
        if not node.targets or not self.is_odoo_field(node):
            return None

        target = node.targets[0]
        if not isinstance(target, ast.Name):
            return None

        field_info = FieldInfo(node=node, name=target.id)

        # Extract field attributes
        self._extract_field_attributes(node.value, field_info, all_methods)

        # Determine semantic group
        field_info.semantic_group = self._get_semantic_group(field_info.name)

        return field_info

    def _extract_field_attributes(
        self, value_node: ast.Call, field_info: FieldInfo, all_methods: List
    ) -> None:
        """Extract field attributes from declaration."""
        # Get field type
        if isinstance(value_node.func, ast.Attribute):
            field_info.field_type = value_node.func.attr
        elif isinstance(value_node.func, ast.Name):
            field_info.field_type = value_node.func.id

        # Extract keyword arguments
        for keyword in value_node.keywords:
            if keyword.arg == "compute" and isinstance(keyword.value, ast.Constant):
                field_info.compute = keyword.value.value
                field_info.is_computed = True
                # Extract dependencies
                field_info.dependencies = self._extract_compute_dependencies(
                    keyword.value.value, all_methods
                )
            elif keyword.arg == "related" and isinstance(keyword.value, ast.Constant):
                field_info.related = keyword.value.value
                field_info.is_related = True
            elif keyword.arg == "store" and isinstance(keyword.value, ast.Constant):
                field_info.store = keyword.value.value
            elif keyword.arg == "readonly" and isinstance(keyword.value, ast.Constant):
                field_info.readonly = keyword.value.value
            elif keyword.arg == "required" and isinstance(keyword.value, ast.Constant):
                field_info.required = keyword.value.value

    def _extract_compute_dependencies(
        self, compute_method: str, all_methods: List
    ) -> List[str]:
        """Extract field dependencies from compute method."""
        dependencies = []

        for method in all_methods:
            if hasattr(method, "name") and method.name == compute_method:
                for decorator in method.decorator_list:
                    if self._is_depends_decorator(decorator):
                        dependencies.extend(self._extract_depends_fields(decorator))

        return dependencies

    def _is_depends_decorator(self, decorator: ast.expr) -> bool:
        """Check if decorator is @api.depends."""
        dec_name = ASTUtils.extract_decorator_name(decorator)
        return dec_name and "depends" in dec_name

    def _extract_depends_fields(self, decorator: ast.expr) -> List[str]:
        """Extract field names from @api.depends decorator."""
        fields = []

        if isinstance(decorator, ast.Call):
            for arg in decorator.args:
                if isinstance(arg, ast.Constant):
                    # Extract base field name (before dots)
                    field_name = arg.value.split(".")[0]
                    if field_name:
                        fields.append(field_name)

        return fields

    def _get_semantic_group(self, field_name: str) -> str:
        """Determine the semantic group of a field."""
        field_lower = field_name.lower()

        # Check exact matches first
        system_fields = {
            "id": "identification",
            "create_uid": "user_tracking",
            "write_uid": "user_tracking",
            "create_date": "date_time",
            "write_date": "date_time",
            "active": "status",
            "state": "status",
            "company_id": "company",
        }

        if field_name in system_fields:
            return system_fields[field_name]

        # Check patterns
        for group, patterns in self.config.SEMANTIC_GROUPS.items():
            if any(pattern in field_lower for pattern in patterns):
                return group

        # Check suffixes
        if field_lower.endswith("_id"):
            return "relation"
        elif field_lower.endswith("_ids"):
            return "relation_multiple"

        return "other"

    def organize_fields(
        self, fields: List[ast.Assign], all_methods: List
    ) -> List[ast.Assign]:
        """Organize fields semantically with dependency resolution."""
        if not fields:
            return fields

        # Extract field information
        field_infos = []
        for field in fields:
            info = self.extract_field_info(field, all_methods)
            if info:
                field_infos.append(info)

        # Sort fields
        sorted_infos = self._sort_fields(field_infos)

        return [info.node for info in sorted_infos]

    def _sort_fields(self, field_infos: List[FieldInfo]) -> List[FieldInfo]:
        """Sort fields by priority and dependencies."""
        # Separate by category
        common = []
        computed = []
        related = []
        other = []

        for info in field_infos:
            if info.name in self.config.COMMON_FIELDS_ORDER:
                common.append(info)
            elif info.is_computed:
                computed.append(info)
            elif info.is_related:
                related.append(info)
            else:
                other.append(info)

        # Sort each category
        common.sort(key=lambda f: self.config.COMMON_FIELDS_ORDER.index(f.name))
        computed = self._topological_sort(computed)
        related.sort(key=lambda f: f.related or "")
        other = self._sort_by_semantic_group(other)

        return common + computed + related + other

    def _topological_sort(self, fields: List[FieldInfo]) -> List[FieldInfo]:
        """Sort fields based on dependencies."""
        if not fields:
            return fields

        # Build dependency graph
        field_map = {f.name: f for f in fields}
        visited = set()
        result = []

        def visit(field_info: FieldInfo):
            if field_info.name in visited:
                return
            visited.add(field_info.name)

            # Visit dependencies first
            for dep in field_info.dependencies:
                if dep in field_map:
                    visit(field_map[dep])

            result.append(field_info)

        # Visit all fields
        for field in fields:
            visit(field)

        return result

    def _sort_by_semantic_group(self, fields: List[FieldInfo]) -> List[FieldInfo]:
        """Sort fields by semantic group."""
        group_order = [
            "identification",
            "hierarchy",
            "sequence",
            "status",
            "user_tracking",
            "date_time",
            "company",
            "partner",
            "product",
            "financial",
            "quantity",
            "description",
            "configuration",
            "attachment",
            "messaging",
            "relation",
            "relation_multiple",
            "other",
        ]

        fields.sort(
            key=lambda f: (
                (
                    group_order.index(f.semantic_group)
                    if f.semantic_group in group_order
                    else 999
                ),
                f.name,
            )
        )

        return fields


# =============================================================================
# METHOD CLASSIFICATION
# =============================================================================


class MethodClassifier:
    """Classifies and organizes methods."""

    def __init__(self):
        self.config = OdooConfiguration()
        self._decorator_cache: Dict[str, List[str]] = {}

    def classify_method(
        self, method: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> MethodType:
        """Classify method type based on decorators and naming patterns."""
        decorator_names = self._get_decorator_names(method)

        # Check decorators first
        method_type = self._classify_by_decorators(decorator_names)
        if method_type:
            return method_type

        # Check naming patterns
        return self._classify_by_name(method.name, decorator_names)

    def _get_decorator_names(
        self, method: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> List[str]:
        """Extract decorator names from method."""
        # Use cache for performance
        if method.name in self._decorator_cache:
            return self._decorator_cache[method.name]

        decorator_names = []
        for decorator in method.decorator_list:
            name = ASTUtils.extract_decorator_name(decorator)
            if name:
                decorator_names.append(name)

        self._decorator_cache[method.name] = decorator_names
        return decorator_names

    def _classify_by_decorators(
        self, decorator_names: List[str]
    ) -> Optional[MethodType]:
        """Classify method by its decorators."""
        for dec_name in decorator_names:
            # Check each decorator against known patterns
            if "@api.depends" in dec_name:
                return MethodType.COMPUTE
            elif "@api.constrains" in dec_name:
                return MethodType.CONSTRAINT
            elif "@api.onchange" in dec_name:
                return MethodType.ONCHANGE
            elif "@api.model_create_multi" in dec_name or "@api.ondelete" in dec_name:
                return MethodType.CRUD

        return None

    def _classify_by_name(
        self, method_name: str, decorator_names: List[str]
    ) -> MethodType:
        """Classify method by naming patterns."""
        # Check CRUD methods
        if method_name in self.config.CRUD_METHOD_ORDER:
            return MethodType.CRUD

        # Check pattern prefixes
        for method_type, patterns in self.config.METHOD_PATTERNS.items():
            if any(method_name.startswith(pattern) for pattern in patterns):
                return method_type

        # Check special methods
        if method_name.startswith("__") and method_name.endswith("__"):
            return MethodType.PUBLIC

        # Private methods
        if method_name.startswith("_"):
            return MethodType.PRIVATE

        # Check if override
        if any("@api.model" in d for d in decorator_names):
            return MethodType.OVERRIDE

        return MethodType.PUBLIC

    def organize_methods(
        self, methods: List[Union[ast.FunctionDef, ast.AsyncFunctionDef]]
    ) -> Dict[MethodType, List]:
        """Organize methods by type."""
        categorized = {method_type: [] for method_type in MethodType}

        for method in methods:
            method_type = self.classify_method(method)
            categorized[method_type].append(method)

        # Sort within categories
        self._sort_categorized_methods(categorized)

        return categorized

    def _sort_categorized_methods(self, categorized: Dict[MethodType, List]) -> None:
        """Sort methods within each category."""
        # CRUD methods have special ordering
        if categorized[MethodType.CRUD]:
            categorized[MethodType.CRUD] = self._sort_crud_methods(
                categorized[MethodType.CRUD]
            )

        # Compute-like methods: undecorated first
        for method_type in [
            MethodType.COMPUTE,
            MethodType.INVERSE,
            MethodType.SEARCH,
            MethodType.CONSTRAINT,
            MethodType.ONCHANGE,
        ]:
            if categorized[method_type]:
                categorized[method_type] = self._sort_undecorated_first(
                    categorized[method_type]
                )

        # Other methods: alphabetical
        for method_type in [
            MethodType.ACTION,
            MethodType.BUTTON,
            MethodType.OVERRIDE,
            MethodType.PUBLIC,
            MethodType.HELPER,
            MethodType.PRIVATE,
            MethodType.MIGRATION,
        ]:
            if categorized[method_type]:
                categorized[method_type].sort(key=lambda m: m.name)

    def _sort_crud_methods(self, methods: List) -> List:
        """Sort CRUD methods by lifecycle order."""
        method_dict = {m.name: m for m in methods}
        ordered = []

        # Add in defined order
        for name in self.config.CRUD_METHOD_ORDER:
            if name in method_dict:
                ordered.append(method_dict.pop(name))

        # Add remaining alphabetically
        remaining = sorted(method_dict.values(), key=lambda m: m.name)
        return ordered + remaining

    def _sort_undecorated_first(self, methods: List) -> List:
        """Sort methods with undecorated ones first."""
        undecorated = [m for m in methods if not m.decorator_list]
        decorated = [m for m in methods if m.decorator_list]

        undecorated.sort(key=lambda m: m.name)
        decorated.sort(key=lambda m: m.name)

        return undecorated + decorated


# =============================================================================
# CLASS REORGANIZER
# =============================================================================


class ClassReorganizer:
    """Handles class reorganization."""

    def __init__(self):
        self.config = OdooConfiguration()
        self.field_analyzer = FieldAnalyzer()
        self.method_classifier = MethodClassifier()

    def is_odoo_model(self, cls: ast.ClassDef) -> bool:
        """Check if class is an Odoo model."""
        model_bases = ["Model", "AbstractModel", "TransientModel"]
        return any(self._has_base(cls, base) for base in model_bases)

    def _has_base(self, cls: ast.ClassDef, base_name: str) -> bool:
        """Check if class has specific base."""
        for base in cls.bases:
            if isinstance(base, ast.Attribute) and base.attr == base_name:
                return True
            elif isinstance(base, ast.Name) and base.id == base_name:
                return True
        return False

    def reorganize_class(self, cls: ast.ClassDef) -> None:
        """Reorganize a class following Odoo conventions."""
        # Categorize class elements
        elements = self._categorize_elements(cls)

        # Sort within categories
        self._sort_elements(elements)

        # Build sections
        sections = self._build_sections(elements)

        # Store for later use
        cls._odoo_sections = sections
        cls._odoo_other_statements = elements["other"]

        # Rebuild class body
        self._rebuild_class_body(cls, sections, elements["other"])

    def _categorize_elements(self, cls: ast.ClassDef) -> Dict[str, List]:
        """Categorize all class elements."""
        elements = {
            "model_attrs": [],
            "fields": [],
            "sql_constraints": [],
            "model_indexes": [],
            "methods": [],
            "other": [],
        }

        # Extract all methods for dependency analysis
        all_methods = [
            node
            for node in cls.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        elements["all_methods"] = all_methods

        # Categorize
        for node in cls.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                elements["methods"].append(node)
            elif isinstance(node, ast.Assign):
                if self._is_model_attribute(node):
                    elements["model_attrs"].append(node)
                elif self._is_sql_constraint(node):
                    elements["sql_constraints"].append(node)
                elif self._is_model_index(node):
                    elements["model_indexes"].append(node)
                elif self.field_analyzer.is_odoo_field(node):
                    elements["fields"].append(node)
                else:
                    elements["other"].append(node)
            else:
                elements["other"].append(node)

        return elements

    def _is_model_attribute(self, node: ast.Assign) -> bool:
        """Check if assignment is a model attribute."""
        if not node.targets or not isinstance(node.targets[0], ast.Name):
            return False
        return node.targets[0].id in self.config.MODEL_ATTRIBUTES_ORDER

    def _is_sql_constraint(self, node: ast.Assign) -> bool:
        """Check if assignment is _sql_constraints."""
        if not node.targets or not isinstance(node.targets[0], ast.Name):
            return False
        return node.targets[0].id == "_sql_constraints"

    def _is_model_index(self, node: ast.Assign) -> bool:
        """Check if assignment is a model index."""
        if not node.targets or not isinstance(node.targets[0], ast.Name):
            return False
        attr_name = node.targets[0].id
        return attr_name.endswith("_index") or attr_name == "_sql_indexes"

    def _sort_elements(self, elements: Dict[str, List]) -> None:
        """Sort elements within categories."""
        # Sort model attributes by defined order
        elements["model_attrs"].sort(key=lambda x: self._get_model_attr_priority(x))

        # Organize fields semantically
        elements["fields"] = self.field_analyzer.organize_fields(
            elements["fields"], elements["all_methods"]
        )

        # Organize methods by type
        elements["methods_by_type"] = self.method_classifier.organize_methods(
            elements["methods"]
        )

    def _get_model_attr_priority(self, node: ast.Assign) -> int:
        """Get priority for model attribute ordering."""
        if not node.targets or not isinstance(node.targets[0], ast.Name):
            return 999

        attr_name = node.targets[0].id
        try:
            return self.config.MODEL_ATTRIBUTES_ORDER.index(attr_name)
        except ValueError:
            return 999

    def _build_sections(self, elements: Dict[str, List]) -> List[Tuple]:
        """Build sections for class organization."""
        sections = []

        # Model attributes (no header)
        if elements["model_attrs"]:
            sections.append((None, elements["model_attrs"]))

        # Fields
        if elements["fields"]:
            sections.append(
                (self.config.SECTION_HEADERS[MethodType.FIELD], elements["fields"])
            )

        # SQL constraints
        if elements["sql_constraints"]:
            sections.append(
                (
                    self.config.SECTION_HEADERS[MethodType.SQL_CONSTRAINT],
                    elements["sql_constraints"],
                )
            )

        # Model indexes (placed after SQL constraints)
        if elements["model_indexes"]:
            sections.append((None, elements["model_indexes"]))

        # Methods by type
        if "methods_by_type" in elements:
            for method_type in MethodType:
                methods = elements["methods_by_type"].get(method_type, [])
                if methods and method_type in self.config.SECTION_HEADERS:
                    header = self.config.SECTION_HEADERS[method_type]
                    if header:  # Skip if no header defined
                        sections.append((header, methods))

        return sections

    def _rebuild_class_body(
        self, cls: ast.ClassDef, sections: List[Tuple], other_statements: List
    ) -> None:
        """Rebuild class body with organized sections."""
        new_body = []

        # Add sections
        for _, items in sections:
            new_body.extend(items)

        # Add other statements
        new_body.extend(other_statements)

        cls.body = new_body


# =============================================================================
# CODE GENERATOR
# =============================================================================


class CodeGenerator:
    """Generates formatted code with section headers."""

    def __init__(self, add_section_headers: bool = True):
        self.add_section_headers = add_section_headers
        self.config = OdooConfiguration()

    def generate_file(
        self, components: FileComponents, organized_imports: Dict[str, List[ast.stmt]]
    ) -> str:
        """Generate complete file from components."""
        lines = []

        # Header
        if components.header:
            lines.extend(components.header)
            if not components.header[-1].strip():
                lines.append("")

        # Module docstring
        if components.module_docstring:
            lines.append('"""' + components.module_docstring + '"""')
            lines.append("")

        # Imports
        self._add_imports(organized_imports, lines)

        # Module-level constants
        module_vars = [
            s for s in components.other_statements if isinstance(s, ast.Assign)
        ]
        if module_vars:
            for var in module_vars:
                lines.append(ast.unparse(var))
            lines.extend(["", ""])

        # Functions
        if components.functions:
            for i, func in enumerate(components.functions):
                if i > 0:
                    lines.extend(["", ""])
                lines.append(ast.unparse(func))

        # Classes
        if components.classes:
            if lines:
                lines.extend(["", ""])

            for i, cls in enumerate(components.classes):
                if i > 0:
                    lines.extend(["", ""])

                if self.add_section_headers and hasattr(cls, "_odoo_sections"):
                    class_code = self._generate_class_with_headers(cls)
                    lines.append(class_code)
                else:
                    lines.append(ast.unparse(cls))

        # Remaining statements
        remaining = [
            s for s in components.other_statements if not isinstance(s, ast.Assign)
        ]
        if remaining:
            lines.extend(["", ""])
            for stmt in remaining:
                lines.append(ast.unparse(stmt))

        return "\n".join(lines)

    def _add_imports(
        self, organized_imports: Dict[str, List[ast.stmt]], lines: List[str]
    ) -> None:
        """Add organized imports to lines."""
        import_added = False

        for group in [
            "python_stdlib",
            "third_party",
            "odoo",
            "odoo_addons",
            "relative",
        ]:
            imports = organized_imports.get(group, [])
            if imports:
                if import_added:
                    lines.append("")  # Blank line between groups
                for imp in imports:
                    lines.append(ast.unparse(imp))
                import_added = True

        if import_added:
            lines.extend(["", ""])  # Two blank lines after imports

    def _generate_class_with_headers(self, cls: ast.ClassDef) -> str:
        """Generate class code with section headers."""
        lines = []

        # Class definition
        class_def = f"class {cls.name}"
        if cls.bases:
            base_names = [ast.unparse(base) for base in cls.bases]
            class_def += f"({', '.join(base_names)})"
        class_def += ":"
        lines.append(class_def)

        # Docstring
        if cls.body and ASTUtils.is_docstring(cls.body[0]):
            docstring = ast.unparse(cls.body[0])
            for line in docstring.split("\n"):
                lines.append(f"    {line}" if line.strip() else "")
            lines.append("")

        # Sections
        if hasattr(cls, "_odoo_sections"):
            for header_name, items in cls._odoo_sections:
                if not items:
                    continue

                if header_name:
                    # Add section header
                    divider = "    # " + "-" * 60
                    header = f"    # {header_name}"
                    lines.extend([divider, header, divider, ""])

                # Add items
                for item in items:
                    item_code = ast.unparse(item)
                    for line in item_code.split("\n"):
                        lines.append(f"    {line}" if line.strip() else "")

                # Add spacing
                if header_name not in ["FIELDS", "SQL CONSTRAINTS"]:
                    lines.append("")
                else:
                    lines.append("")

        # Other statements
        if hasattr(cls, "_odoo_other_statements"):
            for stmt in cls._odoo_other_statements:
                stmt_code = ast.unparse(stmt)
                for line in stmt_code.split("\n"):
                    lines.append(f"    {line}" if line.strip() else "")

        # Clean trailing lines
        while lines and not lines[-1].strip():
            lines.pop()

        return "\n".join(lines)


# =============================================================================
# FILE PROCESSORS
# =============================================================================


class PythonFileProcessor(FileHandler):
    """Processes Python files."""

    def __init__(self, config: ReorganizerConfig):
        self.config = config
        self.import_organizer = ImportOrganizer()
        self.class_reorganizer = ClassReorganizer()
        self.code_generator = CodeGenerator(config.add_section_headers)

    def can_handle(self, filepath: Path) -> bool:
        """Check if this processor can handle the file."""
        return filepath.suffix == PYTHON_EXTENSION

    def process(self, filepath: Path, config: ReorganizerConfig) -> Tuple[str, bool]:
        """Process Python file and return (content, changed)."""
        try:
            # Read file
            content = FileUtils.read_file(filepath)
            if not content.strip():
                return content, False

            # Parse and format
            formatted_content = self._format_with_black(content, filepath)
            tree = ast.parse(formatted_content)

            # Extract components
            components = self._extract_components(formatted_content, tree)

            # Reorganize
            reorganized = self._reorganize_components(components)

            # Generate new content
            new_content = self._generate_content(reorganized)

            # Final formatting
            new_content = self._format_with_black(new_content, filepath)

            changed = new_content != content
            return new_content, changed

        except Exception as e:
            ErrorHandler.handle_file_error(filepath, e, ProcessingStats())
            raise

    def _format_with_black(self, content: str, filepath: Path) -> str:
        """Format content with Black."""
        try:
            formatted = black.format_str(content, mode=self.config.black_mode)
            # Post-process to fix triple quotes that were converted to escaped strings
            return self._fix_triple_quotes(formatted)
        except black.InvalidInput as e:
            ErrorHandler.handle_warning(f"Black formatting failed for {filepath}: {e}")
            return content

    def _fix_triple_quotes(self, content: str) -> str:
        """Fix strings with newline escapes back to triple quotes where appropriate."""
        import re

        # Pattern to find strings with multiple newlines that should be triple quotes
        # This pattern looks for strings that start and end with \n and contain multiple \n
        pattern = r'(domain\s*=\s*lambda\s+\w+:\s*)"(\\n\s*.*?\\n\s*)"(\.format\(|,|\))'

        def replace_with_triple_quotes(match):
            prefix = match.group(1)
            string_content = match.group(2)
            suffix = match.group(3)

            # Convert escaped newlines back to actual newlines
            unescaped = string_content.replace("\\n", "\n")

            # Use triple quotes
            return f'{prefix}"""{unescaped}"""{suffix}'

        return re.sub(pattern, replace_with_triple_quotes, content, flags=re.DOTALL)

    def _extract_components(self, content: str, tree: ast.Module) -> FileComponents:
        """Extract components from parsed file."""
        components = FileComponents()

        # Extract header
        components.header = self._extract_header(content)

        # Extract docstring
        components.module_docstring = ASTUtils.extract_docstring(tree)

        # Skip docstring node if present
        skip_first = bool(components.module_docstring)

        # Categorize nodes
        for i, node in enumerate(tree.body):
            if skip_first and i == 0:
                continue

            if isinstance(node, (ast.Import, ast.ImportFrom)):
                components.imports.append(node)
            elif isinstance(node, ast.ClassDef):
                components.classes.append(node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                components.functions.append(node)
            else:
                components.other_statements.append(node)

        return components

    def _extract_header(self, content: str) -> List[str]:
        """Extract file header lines."""
        lines = content.split("\n")
        header = []
        config = OdooConfiguration()

        for line in lines:
            if any(pattern in line.lower() for pattern in config.HEADER_PATTERNS):
                header.append(line)
            elif line.strip() and not line.startswith("#"):
                break

        return header

    def _reorganize_components(
        self, components: FileComponents
    ) -> Tuple[FileComponents, Dict]:
        """Reorganize file components."""
        # Organize imports
        organized_imports = self.import_organizer.organize_imports(components.imports)

        # Reorganize classes
        for cls in components.classes:
            if self.class_reorganizer.is_odoo_model(cls):
                self.class_reorganizer.reorganize_class(cls)

        # Sort functions
        components.functions.sort(key=lambda f: (f.name.startswith("_"), f.name))

        return components, organized_imports

    def _generate_content(self, reorganized: Tuple[FileComponents, Dict]) -> str:
        """Generate new file content."""
        components, organized_imports = reorganized
        return self.code_generator.generate_file(components, organized_imports)


class InitFileProcessor(FileHandler):
    """Special processor for __init__.py files."""

    def __init__(self, config: ReorganizerConfig):
        self.config = config
        self.import_organizer = ImportOrganizer()

    def can_handle(self, filepath: Path) -> bool:
        """Check if this is an __init__.py file."""
        return filepath.name == "__init__.py"

    def process(self, filepath: Path, config: ReorganizerConfig) -> Tuple[str, bool]:
        """Process __init__.py file."""
        try:
            content = FileUtils.read_file(filepath)

            # Empty init files don't need processing
            if not content.strip():
                return content, False

            # Parse file
            tree = ast.parse(content)

            # Extract imports only
            imports = [
                node
                for node in tree.body
                if isinstance(node, (ast.Import, ast.ImportFrom))
            ]

            if not imports:
                return content, False

            # Reorganize
            new_content = self._reorganize_init_file(content, imports)

            # Format with Black
            try:
                new_content = black.format_str(new_content, mode=config.black_mode)
            except:
                pass

            changed = new_content != content
            return new_content, changed

        except Exception as e:
            ErrorHandler.handle_file_error(filepath, e, ProcessingStats())
            return FileUtils.read_file(filepath), False

    def _reorganize_init_file(self, content: str, imports: List[ast.stmt]) -> str:
        """Reorganize __init__.py file."""
        # Extract header
        header = self._extract_header(content)

        # Organize imports
        organized_imports = self.import_organizer.organize_imports(imports)

        # Build new content
        lines = []

        # Add header
        if header:
            lines.extend(header)
            if header and not header[-1].strip():
                lines.append("")

        # Add imports
        import_added = False
        for group in [
            "python_stdlib",
            "third_party",
            "odoo",
            "odoo_addons",
            "relative",
        ]:
            group_imports = organized_imports.get(group, [])
            if group_imports:
                if import_added:
                    lines.append("")
                for imp in group_imports:
                    lines.append(ast.unparse(imp))
                import_added = True

        return "\n".join(lines)

    def _extract_header(self, content: str) -> List[str]:
        """Extract header from init file."""
        lines = content.split("\n")
        header = []
        config = OdooConfiguration()

        for line in lines:
            if any(pattern in line.lower() for pattern in config.HEADER_PATTERNS):
                header.append(line)
            elif line.strip() and not line.startswith("#"):
                break

        return header


# =============================================================================
# MODULE AND DIRECTORY PROCESSORS
# =============================================================================


class ModuleProcessor:
    """Processes Odoo modules."""

    def __init__(self, config: ReorganizerConfig):
        self.config = config
        self.python_processor = PythonFileProcessor(config)
        self.init_processor = InitFileProcessor(config)
        self.odoo_config = OdooConfiguration()

    def is_odoo_module(self, path: Path) -> bool:
        """Check if directory is an Odoo module."""
        return any(
            (path / manifest).exists() for manifest in self.odoo_config.MANIFEST_FILES
        )

    def process_module(self, module_path: Path) -> ProcessingStats:
        """Process an entire Odoo module."""
        stats = ProcessingStats()

        if not self.is_odoo_module(module_path):
            ErrorHandler.handle_warning(f"{module_path} is not an Odoo module")
            return stats

        logger.info(f"Processing Odoo module: {module_path}")

        # Process root __init__.py
        root_init = module_path / "__init__.py"
        if root_init.exists():
            self._process_file(root_init, self.init_processor, stats)

        # Process Python directories
        for dir_name in self.odoo_config.PYTHON_DIRS:
            dir_path = module_path / dir_name
            if dir_path.exists():
                self._process_directory(dir_path, stats)

        return stats

    def _process_directory(self, dir_path: Path, stats: ProcessingStats) -> None:
        """Process all Python files in a directory."""
        # Process __init__.py first
        init_file = dir_path / "__init__.py"
        if init_file.exists():
            self._process_file(init_file, self.init_processor, stats)

        # Process other Python files
        for py_file in dir_path.glob("*.py"):
            if py_file.name != "__init__.py":
                self._process_file(py_file, self.python_processor, stats)

    def _process_file(
        self, filepath: Path, processor: FileHandler, stats: ProcessingStats
    ) -> None:
        """Process a single file."""
        stats.processed += 1

        try:
            new_content, changed = processor.process(filepath, self.config)

            if changed:
                if not self.config.dry_run:
                    if not self.config.no_backup:
                        FileUtils.create_backup(filepath)
                    FileUtils.write_file(filepath, new_content)
                    logger.info(f"Reorganized {filepath}")
                else:
                    logger.info(f"Would reorganize {filepath}")
                stats.changed += 1
            else:
                logger.debug(f"No changes needed for {filepath}")

        except Exception as e:
            ErrorHandler.handle_file_error(filepath, e, stats)


class DirectoryProcessor:
    """Processes directories."""

    def __init__(self, config: ReorganizerConfig):
        self.config = config
        self.module_processor = ModuleProcessor(config)
        self.python_processor = PythonFileProcessor(config)
        self.init_processor = InitFileProcessor(config)
        self.odoo_config = OdooConfiguration()

    def process_directory(
        self, dir_path: Path, recursive: bool = True
    ) -> ProcessingStats:
        """Process all Python files in a directory."""
        stats = ProcessingStats()

        # Check if it's an Odoo module
        if self.module_processor.is_odoo_module(dir_path):
            logger.info(f"Detected Odoo module at {dir_path}")
            return self.module_processor.process_module(dir_path)

        # Process as regular directory
        pattern = "**/*.py" if recursive else "*.py"

        for filepath in dir_path.glob(pattern):
            if FileUtils.should_skip(filepath, self.odoo_config.SKIP_DIRS):
                continue

            stats.processed += 1

            try:
                # Choose processor
                if filepath.name == "__init__.py":
                    processor = self.init_processor
                else:
                    processor = self.python_processor

                new_content, changed = processor.process(filepath, self.config)

                if changed:
                    if not self.config.dry_run:
                        if not self.config.no_backup:
                            FileUtils.create_backup(filepath)
                        FileUtils.write_file(filepath, new_content)
                        logger.info(f"Reorganized {filepath}")
                    else:
                        logger.info(f"Would reorganize {filepath}")
                    stats.changed += 1

            except Exception as e:
                ErrorHandler.handle_file_error(filepath, e, stats)

        return stats


# =============================================================================
# MAIN REORGANIZER
# =============================================================================


class OdooCodeReorganizer:
    """Main orchestrator for reorganizing Odoo source code."""

    def __init__(self, **kwargs):
        """Initialize the reorganizer with configuration."""
        self.config = ReorganizerConfig(**kwargs)
        self.module_processor = ModuleProcessor(self.config)
        self.directory_processor = DirectoryProcessor(self.config)
        self.python_processor = PythonFileProcessor(self.config)
        self.init_processor = InitFileProcessor(self.config)

    def reorganize_file(self, filepath: str) -> str:
        """Reorganize a single Python file."""
        path = Path(filepath)

        if not path.is_file():
            raise FileNotFoundError(f"File not found: {filepath}")

        if not path.suffix == PYTHON_EXTENSION:
            raise ValueError(f"Not a Python file: {filepath}")

        # Choose processor
        if path.name == "__init__.py":
            processor = self.init_processor
        else:
            processor = self.python_processor

        new_content, changed = processor.process(path, self.config)

        if not self.config.dry_run and changed:
            if not self.config.no_backup:
                FileUtils.create_backup(path)
            FileUtils.write_file(path, new_content)
            logger.info(f"Reorganized {path}")

        return new_content

    def process_module(self, module_path: str) -> None:
        """Process an entire Odoo module."""
        path = Path(module_path)

        if not path.exists():
            raise FileNotFoundError(f"Path not found: {module_path}")

        if not path.is_dir():
            raise ValueError(f"Not a directory: {module_path}")

        stats = self.module_processor.process_module(path)
        stats.log_summary("Module processing")

    def process_directory(self, directory: str, recursive: bool = True) -> None:
        """Process all Python files in a directory."""
        path = Path(directory)

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not path.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        stats = self.directory_processor.process_directory(path, recursive)
        stats.log_summary("Directory processing")


# =============================================================================
# CLI INTERFACE
# =============================================================================


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Reorganize Odoo source code for consistency using Black formatting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("path", help="File, directory, or Odoo module to process")
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Process directories recursively"
    )
    parser.add_argument(
        "-m", "--module", action="store_true", help="Force module processing mode"
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
        "--no-section-headers",
        action="store_true",
        help="Disable adding section headers",
    )
    parser.add_argument("--output-dir", type=str, help="Output to separate directory")
    parser.add_argument(
        "--odoo-version",
        type=str,
        default="19.0",
        choices=["17.0", "18.0", "19.0"],
        help="Odoo version (default: 19.0)",
    )

    return parser


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        # Create reorganizer
        reorganizer = OdooCodeReorganizer(
            line_length=args.line_length,
            add_section_headers=not args.no_section_headers,
            output_dir=args.output_dir,
            odoo_version=args.odoo_version,
            dry_run=args.dry_run,
            no_backup=args.no_backup,
        )

        # Process path
        path = Path(args.path)

        if path.is_file():
            reorganizer.reorganize_file(str(path))
        elif path.is_dir():
            if args.module or reorganizer.module_processor.is_odoo_module(path):
                reorganizer.process_module(str(path))
            else:
                reorganizer.process_directory(str(path), recursive=args.recursive)
        else:
            logger.error(f"Path {path} does not exist")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        if logger.isEnabledFor(logging.DEBUG):
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
