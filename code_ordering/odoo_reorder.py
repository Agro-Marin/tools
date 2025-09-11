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
# ORDER EXPORT/IMPORT
# =============================================================================


class OrderExportType(Enum):
    """Types of order exports."""

    FILE = "file"
    MODULE = "module"
    DIRECTORY = "directory"


@dataclass
class ClassOrder:
    """Order information for a class."""

    name: str
    model_attributes: List[str] = field(default_factory=list)
    fields: List[str] = field(default_factory=list)
    sql_constraints: List[str] = field(default_factory=list)
    model_indexes: List[str] = field(default_factory=list)
    methods: Dict[str, List[str]] = field(default_factory=dict)
    section_headers: Dict[str, str] = field(
        default_factory=dict
    )  # Maps section name to header text

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "model_attributes": self.model_attributes,
            "fields": self.fields,
            "sql_constraints": self.sql_constraints,
            "model_indexes": self.model_indexes,
            "methods": self.methods,
            "section_headers": self.section_headers,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ClassOrder":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            model_attributes=data.get("model_attributes", []),
            fields=data.get("fields", []),
            sql_constraints=data.get("sql_constraints", []),
            model_indexes=data.get("model_indexes", []),
            methods=data.get("methods", {}),
            section_headers=data.get("section_headers", {}),
        )


@dataclass
class FileOrder:
    """Order information for a file."""

    filepath: str
    import_groups: List[str] = field(default_factory=list)
    import_statements: List[str] = field(default_factory=list)
    classes: List[ClassOrder] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    module_level_vars: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "filepath": self.filepath,
            "import_groups": self.import_groups,
            "import_statements": self.import_statements,
            "classes": [cls.to_dict() for cls in self.classes],
            "functions": self.functions,
            "module_level_vars": self.module_level_vars,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "FileOrder":
        """Create from dictionary."""
        return cls(
            filepath=data["filepath"],
            import_groups=data.get("import_groups", []),
            import_statements=data.get("import_statements", []),
            classes=[ClassOrder.from_dict(c) for c in data.get("classes", [])],
            functions=data.get("functions", []),
            module_level_vars=data.get("module_level_vars", []),
        )


@dataclass
class OrderExport:
    """Complete order export data."""

    version: str = "1.0"
    odoo_version: str = "19.0"
    export_date: str = field(default_factory=lambda: datetime.now().isoformat())
    export_type: OrderExportType = OrderExportType.FILE
    name: str = ""
    files: Dict[str, FileOrder] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "odoo_version": self.odoo_version,
            "export_date": self.export_date,
            "type": self.export_type.value,
            "name": self.name,
            "files": {k: v.to_dict() for k, v in self.files.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "OrderExport":
        """Create from dictionary."""
        return cls(
            version=data.get("version", "1.0"),
            odoo_version=data.get("odoo_version", "19.0"),
            export_date=data.get("export_date", datetime.now().isoformat()),
            export_type=OrderExportType(data.get("type", "file")),
            name=data.get("name", ""),
            files={k: FileOrder.from_dict(v) for k, v in data.get("files", {}).items()},
        )


class OrderExporter:
    """Exports the current order of code elements."""

    def __init__(self):
        self.config = OdooConfiguration()
        self.field_analyzer = FieldAnalyzer()
        self.method_classifier = MethodClassifier()

    def export_file(self, filepath: Path, odoo_version: str = "19.0") -> OrderExport:
        """Export the current order of a single Python file."""
        try:
            content = FileUtils.read_file(filepath)
            if not content.strip():
                raise ValueError(f"File {filepath} is empty")

            tree = ast.parse(content)
            file_order = self._extract_file_order(filepath, tree, content)

            export = OrderExport(
                odoo_version=odoo_version,
                export_type=OrderExportType.FILE,
                name=str(filepath),
                files={str(filepath): file_order},
            )

            return export

        except Exception as e:
            logger.error(f"Failed to export order from {filepath}: {e}")
            raise

    def export_module(
        self, module_path: Path, odoo_version: str = "19.0"
    ) -> OrderExport:
        """Export the current order of an entire Odoo module."""
        if not module_path.is_dir():
            raise ValueError(f"{module_path} is not a directory")

        # Check if it's an Odoo module
        manifest_files = ["__manifest__.py", "__openerp__.py"]
        if not any((module_path / f).exists() for f in manifest_files):
            raise ValueError(f"{module_path} is not an Odoo module")

        export = OrderExport(
            odoo_version=odoo_version,
            export_type=OrderExportType.MODULE,
            name=module_path.name,
            files={},
        )

        # Process Python directories
        for dir_name in self.config.PYTHON_DIRS:
            dir_path = module_path / dir_name
            if dir_path.exists():
                self._process_directory_for_export(dir_path, module_path, export)

        # Process root __init__.py
        root_init = module_path / "__init__.py"
        if root_init.exists():
            relative_path = str(root_init.relative_to(module_path))
            content = FileUtils.read_file(root_init)
            if content.strip():
                tree = ast.parse(content)
                export.files[relative_path] = self._extract_file_order(
                    root_init, tree, content
                )

        return export

    def export_directory(
        self, dir_path: Path, odoo_version: str = "19.0"
    ) -> OrderExport:
        """Export the current order of all Python files in a directory."""
        if not dir_path.is_dir():
            raise ValueError(f"{dir_path} is not a directory")

        export = OrderExport(
            odoo_version=odoo_version,
            export_type=OrderExportType.DIRECTORY,
            name=str(dir_path),
            files={},
        )

        # Find all Python files
        for py_file in dir_path.rglob("*.py"):
            if not FileUtils.should_skip(py_file, self.config.SKIP_DIRS):
                relative_path = str(py_file.relative_to(dir_path))
                content = FileUtils.read_file(py_file)
                if content.strip():
                    tree = ast.parse(content)
                    export.files[relative_path] = self._extract_file_order(
                        py_file, tree, content
                    )

        return export

    def save_order(self, order_export: OrderExport, output_path: Path) -> None:
        """Save order export to JSON file."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(order_export.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Order exported to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save order to {output_path}: {e}")
            raise

    def _process_directory_for_export(
        self, dir_path: Path, base_path: Path, export: OrderExport
    ) -> None:
        """Process a directory for export."""
        for py_file in dir_path.glob("*.py"):
            relative_path = str(py_file.relative_to(base_path))
            content = FileUtils.read_file(py_file)
            if content.strip():
                tree = ast.parse(content)
                export.files[relative_path] = self._extract_file_order(
                    py_file, tree, content
                )

    def _extract_file_order(
        self, filepath: Path, tree: ast.Module, content: str
    ) -> FileOrder:
        """Extract the order of elements from a parsed file."""
        file_order = FileOrder(filepath=str(filepath))

        # Extract imports order
        imports = [
            node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        for imp in imports:
            file_order.import_statements.append(ast.unparse(imp))

        # Extract import groups
        import_organizer = ImportOrganizer()
        grouped_imports = import_organizer.organize_imports(imports)
        file_order.import_groups = list(grouped_imports.keys())

        # Extract classes
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_order = self._extract_class_order(node, content)
                file_order.classes.append(class_order)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                file_order.functions.append(node.name)
            elif isinstance(node, ast.Assign) and not isinstance(node, ast.AnnAssign):
                # Module-level variables
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        file_order.module_level_vars.append(target.id)

        return file_order

    def _extract_class_order(
        self, class_node: ast.ClassDef, content: str
    ) -> ClassOrder:
        """Extract the order of elements from a class."""
        class_order = ClassOrder(name=class_node.name)

        # Extract section headers from the source content
        section_headers = self._extract_section_headers(class_node, content)
        class_order.section_headers = section_headers

        # Group methods by type
        methods_by_type = {}

        for node in class_node.body:
            if isinstance(node, ast.Assign):
                # Check if it's a model attribute
                if node.targets and isinstance(node.targets[0], ast.Name):
                    attr_name = node.targets[0].id

                    if attr_name in self.config.MODEL_ATTRIBUTES_ORDER:
                        class_order.model_attributes.append(attr_name)
                    elif attr_name == "_sql_constraints":
                        class_order.sql_constraints.append(attr_name)
                    elif attr_name.endswith("_index") or attr_name == "_sql_indexes":
                        # Handle model indexes
                        class_order.model_indexes.append(attr_name)
                    elif self.field_analyzer.is_odoo_field(node):
                        class_order.fields.append(attr_name)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_type = self.method_classifier.classify_method(node)
                type_name = method_type.name

                if type_name not in methods_by_type:
                    methods_by_type[type_name] = []
                methods_by_type[type_name].append(node.name)

        class_order.methods = methods_by_type
        return class_order

    def _extract_section_headers(
        self, class_node: ast.ClassDef, content: str
    ) -> Dict[str, str]:
        """Extract section headers from the class source code."""
        section_headers = {}

        # Get the source lines for the class
        lines = content.split("\n")

        # Find section headers (pattern: # ---- followed by # SECTION_NAME followed by # ----)
        import re

        header_pattern = re.compile(r"^\s*# -+$")

        i = 0
        while i < len(lines):
            line = lines[i]
            # Check if this is a header divider
            if header_pattern.match(line):
                # Check if next line contains the section name
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip().startswith("#"):
                        # Extract section name
                        section_name = next_line.strip().lstrip("#").strip()
                        # Check if there's another divider after
                        if i + 2 < len(lines) and header_pattern.match(lines[i + 2]):
                            # Store the complete header (3 lines)
                            header_text = "\n".join([line, next_line, lines[i + 2]])
                            section_headers[section_name] = header_text
                            i += 3
                            continue
            i += 1

        return section_headers


class OrderImporter:
    """Imports and applies a previously exported order."""

    def __init__(self):
        self.config = OdooConfiguration()
        self.field_analyzer = FieldAnalyzer()
        self.method_classifier = MethodClassifier()
        self.class_reorganizer = ClassReorganizer()

    def load_order(self, order_file: Path) -> OrderExport:
        """Load order from JSON file."""
        try:
            with open(order_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return OrderExport.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load order from {order_file}: {e}")
            raise

    def apply_order_to_file(
        self, order_data: OrderExport, filepath: Path
    ) -> Tuple[str, bool]:
        """Apply saved order to a single file."""
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Find the order for this file
        file_order = None
        for file_path, order in order_data.files.items():
            if Path(file_path).name == filepath.name:
                file_order = order
                break

        # If no exact match, use the first available order (for cross-version ordering)
        if not file_order and order_data.files:
            # Use the first (and typically only) order in the file
            file_order = list(order_data.files.values())[0]
            logger.info(
                f"Using order from {list(order_data.files.keys())[0]} for {filepath}"
            )

        if not file_order:
            raise ValueError(f"No order found in the order file")

        content = FileUtils.read_file(filepath)
        tree = ast.parse(content)

        # Apply the order
        new_content = self._apply_order(tree, file_order, content)

        # Format with Black
        try:
            config = ReorganizerConfig(odoo_version=order_data.odoo_version)
            formatted = black.format_str(new_content, mode=config.black_mode)
            new_content = self._fix_triple_quotes(formatted)
        except:
            pass

        changed = new_content != content
        return new_content, changed

    def apply_order_to_module(
        self, order_data: OrderExport, module_path: Path
    ) -> ProcessingStats:
        """Apply saved order to an entire module."""
        if order_data.export_type != OrderExportType.MODULE:
            raise ValueError("Order file is not for a module")

        stats = ProcessingStats()

        for file_path, file_order in order_data.files.items():
            full_path = module_path / file_path
            if full_path.exists():
                try:
                    new_content, changed = self._apply_file_order(
                        full_path, file_order, order_data.odoo_version
                    )
                    if changed:
                        FileUtils.create_backup(full_path)
                        FileUtils.write_file(full_path, new_content)
                        stats.changed += 1
                        logger.info(f"Applied order to {full_path}")
                    stats.processed += 1
                except Exception as e:
                    logger.error(f"Failed to apply order to {full_path}: {e}")
                    stats.errors += 1
            else:
                logger.warning(f"File {full_path} not found, skipping")

        return stats

    def _apply_order(
        self, tree: ast.Module, file_order: FileOrder, content: str
    ) -> str:
        """Apply order to AST and generate new content."""
        # Extract components
        components = self._extract_components_with_order(tree, file_order, content)

        # Generate new content
        lines = []

        # Add header if exists
        header = self._extract_header(content)
        if header:
            lines.extend(header)
            lines.append("")

        # Add module docstring if exists
        if tree.body and ASTUtils.is_docstring(tree.body[0]):
            docstring = ast.get_docstring(tree, clean=False)
            if docstring:
                lines.append('"""' + docstring + '"""')
                lines.append("")

        # Add imports in order
        if components["imports"]:
            for imp in components["imports"]:
                lines.append(ast.unparse(imp))
            lines.extend(["", ""])

        # Add module-level variables in order
        if components["module_vars"]:
            for var in components["module_vars"]:
                lines.append(ast.unparse(var))
            lines.extend(["", ""])

        # Add functions in order
        if components["functions"]:
            for i, func in enumerate(components["functions"]):
                if i > 0:
                    lines.extend(["", ""])
                lines.append(ast.unparse(func))

        # Add classes in order
        if components["classes"]:
            if lines:
                lines.extend(["", ""])

            for i, cls in enumerate(components["classes"]):
                if i > 0:
                    lines.extend(["", ""])

                # Apply order to class internals
                self._apply_class_order(cls, file_order)
                # Use the rewriter to generate class with headers
                if hasattr(cls, "_odoo_sections"):
                    class_code = self._generate_class_with_headers(cls)
                    lines.append(class_code)
                else:
                    lines.append(ast.unparse(cls))

        # Add other statements
        if components["other"]:
            lines.extend(["", ""])
            for stmt in components["other"]:
                lines.append(ast.unparse(stmt))

        return "\n".join(lines)

    def _apply_file_order(
        self, filepath: Path, file_order: FileOrder, odoo_version: str
    ) -> Tuple[str, bool]:
        """Apply order to a file."""
        content = FileUtils.read_file(filepath)
        tree = ast.parse(content)

        new_content = self._apply_order(tree, file_order, content)

        # Format with Black
        try:
            config = ReorganizerConfig(odoo_version=odoo_version)
            formatted = black.format_str(new_content, mode=config.black_mode)
            new_content = self._fix_triple_quotes(formatted)
        except:
            pass

        changed = new_content != content
        return new_content, changed

    def _extract_components_with_order(
        self, tree: ast.Module, file_order: FileOrder, content: str
    ) -> Dict:
        """Extract components and organize them according to the saved order."""
        components = {
            "imports": [],
            "module_vars": [],
            "functions": [],
            "classes": [],
            "other": [],
        }

        # Create lookup maps
        import_map = {}
        var_map = {}
        func_map = {}
        class_map = {}

        # Skip docstring if present
        skip_first = tree.body and ASTUtils.is_docstring(tree.body[0])

        for i, node in enumerate(tree.body):
            if skip_first and i == 0:
                continue

            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_str = ast.unparse(node)
                import_map[import_str] = node
            elif isinstance(node, ast.ClassDef):
                class_map[node.name] = node
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_map[node.name] = node
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_map[target.id] = node
                        break
            else:
                components["other"].append(node)

        # Order imports according to saved order
        for import_str in file_order.import_statements:
            if import_str in import_map:
                components["imports"].append(import_map.pop(import_str))

        # Add any new imports not in the order
        components["imports"].extend(import_map.values())

        # Order module variables
        for var_name in file_order.module_level_vars:
            if var_name in var_map:
                components["module_vars"].append(var_map.pop(var_name))

        # Add any new variables
        components["module_vars"].extend(var_map.values())

        # Order functions
        for func_name in file_order.functions:
            if func_name in func_map:
                components["functions"].append(func_map.pop(func_name))

        # Add any new functions
        components["functions"].extend(func_map.values())

        # Order classes
        for class_order in file_order.classes:
            if class_order.name in class_map:
                components["classes"].append(class_map.pop(class_order.name))

        # Add any new classes
        components["classes"].extend(class_map.values())

        return components

    def _apply_class_order(
        self, class_node: ast.ClassDef, file_order: FileOrder
    ) -> None:
        """Apply order to class internals."""
        # Find the class order
        class_order = None
        for co in file_order.classes:
            if co.name == class_node.name:
                class_order = co
                break

        if not class_order:
            return

        # Organize class body elements
        new_body = []
        elements = {
            "docstring": None,
            "model_attrs": {},
            "fields": {},
            "sql_constraints": {},
            "model_indexes": {},
            "methods": {},
            "other": [],
        }

        # Categorize elements
        for node in class_node.body:
            if ASTUtils.is_docstring(node):
                elements["docstring"] = node
            elif isinstance(node, ast.Assign):
                if node.targets and isinstance(node.targets[0], ast.Name):
                    attr_name = node.targets[0].id

                    if attr_name in self.config.MODEL_ATTRIBUTES_ORDER:
                        elements["model_attrs"][attr_name] = node
                    elif attr_name == "_sql_constraints":
                        elements["sql_constraints"][attr_name] = node
                    elif attr_name.endswith("_index") or attr_name == "_sql_indexes":
                        # Handle model indexes
                        elements["model_indexes"][attr_name] = node
                    elif self.field_analyzer.is_odoo_field(node):
                        elements["fields"][attr_name] = node
                    else:
                        elements["other"].append(node)
                else:
                    elements["other"].append(node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_type = self.method_classifier.classify_method(node)
                type_name = method_type.name

                if type_name not in elements["methods"]:
                    elements["methods"][type_name] = {}
                elements["methods"][type_name][node.name] = node
            else:
                elements["other"].append(node)

        # Rebuild body in order with section headers
        sections = []

        # Docstring section
        if elements["docstring"]:
            sections.append((None, [elements["docstring"]]))

        # Model attributes
        model_attrs_list = []
        for attr_name in class_order.model_attributes:
            if attr_name in elements["model_attrs"]:
                model_attrs_list.append(elements["model_attrs"].pop(attr_name))
        model_attrs_list.extend(elements["model_attrs"].values())
        if model_attrs_list:
            sections.append((None, model_attrs_list))

        # Fields section with header
        fields_list = []
        for field_name in class_order.fields:
            if field_name in elements["fields"]:
                fields_list.append(elements["fields"].pop(field_name))
        fields_list.extend(elements["fields"].values())
        if fields_list:
            header_name = "FIELDS" if "FIELDS" in class_order.section_headers else None
            sections.append((header_name, fields_list))

        # SQL constraints
        if elements["sql_constraints"]:
            sections.append((None, list(elements["sql_constraints"].values())))

        # Model indexes section with header
        indexes_list = []
        for index_name in class_order.model_indexes:
            if index_name in elements["model_indexes"]:
                indexes_list.append(elements["model_indexes"].pop(index_name))
        indexes_list.extend(elements["model_indexes"].values())
        if indexes_list:
            header_name = (
                "INDEXES" if "INDEXES" in class_order.section_headers else None
            )
            sections.append((header_name, indexes_list))

        # Methods sections with headers
        # Map method types to their section headers
        method_section_map = {
            "CONSTRAINT_METHODS": "CONSTRAINT METHODS",
            "DEFAULT_METHODS": "DEFAULT METHODS",
            "COMPUTE_METHODS": "COMPUTE METHODS",
            "ONCHANGE_METHODS": "ONCHANGE METHODS",
            "CRUD_METHODS": "CRUD METHODS",
            "ACTION_METHODS": "ACTION METHODS",
            "BUSINESS_METHODS": "BUSINESS METHODS",
            "HELPER_METHODS": "HELPER METHODS",
            "INIT_METHODS": "INIT METHODS",
            "OTHER_METHODS": "OTHER METHODS",
        }

        for method_type, method_names in class_order.methods.items():
            method_list = []
            if method_type in elements["methods"]:
                type_methods = elements["methods"][method_type]

                # Add in saved order
                for method_name in method_names:
                    if method_name in type_methods:
                        method_list.append(type_methods.pop(method_name))

                # Add any remaining methods of this type
                method_list.extend(type_methods.values())

                # Remove this type from elements so we don't add them again
                del elements["methods"][method_type]

            if method_list:
                # Check if we have a header for this method type
                header_name = None
                for header_key in class_order.section_headers:
                    if header_key == method_section_map.get(method_type, method_type):
                        header_name = header_key
                        break
                sections.append((header_name, method_list))

        # Add any remaining methods not in order
        for type_methods in elements["methods"].values():
            if type_methods:
                sections.append((None, list(type_methods.values())))

        # Add other elements
        if elements["other"]:
            sections.append((None, elements["other"]))

        # Store sections in class node for rewriter to use
        class_node._odoo_sections = sections

        # Clear body as it will be regenerated by the rewriter
        class_node.body = []

    def _extract_header(self, content: str) -> List[str]:
        """Extract file header lines."""
        lines = content.split("\n")
        header = []

        for line in lines:
            if any(pattern in line.lower() for pattern in self.config.HEADER_PATTERNS):
                header.append(line)
            elif line.strip() and not line.startswith("#"):
                break

        return header

    def _fix_triple_quotes(self, content: str) -> str:
        """Fix strings with newline escapes back to triple quotes where appropriate."""
        import re

        pattern = r'(domain\s*=\s*lambda\s+\w+:\s*)"(\\n\s*.*?\\n\s*)"(\.format\(|,|\))'

        def replace_with_triple_quotes(match):
            prefix = match.group(1)
            string_content = match.group(2)
            suffix = match.group(3)

            unescaped = string_content.replace("\\n", "\n")
            return f'{prefix}"""{unescaped}"""{suffix}'

        return re.sub(pattern, replace_with_triple_quotes, content, flags=re.DOTALL)

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

        # Sections
        if hasattr(cls, "_odoo_sections"):
            for header_name, items in cls._odoo_sections:
                if not items:
                    continue

                if header_name:
                    # Add section header
                    divider = "    # " + "-" * 60
                    header = f"    # {header_name}"
                    lines.extend([divider, header, divider])

                # Add items
                for item in items:
                    item_code = ast.unparse(item)
                    for line in item_code.split("\n"):
                        lines.append(f"    {line}" if line.strip() else "")

                # Add spacing after section
                lines.append("")

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

    # Order export/import arguments
    parser.add_argument(
        "--export-order",
        action="store_true",
        help="Export the current order of the file/module to a JSON file",
    )
    parser.add_argument(
        "--apply-order",
        type=str,
        metavar="ORDER_FILE",
        help="Apply order from a JSON file to reorganize the code",
    )
    parser.add_argument(
        "-o",
        "--order-output",
        type=str,
        default="order.json",
        help="Output file for order export (default: order.json)",
    )
    parser.add_argument(
        "--validate",
        type=str,
        metavar="BACKUP_FILE",
        help="Validate reordering by comparing with backup file",
    )

    return parser


def validate_reordering(
    original_file: Path, reordered_file: Path, order_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Validate that a reordered file contains all elements from the original file.

    Args:
        original_file: Path to the original/backup file
        reordered_file: Path to the reordered file
        order_file: Optional path to the order JSON file used

    Returns:
        Dictionary with validation results including:
        - is_valid: Boolean indicating if all elements are preserved
        - original_elements: Dict of all elements in original
        - reordered_elements: Dict of all elements in reordered
        - missing_elements: Any elements in original but not in reordered
        - added_elements: Any elements in reordered but not in original
        - order_changes: Details about ordering changes
    """
    logger.info(f"Validating reordering: {original_file} vs {reordered_file}")

    result = {
        "is_valid": True,
        "original_elements": {},
        "reordered_elements": {},
        "missing_elements": {},
        "added_elements": {},
        "order_changes": {},
        "errors": [],
    }

    try:
        # Parse both files
        original_content = FileUtils.read_file(original_file)
        reordered_content = FileUtils.read_file(reordered_file)

        original_tree = ast.parse(original_content)
        reordered_tree = ast.parse(reordered_content)

        # Extract all elements from both files
        processor = PythonFileProcessor(ReorganizerConfig())

        # Extract from original
        original_components = processor._extract_components(
            original_content, original_tree
        )

        # Extract from reordered
        reordered_components = processor._extract_components(
            reordered_content, reordered_tree
        )

        # Compare imports
        original_imports = set()
        reordered_imports = set()

        for imp in original_components.imports:
            original_imports.add(ast.unparse(imp))

        for imp in reordered_components.imports:
            reordered_imports.add(ast.unparse(imp))

        result["original_elements"]["imports"] = sorted(original_imports)
        result["reordered_elements"]["imports"] = sorted(reordered_imports)

        missing_imports = original_imports - reordered_imports
        added_imports = reordered_imports - original_imports

        if missing_imports:
            result["missing_elements"]["imports"] = sorted(missing_imports)
            result["is_valid"] = False
            result["errors"].append(f"Missing imports: {missing_imports}")

        if added_imports:
            result["added_elements"]["imports"] = sorted(added_imports)
            # Added imports are not necessarily invalid

        # Compare classes
        original_classes = {cls.name: cls for cls in original_components.classes}
        reordered_classes = {cls.name: cls for cls in reordered_components.classes}

        result["original_elements"]["classes"] = sorted(original_classes.keys())
        result["reordered_elements"]["classes"] = sorted(reordered_classes.keys())

        missing_classes = set(original_classes.keys()) - set(reordered_classes.keys())
        added_classes = set(reordered_classes.keys()) - set(original_classes.keys())

        if missing_classes:
            result["missing_elements"]["classes"] = sorted(missing_classes)
            result["is_valid"] = False
            result["errors"].append(f"Missing classes: {missing_classes}")

        if added_classes:
            result["added_elements"]["classes"] = sorted(added_classes)

        # For each class, compare fields and methods
        for class_name in original_classes:
            if class_name not in reordered_classes:
                continue

            orig_class = original_classes[class_name]
            reord_class = reordered_classes[class_name]

            # Compare fields - fields are stored in the class body
            orig_fields = set()
            reord_fields = set()

            for node in orig_class.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            orig_fields.add(target.id)

            for node in reord_class.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            reord_fields.add(target.id)

            missing_fields = orig_fields - reord_fields
            added_fields = reord_fields - orig_fields

            if missing_fields:
                if "fields" not in result["missing_elements"]:
                    result["missing_elements"]["fields"] = {}
                result["missing_elements"]["fields"][class_name] = sorted(
                    missing_fields
                )
                result["is_valid"] = False
                result["errors"].append(
                    f"Missing fields in {class_name}: {missing_fields}"
                )

            if added_fields:
                if "fields" not in result["added_elements"]:
                    result["added_elements"]["fields"] = {}
                result["added_elements"]["fields"][class_name] = sorted(added_fields)

            # Compare methods - methods are functions in the class body
            orig_methods = set()
            reord_methods = set()

            for node in orig_class.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    orig_methods.add(node.name)

            for node in reord_class.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    reord_methods.add(node.name)

            missing_methods = orig_methods - reord_methods
            added_methods = reord_methods - orig_methods

            if missing_methods:
                if "methods" not in result["missing_elements"]:
                    result["missing_elements"]["methods"] = {}
                result["missing_elements"]["methods"][class_name] = sorted(
                    missing_methods
                )
                result["is_valid"] = False
                result["errors"].append(
                    f"Missing methods in {class_name}: {missing_methods}"
                )

            if added_methods:
                if "methods" not in result["added_elements"]:
                    result["added_elements"]["methods"] = {}
                result["added_elements"]["methods"][class_name] = sorted(added_methods)

            # Track field order changes
            if orig_fields == reord_fields and len(orig_fields) > 0:
                orig_field_order = []
                reord_field_order = []

                for node in orig_class.body:
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                orig_field_order.append(target.id)

                for node in reord_class.body:
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                reord_field_order.append(target.id)

                if orig_field_order != reord_field_order:
                    if "fields" not in result["order_changes"]:
                        result["order_changes"]["fields"] = {}
                    result["order_changes"]["fields"][class_name] = {
                        "original": orig_field_order[:10],  # First 10 for brevity
                        "reordered": reord_field_order[:10],
                    }

            # Track method order changes
            if orig_methods == reord_methods and len(orig_methods) > 0:
                orig_method_order = []
                reord_method_order = []

                for node in orig_class.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        orig_method_order.append(node.name)

                for node in reord_class.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        reord_method_order.append(node.name)

                if orig_method_order != reord_method_order:
                    if "methods" not in result["order_changes"]:
                        result["order_changes"]["methods"] = {}
                    result["order_changes"]["methods"][class_name] = {
                        "original": orig_method_order[:10],  # First 10 for brevity
                        "reordered": reord_method_order[:10],
                    }

        # Compare functions
        orig_functions = {func.name for func in original_components.functions}
        reord_functions = {func.name for func in reordered_components.functions}

        result["original_elements"]["functions"] = sorted(orig_functions)
        result["reordered_elements"]["functions"] = sorted(reord_functions)

        missing_functions = orig_functions - reord_functions
        added_functions = reord_functions - orig_functions

        if missing_functions:
            result["missing_elements"]["functions"] = sorted(missing_functions)
            result["is_valid"] = False
            result["errors"].append(f"Missing functions: {missing_functions}")

        if added_functions:
            result["added_elements"]["functions"] = sorted(added_functions)

        # Compare module-level variables
        orig_vars = set()
        reord_vars = set()

        # Extract module-level variables from other_statements
        for stmt in original_components.other_statements:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        orig_vars.add(target.id)

        for stmt in reordered_components.other_statements:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        reord_vars.add(target.id)

        result["original_elements"]["module_vars"] = sorted(orig_vars)
        result["reordered_elements"]["module_vars"] = sorted(reord_vars)

        missing_vars = orig_vars - reord_vars
        added_vars = reord_vars - orig_vars

        if missing_vars:
            result["missing_elements"]["module_vars"] = sorted(missing_vars)
            result["is_valid"] = False
            result["errors"].append(f"Missing module variables: {missing_vars}")

        if added_vars:
            result["added_elements"]["module_vars"] = sorted(added_vars)

        # Summary
        if result["is_valid"]:
            logger.info("✅ Validation PASSED: All elements preserved")
        else:
            logger.error("❌ Validation FAILED: Missing elements detected")
            for error in result["errors"]:
                logger.error(f"  - {error}")

        # Log statistics
        logger.info(f"Original file elements:")
        logger.info(f"  - Imports: {len(original_imports)}")
        logger.info(f"  - Classes: {len(original_classes)}")
        logger.info(f"  - Functions: {len(orig_functions)}")
        logger.info(f"  - Module vars: {len(orig_vars)}")

        logger.info(f"Reordered file elements:")
        logger.info(f"  - Imports: {len(reordered_imports)}")
        logger.info(f"  - Classes: {len(reordered_classes)}")
        logger.info(f"  - Functions: {len(reord_functions)}")
        logger.info(f"  - Module vars: {len(reord_vars)}")

        if result["order_changes"]:
            logger.info("Order changes detected (this is expected)")

    except Exception as e:
        result["is_valid"] = False
        result["errors"].append(f"Validation error: {str(e)}")
        logger.error(f"Validation failed with error: {e}")
        if logger.isEnabledFor(logging.DEBUG):
            traceback.print_exc()

    return result


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        # Process path
        path = Path(args.path)

        # Handle validation
        if args.validate:
            backup_file = Path(args.validate)
            if not backup_file.exists():
                logger.error(f"Backup file {backup_file} does not exist")
                sys.exit(1)

            result = validate_reordering(backup_file, path)

            if result["is_valid"]:
                logger.info("✅ Validation PASSED")
                sys.exit(0)
            else:
                logger.error("❌ Validation FAILED")
                sys.exit(1)

        # Handle order export
        elif args.export_order:
            exporter = OrderExporter()

            if path.is_file():
                order_data = exporter.export_file(path, args.odoo_version)
            elif path.is_dir():
                if args.module or any(
                    (path / f).exists() for f in ["__manifest__.py", "__openerp__.py"]
                ):
                    order_data = exporter.export_module(path, args.odoo_version)
                else:
                    order_data = exporter.export_directory(path, args.odoo_version)
            else:
                logger.error(f"Path {path} does not exist")
                sys.exit(1)

            output_path = Path(args.order_output)
            exporter.save_order(order_data, output_path)
            logger.info(f"Order exported successfully to {output_path}")

        # Handle order import/apply
        elif args.apply_order:
            importer = OrderImporter()
            order_file = Path(args.apply_order)

            if not order_file.exists():
                logger.error(f"Order file {order_file} does not exist")
                sys.exit(1)

            order_data = importer.load_order(order_file)

            if path.is_file():
                new_content, changed = importer.apply_order_to_file(order_data, path)
                if changed and not args.dry_run:
                    if not args.no_backup:
                        FileUtils.create_backup(path)
                    FileUtils.write_file(path, new_content)
                    logger.info(f"Applied order to {path}")
                elif changed:
                    logger.info(f"Would apply order to {path}")
                else:
                    logger.info(f"No changes needed for {path}")

            elif path.is_dir() and order_data.export_type == OrderExportType.MODULE:
                stats = importer.apply_order_to_module(order_data, path)
                stats.log_summary("Order application")
            else:
                logger.error("Order file type doesn't match the target path")
                sys.exit(1)

        # Regular reorganization (existing functionality)
        else:
            reorganizer = OdooCodeReorganizer(
                line_length=args.line_length,
                add_section_headers=not args.no_section_headers,
                output_dir=args.output_dir,
                odoo_version=args.odoo_version,
                dry_run=args.dry_run,
                no_backup=args.no_backup,
            )

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
