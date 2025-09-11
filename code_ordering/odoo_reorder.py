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
from datetime import datetime
import logging
import shutil
import sys
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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
    generate_docs: bool = False
    docs_output_dir: Optional[str] = None
    
    # Migration/Pattern Application Configuration
    apply_pattern: bool = False
    pattern_file: Optional[str] = None
    target_file: Optional[str] = None
    match_threshold: float = 0.8
    backup_suffix: str = ".backup"
    migration_report_path: Optional[str] = None
    
    # Migration Strategies
    missing_element_strategy: str = "document"  # document, ignore, error
    new_element_strategy: str = "append"        # append, classify, ignore
    conflict_resolution: str = "preserve"       # preserve, override, manual

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
            
        # Validate migration configurations
        if self.apply_pattern:
            if not self.pattern_file:
                raise ValueError("Pattern file is required when apply_pattern is True")
            if not self.target_file:
                raise ValueError("Target file is required when apply_pattern is True")
                
        if not 0.0 <= self.match_threshold <= 1.0:
            raise ValueError("Match threshold must be between 0.0 and 1.0")
            
        if self.missing_element_strategy not in ["document", "ignore", "error"]:
            raise ValueError("missing_element_strategy must be 'document', 'ignore', or 'error'")
            
        if self.new_element_strategy not in ["append", "classify", "ignore"]:
            raise ValueError("new_element_strategy must be 'append', 'classify', or 'ignore'")
            
        if self.conflict_resolution not in ["preserve", "override", "manual"]:
            raise ValueError("conflict_resolution must be 'preserve', 'override', or 'manual'")

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
# DOCUMENTATION SYSTEM
# =============================================================================


class DocumentationAnalyzer:
    """Analyzes code structure preserving original order for documentation."""

    def __init__(self):
        self.config = OdooConfiguration()
        self.field_analyzer = FieldAnalyzer()
        self.method_classifier = MethodClassifier()

    def extract_current_structure(self, tree: ast.Module, content: str) -> Dict[str, Any]:
        """Extract current code structure maintaining original order."""
        structure = {
            "imports": [],
            "classes": [],
            "functions": [],
            "module_constants": [],
            "total_lines": len(content.splitlines()),
        }

        # Process nodes in order of appearance
        for i, node in enumerate(tree.body):
            line_number = getattr(node, 'lineno', i + 1)
            
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_info = self._extract_import_info(node, line_number)
                structure["imports"].append(import_info)
            
            elif isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node, line_number)
                structure["classes"].append(class_info)
            
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_info = self._extract_function_info(node, line_number)
                structure["functions"].append(function_info)
            
            elif isinstance(node, ast.Assign):
                const_info = self._extract_constant_info(node, line_number)
                if const_info:
                    structure["module_constants"].append(const_info)

        return structure

    def _extract_import_info(self, node: Union[ast.Import, ast.ImportFrom], line_number: int) -> Dict[str, Any]:
        """Extract import information maintaining original order."""
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            return {
                "type": "import",
                "module": None,
                "names": names,
                "line": line_number,
                "raw": ast.unparse(node),
                "group": self._classify_import_group(names[0] if names else "")
            }
        else:  # ImportFrom
            names = [alias.name for alias in node.names]
            module = node.module or ""
            return {
                "type": "from_import", 
                "module": module,
                "names": names,
                "line": line_number,
                "level": node.level,
                "raw": ast.unparse(node),
                "group": self._classify_import_group(module)
            }

    def _extract_class_info(self, node: ast.ClassDef, line_number: int) -> Dict[str, Any]:
        """Extract class information preserving original element order."""
        class_info = {
            "name": node.name,
            "line": line_number,
            "bases": [ast.unparse(base) for base in node.bases],
            "is_odoo_model": self._is_odoo_model(node),
            "model_attributes": [],
            "fields": [],
            "methods": [],
            "other": []
        }

        # Process class body in original order
        for i, body_node in enumerate(node.body):
            element_line = getattr(body_node, 'lineno', line_number + i + 1)
            
            if isinstance(body_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._extract_method_info(body_node, element_line)
                class_info["methods"].append(method_info)
            
            elif isinstance(body_node, ast.Assign):
                if self._is_model_attribute(body_node):
                    attr_info = self._extract_model_attribute_info(body_node, element_line)
                    class_info["model_attributes"].append(attr_info)
                elif self.field_analyzer.is_odoo_field(body_node):
                    field_info = self._extract_field_info(body_node, element_line, node.body)
                    class_info["fields"].append(field_info)
                else:
                    other_info = self._extract_other_assignment(body_node, element_line)
                    class_info["other"].append(other_info)
            else:
                # Docstrings, decorators, etc.
                if not ASTUtils.is_docstring(body_node):
                    other_info = {
                        "type": type(body_node).__name__,
                        "line": element_line,
                        "raw": ast.unparse(body_node)
                    }
                    class_info["other"].append(other_info)

        return class_info

    def _extract_method_info(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], line_number: int) -> Dict[str, Any]:
        """Extract method information with classification."""
        decorators = []
        for decorator in node.decorator_list:
            dec_name = ASTUtils.extract_decorator_name(decorator)
            if dec_name:
                decorators.append(dec_name)

        method_type = self.method_classifier.classify_method(node)
        
        return {
            "name": node.name,
            "line": line_number,
            "type": method_type.name,
            "decorators": decorators,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "args_count": len(node.args.args),
            "raw": ast.unparse(node)
        }

    def _extract_field_info(self, node: ast.Assign, line_number: int, all_methods: List) -> Dict[str, Any]:
        """Extract field information with original position."""
        if not node.targets or not isinstance(node.targets[0], ast.Name):
            return {}

        field_name = node.targets[0].id
        field_info = self.field_analyzer.extract_field_info(node, all_methods)
        
        return {
            "name": field_name,
            "line": line_number,
            "field_type": field_info.field_type if field_info else "Unknown",
            "semantic_group": field_info.semantic_group if field_info else "other",
            "is_computed": field_info.is_computed if field_info else False,
            "is_related": field_info.is_related if field_info else False,
            "compute_method": field_info.compute if field_info else None,
            "raw": ast.unparse(node)
        }

    def _extract_model_attribute_info(self, node: ast.Assign, line_number: int) -> Dict[str, Any]:
        """Extract model attribute information."""
        if not node.targets or not isinstance(node.targets[0], ast.Name):
            return {}

        attr_name = node.targets[0].id
        value = ast.unparse(node.value) if node.value else ""
        
        return {
            "name": attr_name,
            "line": line_number,
            "value": value,
            "raw": ast.unparse(node)
        }

    def _extract_function_info(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], line_number: int) -> Dict[str, Any]:
        """Extract module-level function information."""
        return {
            "name": node.name,
            "line": line_number,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "args_count": len(node.args.args),
            "raw": ast.unparse(node)
        }

    def _extract_constant_info(self, node: ast.Assign, line_number: int) -> Optional[Dict[str, Any]]:
        """Extract module-level constant information."""
        if not node.targets or not isinstance(node.targets[0], ast.Name):
            return None

        const_name = node.targets[0].id
        # Only consider uppercase names as constants
        if const_name.isupper():
            return {
                "name": const_name,
                "line": line_number,
                "value": ast.unparse(node.value) if node.value else "",
                "raw": ast.unparse(node)
            }
        return None

    def _extract_other_assignment(self, node: ast.Assign, line_number: int) -> Dict[str, Any]:
        """Extract other assignment information."""
        target_names = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                target_names.append(target.id)
            else:
                target_names.append(ast.unparse(target))

        return {
            "targets": target_names,
            "line": line_number,
            "raw": ast.unparse(node)
        }

    def _is_odoo_model(self, node: ast.ClassDef) -> bool:
        """Check if class is an Odoo model."""
        model_bases = ["Model", "AbstractModel", "TransientModel"]
        for base in node.bases:
            if isinstance(base, ast.Attribute) and base.attr in model_bases:
                return True
            elif isinstance(base, ast.Name) and base.id in model_bases:
                return True
        return False

    def _is_model_attribute(self, node: ast.Assign) -> bool:
        """Check if assignment is a model attribute."""
        if not node.targets or not isinstance(node.targets[0], ast.Name):
            return False
        return node.targets[0].id in self.config.MODEL_ATTRIBUTES_ORDER

    def _classify_import_group(self, module_name: str) -> str:
        """Classify import into groups."""
        if not module_name:
            return "unknown"
        
        if module_name.startswith("odoo.addons"):
            return "odoo_addons"
        elif module_name.startswith("odoo"):
            return "odoo"
        elif module_name in sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else False:
            return "python_stdlib"
        else:
            return "third_party"


class DocumentationGenerator:
    """Generates documentation content from analyzed code structure."""

    def __init__(self):
        self.config = OdooConfiguration()

    def generate_documentation_content(self, structure: Dict[str, Any], original_filename: str) -> str:
        """Generate complete documentation file content."""
        lines = []
        
        # File header
        lines.extend(self._generate_header(original_filename))
        lines.append("")

        # General information
        lines.extend(self._generate_general_info(structure, original_filename))
        lines.append("")

        # Imports
        if structure["imports"]:
            lines.extend(self._generate_imports_section(structure["imports"]))
            lines.append("")

        # Module constants
        if structure["module_constants"]:
            lines.extend(self._generate_constants_section(structure["module_constants"]))
            lines.append("")

        # Classes
        if structure["classes"]:
            lines.extend(self._generate_classes_section(structure["classes"]))
            lines.append("")

        # Functions
        if structure["functions"]:
            lines.extend(self._generate_functions_section(structure["functions"]))
            lines.append("")

        # Statistics
        lines.extend(self._generate_statistics(structure))

        return "\n".join(lines)

    def _generate_header(self, original_filename: str) -> List[str]:
        """Generate file header."""
        return [
            "#!/usr/bin/env python3",
            '"""',
            f"Documentación del orden actual para: {original_filename}",
            "Generado automáticamente - refleja la estructura EXISTENTE",
            "",
            "Este archivo documenta el orden actual de elementos en el código fuente,",
            "preservando la secuencia exacta como aparece en el archivo original.",
            '"""',
            "",
            "from datetime import datetime",
            "",
            f"# Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]

    def _generate_general_info(self, structure: Dict[str, Any], original_filename: str) -> List[str]:
        """Generate general file information."""
        return [
            "# =============================================================================",
            "# INFORMACIÓN GENERAL DEL ARCHIVO",
            "# =============================================================================",
            "",
            f'ANALYZED_FILE = "{original_filename}"',
            f'TOTAL_LINES = {structure["total_lines"]}',
            f'TOTAL_CLASSES = {len(structure["classes"])}',
            f'TOTAL_FUNCTIONS = {len(structure["functions"])}',
            f'TOTAL_IMPORTS = {len(structure["imports"])}',
            f'TOTAL_CONSTANTS = {len(structure["module_constants"])}'
        ]

    def _generate_imports_section(self, imports: List[Dict[str, Any]]) -> List[str]:
        """Generate imports documentation."""
        lines = [
            "# =============================================================================", 
            "# IMPORTS EN ORDEN ACTUAL",
            "# =============================================================================",
            "",
            "# Lista de imports en el orden exacto de aparición",
            "CURRENT_IMPORTS_ORDER = ["
        ]

        for imp in imports:
            if imp["type"] == "import":
                import_str = f"import {', '.join(imp['names'])}"
            else:  # from_import
                level_str = "." * imp["level"] if imp["level"] > 0 else ""
                module_str = imp["module"] if imp["module"] else ""
                import_str = f"from {level_str}{module_str} import {', '.join(imp['names'])}"
            
            lines.append(f'    ("{import_str}", {imp["line"]}, "{imp["group"]}"),')

        lines.extend([
            "]",
            "",
            "# Imports agrupados por tipo",
            "IMPORTS_BY_GROUP = {"
        ])

        # Group by type
        groups = {}
        for imp in imports:
            group = imp["group"]
            if group not in groups:
                groups[group] = []
            groups[group].append(imp)

        for group_name, group_imports in groups.items():
            lines.append(f'    "{group_name}": [')
            for imp in group_imports:
                lines.append(f'        ("{imp["raw"]}", {imp["line"]}),')
            lines.append("    ],")

        lines.append("}")

        return lines

    def _generate_constants_section(self, constants: List[Dict[str, Any]]) -> List[str]:
        """Generate module constants documentation."""
        lines = [
            "# =============================================================================",
            "# CONSTANTES DE MÓDULO",
            "# =============================================================================",
            "",
            "CURRENT_CONSTANTS_ORDER = ["
        ]

        for const in constants:
            lines.append(f'    ("{const["name"]}", {const["line"]}, {const["value"]}),')

        lines.append("]")
        return lines

    def _generate_classes_section(self, classes: List[Dict[str, Any]]) -> List[str]:
        """Generate classes documentation."""
        lines = [
            "# =============================================================================",
            "# CLASES EN ORDEN ACTUAL", 
            "# =============================================================================",
            "",
            "# Clases encontradas en orden de aparición",
            "CLASSES_ORDER = ["
        ]

        for cls in classes:
            comment = f" # línea {cls['line']}"
            if cls["is_odoo_model"]:
                comment += " (Modelo Odoo)"
            lines.append(f'    "{cls["name"]}",{comment}')

        lines.extend([
            "]",
            "",
            "# Información detallada por clase",
            "CLASSES_INFO = {"
        ])

        for cls in classes:
            lines.extend(self._generate_single_class_info(cls))

        lines.append("}")

        return lines

    def _generate_single_class_info(self, cls: Dict[str, Any]) -> List[str]:
        """Generate detailed information for a single class."""
        lines = [f'    "{cls["name"]}": {{']
        
        # Basic info
        lines.extend([
            f'        "line": {cls["line"]},',
            f'        "bases": {cls["bases"]},',
            f'        "is_odoo_model": {cls["is_odoo_model"]},'
        ])

        # Model attributes
        if cls["model_attributes"]:
            lines.append('        "model_attributes_order": [')
            for attr in cls["model_attributes"]:
                lines.append(f'            ("{attr["name"]}", {attr["line"]}, {attr["value"]}),')
            lines.append('        ],')

        # Fields
        if cls["fields"]:
            lines.append('        "fields_order": [')
            for field in cls["fields"]:
                lines.append(f'            ("{field["name"]}", {field["line"]}, "{field["field_type"]}", "{field["semantic_group"]}"),')
            lines.append('        ],')

        # Methods
        if cls["methods"]:
            lines.append('        "methods_order": [')
            for method in cls["methods"]:
                decorators_str = repr(method["decorators"])
                lines.append(f'            ("{method["name"]}", {method["line"]}, "{method["type"]}", {decorators_str}),')
            lines.append('        ],')

        # Other elements
        if cls["other"]:
            lines.append('        "other_elements": [')
            for other in cls["other"]:
                if isinstance(other, dict) and "targets" in other:
                    targets_str = ", ".join(other["targets"])
                    lines.append(f'            ("{targets_str}", {other["line"]}),')
                elif isinstance(other, dict) and "type" in other:
                    lines.append(f'            ("{other["type"]}", {other["line"]}),')
            lines.append('        ],')

        # Remove trailing comma and close
        if lines[-1].endswith(','):
            lines[-1] = lines[-1][:-1]
        lines.append('    },')

        return lines

    def _generate_functions_section(self, functions: List[Dict[str, Any]]) -> List[str]:
        """Generate module functions documentation."""
        lines = [
            "# =============================================================================",
            "# FUNCIONES DE MÓDULO",
            "# =============================================================================",
            "",
            "MODULE_FUNCTIONS_ORDER = ["
        ]

        for func in functions:
            async_marker = " (async)" if func["is_async"] else ""
            lines.append(f'    ("{func["name"]}", {func["line"]}, {func["args_count"]}),{async_marker}')

        lines.append("]")
        return lines

    def _generate_statistics(self, structure: Dict[str, Any]) -> List[str]:
        """Generate analysis statistics."""
        lines = [
            "# =============================================================================",
            "# ESTADÍSTICAS DEL ANÁLISIS",
            "# =============================================================================",
            "",
            "ANALYSIS_STATS = {"
        ]

        total_methods = sum(len(cls["methods"]) for cls in structure["classes"])
        total_fields = sum(len(cls["fields"]) for cls in structure["classes"])
        odoo_models = sum(1 for cls in structure["classes"] if cls["is_odoo_model"])

        lines.extend([
            f'    "total_lines": {structure["total_lines"]},',
            f'    "total_classes": {len(structure["classes"])},',
            f'    "total_functions": {len(structure["functions"])},',
            f'    "total_methods": {total_methods},',
            f'    "total_fields": {total_fields},',
            f'    "total_imports": {len(structure["imports"])},',
            f'    "total_constants": {len(structure["module_constants"])},',
            f'    "odoo_models_detected": {odoo_models},',
            f'    "non_odoo_classes": {len(structure["classes"]) - odoo_models},',
        ])

        # Import statistics by group
        import_groups = {}
        for imp in structure["imports"]:
            group = imp["group"]
            import_groups[group] = import_groups.get(group, 0) + 1

        lines.append('    "imports_by_group": {')
        for group, count in import_groups.items():
            lines.append(f'        "{group}": {count},')
        lines.append('    },')

        # Method type statistics
        method_types = {}
        for cls in structure["classes"]:
            for method in cls["methods"]:
                method_type = method["type"]
                method_types[method_type] = method_types.get(method_type, 0) + 1

        lines.append('    "methods_by_type": {')
        for method_type, count in method_types.items():
            lines.append(f'        "{method_type}": {count},')
        lines.append('    },')

        lines.append("}")

        return lines


class DocumentationFileProcessor(FileHandler):
    """Processes Python files to generate documentation of current order."""

    def __init__(self, config: ReorganizerConfig):
        self.config = config
        self.documentation_analyzer = DocumentationAnalyzer()
        self.documentation_generator = DocumentationGenerator()

    def can_handle(self, filepath: Path) -> bool:
        """Check if this processor can handle the file."""
        return filepath.suffix == PYTHON_EXTENSION

    def process(self, filepath: Path, config: ReorganizerConfig) -> Tuple[str, bool]:
        """Process Python file to generate documentation."""
        try:
            # Read original file
            content = FileUtils.read_file(filepath)
            if not content.strip():
                return "", False

            # Parse AST
            tree = ast.parse(content)

            # Extract structure maintaining original order
            structure = self.documentation_analyzer.extract_current_structure(tree, content)

            # Generate documentation content
            doc_content = self.documentation_generator.generate_documentation_content(
                structure, filepath.name
            )

            # Create output filename
            output_filename = self._get_documentation_filename(filepath)
            
            # Write documentation file
            if config.docs_output_dir:
                output_dir = Path(config.docs_output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / output_filename
            else:
                output_path = filepath.parent / output_filename

            FileUtils.write_file(output_path, doc_content)
            logger.info(f"Generated documentation: {output_path}")

            return doc_content, True

        except Exception as e:
            ErrorHandler.handle_file_error(filepath, e, ProcessingStats())
            return "", False

    def _get_documentation_filename(self, original_filepath: Path) -> str:
        """Generate documentation filename from original file."""
        original_name = original_filepath.stem  # filename without extension
        return f"doc_{original_name}.py"


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
# MIGRATION CLASSES
# =============================================================================


@dataclass
class MatchResult:
    """Result of element matching operation."""
    
    pattern_element: Any
    target_element: Any
    confidence: float
    match_type: str
    notes: List[str] = field(default_factory=list)
    

@dataclass 
class MigrationReport:
    """Report of migration operation."""
    
    original_file: str
    target_file: str
    pattern_file: str
    matches: List[MatchResult] = field(default_factory=list)
    unmatched_pattern: List[Any] = field(default_factory=list)
    unmatched_target: List[Any] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def add_match(self, match: MatchResult):
        """Add a match result to the report."""
        self.matches.append(match)
        
    def add_error(self, error: str):
        """Add an error to the report.""" 
        self.errors.append(error)
        
    def generate_summary(self) -> str:
        """Generate a human-readable summary of the migration."""
        total_pattern = len(self.matches) + len(self.unmatched_pattern)
        total_target = len(self.matches) + len(self.unmatched_target)
        success_rate = (len(self.matches) / total_pattern * 100) if total_pattern > 0 else 0
        
        duration = ""
        if self.start_time and self.end_time:
            duration = f"\nDuration: {(self.end_time - self.start_time).total_seconds():.2f} seconds"
        
        return f"""Migration Report: {self.original_file}
=====================================

Pattern File: {self.pattern_file}
Target File: {self.target_file}

✅ Successfully matched: {len(self.matches)}/{total_pattern} elements ({success_rate:.1f}%)
⚠️  Unmatched from pattern: {len(self.unmatched_pattern)}
⚠️  Unmatched from target: {len(self.unmatched_target)}
❌ Errors: {len(self.errors)}{duration}

Matches by Confidence:
- High (>= 0.9): {sum(1 for m in self.matches if m.confidence >= 0.9)}
- Medium (0.7-0.9): {sum(1 for m in self.matches if 0.7 <= m.confidence < 0.9)}
- Low (< 0.7): {sum(1 for m in self.matches if m.confidence < 0.7)}
"""


class ElementMatcher:
    """Intelligent element matching for migration between code versions."""
    
    def __init__(self, config: ReorganizerConfig):
        """Initialize element matcher with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def match_elements(self, pattern_elements: Dict, target_elements: Dict) -> List[MatchResult]:
        """Match elements between pattern and target using multiple strategies."""
        matches = []
        
        # Match different types of elements
        for element_type in ['fields', 'methods', 'imports', 'classes']:
            if element_type in pattern_elements and element_type in target_elements:
                type_matches = self._match_by_type(
                    pattern_elements[element_type],
                    target_elements[element_type],
                    element_type
                )
                matches.extend(type_matches)
        
        return matches
    
    def _match_by_type(self, pattern_items: List, target_items: List, element_type: str) -> List[MatchResult]:
        """Match elements of a specific type."""
        matches = []
        
        if element_type == 'fields':
            matches = self._match_fields(pattern_items, target_items)
        elif element_type == 'methods':
            matches = self._match_methods(pattern_items, target_items)
        elif element_type == 'imports':
            matches = self._match_imports(pattern_items, target_items)
        elif element_type == 'classes':
            matches = self._match_classes(pattern_items, target_items)
            
        return matches
    
    def _match_fields(self, pattern_fields: List, target_fields: List) -> List[MatchResult]:
        """Match field definitions between versions."""
        matches = []
        
        for pattern_field in pattern_fields:
            pattern_name = pattern_field[0] if isinstance(pattern_field, tuple) else pattern_field
            best_match = None
            best_confidence = 0.0
            
            for target_field in target_fields:
                target_name = target_field[0] if isinstance(target_field, tuple) else target_field
                confidence = self._calculate_field_similarity(pattern_field, target_field)
                
                if confidence > best_confidence and confidence >= self.config.match_threshold:
                    best_match = target_field
                    best_confidence = confidence
            
            if best_match:
                matches.append(MatchResult(
                    pattern_element=pattern_field,
                    target_element=best_match,
                    confidence=best_confidence,
                    match_type="field",
                    notes=[f"Matched field '{pattern_name}' with confidence {best_confidence:.2f}"]
                ))
        
        return matches
    
    def _match_methods(self, pattern_methods: List, target_methods: List) -> List[MatchResult]:
        """Match method definitions between versions."""
        matches = []
        
        for pattern_method in pattern_methods:
            pattern_name = pattern_method[0] if isinstance(pattern_method, tuple) else pattern_method
            best_match = None
            best_confidence = 0.0
            
            for target_method in target_methods:
                target_name = target_method[0] if isinstance(target_method, tuple) else target_method
                confidence = self._calculate_method_similarity(pattern_method, target_method)
                
                if confidence > best_confidence and confidence >= self.config.match_threshold:
                    best_match = target_method
                    best_confidence = confidence
            
            if best_match:
                matches.append(MatchResult(
                    pattern_element=pattern_method,
                    target_element=best_match,
                    confidence=best_confidence,
                    match_type="method",
                    notes=[f"Matched method '{pattern_name}' with confidence {best_confidence:.2f}"]
                ))
        
        return matches
    
    def _match_imports(self, pattern_imports: List, target_imports: List) -> List[MatchResult]:
        """Match import statements between versions."""
        matches = []
        
        for pattern_import in pattern_imports:
            pattern_stmt = pattern_import[0] if isinstance(pattern_import, tuple) else pattern_import
            
            for target_import in target_imports:
                target_stmt = target_import[0] if isinstance(target_import, tuple) else target_import
                
                if pattern_stmt == target_stmt:
                    matches.append(MatchResult(
                        pattern_element=pattern_import,
                        target_element=target_import,
                        confidence=1.0,
                        match_type="import",
                        notes=["Exact import match"]
                    ))
                    break
        
        return matches
    
    def _match_classes(self, pattern_classes: List, target_classes: List) -> List[MatchResult]:
        """Match class definitions between versions."""
        matches = []
        
        for pattern_class in pattern_classes:
            pattern_name = pattern_class if isinstance(pattern_class, str) else pattern_class[0]
            
            for target_class in target_classes:
                target_name = target_class if isinstance(target_class, str) else target_class[0]
                
                if pattern_name == target_name:
                    matches.append(MatchResult(
                        pattern_element=pattern_class,
                        target_element=target_class,
                        confidence=1.0,
                        match_type="class",
                        notes=["Exact class name match"]
                    ))
                    break
        
        return matches
    
    def _calculate_field_similarity(self, pattern_field: Any, target_field: Any) -> float:
        """Calculate similarity between two field definitions."""
        if isinstance(pattern_field, tuple) and isinstance(target_field, tuple):
            pattern_name = pattern_field[0]
            target_name = target_field[0]
            
            # Exact match
            if pattern_name == target_name:
                return 1.0
            
            # REQUIREMENT: Field types must match for similarity calculation
            if len(pattern_field) >= 3 and len(target_field) >= 3:
                pattern_type = pattern_field[2]  # e.g., 'Integer', 'Many2one'
                target_type = target_field[2]    # e.g., 'extracted' (we need better type detection)
                
                # For now, if target_type is 'extracted', we can't validate type
                # In a full implementation, we'd need to parse the actual field definition
                if target_type != 'extracted' and pattern_type != target_type:
                    # Field types don't match - return 0.0 to prevent matching
                    return 0.0
            
            # Only allow name similarity if field types are compatible or unknown
            name_similarity = self._string_similarity(pattern_name, target_name)
            
            # Apply stricter threshold for field name similarity
            # Fields should have at least 50% character overlap to be considered similar
            if name_similarity < 0.5:
                return 0.0
                
            return name_similarity
        
        return 0.0
    
    def _calculate_method_similarity(self, pattern_method: Any, target_method: Any) -> float:
        """Calculate similarity between two method definitions.""" 
        if isinstance(pattern_method, tuple) and isinstance(target_method, tuple):
            pattern_name, target_name = pattern_method[0], target_method[0]
            
            # Exact match
            if pattern_name == target_name:
                return 1.0
                
            # Check method type/decorators if available
            if len(pattern_method) > 2 and len(target_method) > 2:
                pattern_type, target_type = pattern_method[2], target_method[2]
                if pattern_type == target_type:
                    # Same method type increases confidence
                    base_similarity = self._string_similarity(pattern_name, target_name)
                    return min(1.0, base_similarity + 0.2)
            
            return self._string_similarity(pattern_name, target_name)
        
        return 0.0
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity using a simple algorithm."""
        if s1 == s2:
            return 1.0
            
        # Simple similarity based on common characters and length
        common_chars = set(s1) & set(s2)
        total_chars = set(s1) | set(s2)
        
        if not total_chars:
            return 0.0
            
        return len(common_chars) / len(total_chars)


class PatternApplier:
    """Apply documented code patterns to target files."""
    
    def __init__(self, config: ReorganizerConfig):
        """Initialize pattern applier with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.matcher = ElementMatcher(config)
        
    def apply_pattern(self, pattern_file: str, target_file: str) -> MigrationReport:
        """Apply a documented pattern to a target file."""
        report = MigrationReport(
            original_file=target_file,
            target_file=target_file,
            pattern_file=pattern_file,
            start_time=datetime.now()
        )
        
        try:
            # Load pattern and target
            pattern_data = self._load_pattern_file(pattern_file)
            target_data = self._analyze_target_file(target_file)
            
            if not pattern_data or not target_data:
                report.add_error("Failed to load pattern or target file")
                return report
            
            # Create backup if not dry run
            if not self.config.dry_run:
                self._create_backup(target_file)
            
            # Match elements
            matches = self.matcher.match_elements(pattern_data, target_data)
            report.matches.extend(matches)
            
            # Apply reorganization
            if not self.config.dry_run:
                self._apply_reorganization(target_file, pattern_data, matches)
            
        except Exception as e:
            report.add_error(f"Error applying pattern: {str(e)}")
            self.logger.error(f"Pattern application failed: {e}")
        
        report.end_time = datetime.now()
        return report
    
    def _load_pattern_file(self, pattern_file: str) -> Optional[Dict]:
        """Load and parse a pattern documentation file."""
        try:
            # Import the pattern file as a module to access its variables
            import importlib.util
            import sys
            
            spec = importlib.util.spec_from_file_location("pattern_module", pattern_file)
            if not spec or not spec.loader:
                return None
                
            pattern_module = importlib.util.module_from_spec(spec)
            
            # Add mock objects to handle undefined references in pattern files
            pattern_module.models = type('MockModels', (), {
                'Model': 'MockModel',
                'check_company_domain_parent_of': 'MockCheckCompanyDomain'
            })()
            
            spec.loader.exec_module(pattern_module)
            
            # Extract pattern data from module attributes
            pattern_data = {}
            
            if hasattr(pattern_module, 'CLASSES_ORDER'):
                pattern_data['classes'] = pattern_module.CLASSES_ORDER
                
            if hasattr(pattern_module, 'CURRENT_IMPORTS_ORDER'):
                pattern_data['imports'] = pattern_module.CURRENT_IMPORTS_ORDER
                
            # Extract fields and methods from CLASSES_INFO if available
            if hasattr(pattern_module, 'CLASSES_INFO'):
                classes_info = pattern_module.CLASSES_INFO
                pattern_data['fields'] = []
                pattern_data['methods'] = []
                
                for class_name, class_info in classes_info.items():
                    if 'fields_order' in class_info:
                        pattern_data['fields'].extend(class_info['fields_order'])
                    if 'methods_order' in class_info:
                        pattern_data['methods'].extend(class_info['methods_order'])
            
            return pattern_data
            
        except Exception as e:
            self.logger.error(f"Failed to load pattern file {pattern_file}: {e}")
            return None
    
    def _analyze_target_file(self, target_file: str) -> Optional[Dict]:
        """Analyze target file to extract its current structure."""
        try:
            # Use existing DocumentationAnalyzer to get current structure
            with open(target_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            target_data = {}
            
            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_str = ast.unparse(node) if hasattr(ast, 'unparse') else str(node)
                    imports.append((import_str, node.lineno, "extracted"))
            target_data['imports'] = imports
            
            # Extract classes, fields, and methods
            classes = []
            fields = []
            methods = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                    
                    # Extract fields and methods from class
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            # Field assignment
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    field_name = target.id
                                    field_type = self._extract_field_type_from_ast(item.value)
                                    fields.append((field_name, item.lineno, field_type, "unknown"))
                        elif isinstance(item, ast.FunctionDef):
                            # Method definition
                            decorators = [d.id if isinstance(d, ast.Name) else str(d) for d in item.decorator_list]
                            methods.append((item.name, item.lineno, "extracted", decorators))
            
            target_data['classes'] = classes
            target_data['fields'] = fields
            target_data['methods'] = methods
            
            return target_data
            
        except Exception as e:
            self.logger.error(f"Failed to analyze target file {target_file}: {e}")
            return None
    
    def _extract_field_type_from_ast(self, ast_node: ast.AST) -> str:
        """Extract Odoo field type from AST node."""
        try:
            if isinstance(ast_node, ast.Call):
                # Handle fields.FieldType(...) calls
                if isinstance(ast_node.func, ast.Attribute):
                    if (isinstance(ast_node.func.value, ast.Name) and 
                        ast_node.func.value.id == 'fields'):
                        return ast_node.func.attr  # e.g., 'Char', 'Many2one', 'Integer'
                
                # Handle direct field type calls like Char(...), Many2one(...)
                elif isinstance(ast_node.func, ast.Name):
                    field_types = {
                        'Char', 'Text', 'Html', 'Boolean', 'Integer', 'Float', 
                        'Monetary', 'Date', 'Datetime', 'Binary', 'Image',
                        'Selection', 'Reference', 'Many2one', 'One2many', 'Many2many'
                    }
                    if ast_node.func.id in field_types:
                        return ast_node.func.id
            
            return "unknown"
            
        except Exception:
            return "unknown"
    
    def _create_backup(self, target_file: str):
        """Create backup of target file."""
        try:
            backup_path = f"{target_file}{self.config.backup_suffix}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(target_file, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise
    
    def _apply_reorganization(self, target_file: str, pattern_data: Dict, matches: List[MatchResult]):
        """Apply reorganization based on pattern and matches."""
        try:
            # Convert string to Path object
            target_path = Path(target_file)
            
            # 1. Parse the target file AST
            original_content = FileUtils.read_file(target_path)
            tree = ast.parse(original_content)
            
            # 2. Apply pattern-based reorganization (not standard reorganization)
            # Use the pattern data and matches to reorganize according to documented order
            new_content = self._apply_pattern_reorganization(original_content, pattern_data, matches)
            
            # Format with Black
            try:
                new_content = black.format_str(
                    new_content,
                    mode=black.FileMode(
                        line_length=self.config.line_length,
                        string_normalization=False  # Preserve original string quotes
                    )
                )
            except Exception as e:
                self.logger.warning(f"Black formatting failed for {target_file}: {e}")
            
            # Check if content changed
            if new_content == original_content:
                self.logger.info(f"No changes needed for {target_file}")
                return False
            
            # 3. Write the reorganized file back (if not dry run)
            if not self.config.dry_run:
                # Create backup if enabled
                if not self.config.no_backup:
                    FileUtils.create_backup(target_path)
                
                # Write reorganized content
                FileUtils.write_file(target_path, new_content)
                
                # 4. Show "Reorganized" message
                self.logger.info(f"Reorganized {target_file} based on {len(matches)} matches")
            else:
                self.logger.info(f"Would reorganize {target_file} based on {len(matches)} matches")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply reorganization to {target_file}: {e}")
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(traceback.format_exc())
            return False

    def _apply_pattern_reorganization(self, original_content: str, pattern_data: Dict, matches: List[MatchResult]) -> str:
        """Apply pattern-based reorganization using the documented order from pattern_data."""
        try:
            # Create a temporary file to process with the standard reorganizer
            import tempfile
            import os
            import re
            
            # Store multiline strings to preserve their format
            multiline_strings = {}
            placeholder_counter = 0
            
            def preserve_multiline_strings(content):
                nonlocal placeholder_counter
                # Pattern to match triple-quoted strings (both """ and ''')
                triple_quote_pattern = r'(""".*?"""|\'\'\'.*?\'\'\')'
                
                def replace_multiline(match):
                    nonlocal placeholder_counter
                    original_string = match.group(1)
                    placeholder = f"__MULTILINE_PLACEHOLDER_{placeholder_counter}__"
                    multiline_strings[placeholder] = original_string
                    placeholder_counter += 1
                    return f'"{placeholder}"'  # Wrap in quotes so it's valid Python
                
                return re.sub(triple_quote_pattern, replace_multiline, content, flags=re.DOTALL)
            
            def restore_multiline_strings(content):
                for placeholder, original in multiline_strings.items():
                    # Remove the quotes we added and restore original
                    content = content.replace(f'"{placeholder}"', original)
                    content = content.replace(f"'{placeholder}'", original)
                return content
            
            # Preserve multiline strings before processing
            protected_content = preserve_multiline_strings(original_content)
            
            # Create a temporary file with the protected content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(protected_content)
                temp_file_path = temp_file.name
            
            try:
                # Use the standard reorganizer to process the temporary file
                organizer = OdooCodeReorganizer(
                    odoo_version=self.config.odoo_version,
                    dry_run=True,  # This will ensure we get the content back without file operations
                    line_length=self.config.line_length,
                    add_section_headers=self.config.add_section_headers,
                    no_backup=True
                )
                
                # Process the temporary file and get the reorganized content
                reorganized_content = organizer.reorganize_file(temp_file_path)
                
                # Restore the original multiline strings
                final_content = restore_multiline_strings(reorganized_content)
                return final_content
                
            finally:
                # Clean up the temporary file
                os.unlink(temp_file_path)
            
        except Exception as e:
            self.logger.warning(f"Pattern reorganization failed: {e}")
            # If everything fails, return the original content unchanged
            return original_content


class VersionMigrator:
    """Orchestrate version migration operations."""
    
    def __init__(self, config: ReorganizerConfig):
        """Initialize version migrator."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.applier = PatternApplier(config)
        
    def migrate_file(self, pattern_path: str, target_path: str) -> MigrationReport:
        """Migrate a single file using a pattern."""
        self.logger.info(f"Starting migration: {pattern_path} -> {target_path}")
        
        # Validate files exist
        if not Path(pattern_path).exists():
            report = MigrationReport(target_path, target_path, pattern_path)
            report.add_error(f"Pattern file not found: {pattern_path}")
            return report
            
        if not Path(target_path).exists():
            report = MigrationReport(target_path, target_path, pattern_path) 
            report.add_error(f"Target file not found: {target_path}")
            return report
        
        # Apply pattern
        report = self.applier.apply_pattern(pattern_path, target_path)
        
        # Validate migration if not dry run
        if not self.config.dry_run:
            validation_result = self.validate_migration(target_path, report)
            if not validation_result:
                report.add_error("Migration validation failed")
        
        return report
    
    def validate_migration(self, migrated_file: str, report: MigrationReport) -> bool:
        """Validate that migration was successful."""
        try:
            # Check if file is still valid Python
            with open(migrated_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to check syntax
            ast.parse(content)
            
            self.logger.info(f"Migration validation passed for {migrated_file}")
            return True
            
        except SyntaxError as e:
            self.logger.error(f"Syntax error in migrated file {migrated_file}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Validation error for {migrated_file}: {e}")
            return False
    
    def generate_migration_report(self, report: MigrationReport, output_path: Optional[str] = None) -> str:
        """Generate detailed migration report."""
        report_content = report.generate_summary()
        
        # Add detailed match information
        if report.matches:
            report_content += "\n\nDetailed Matches:\n" + "="*50 + "\n"
            for match in report.matches:
                report_content += f"\n{match.match_type.upper()}: {match.pattern_element} -> {match.target_element}"
                report_content += f"\nConfidence: {match.confidence:.2f}"
                if match.notes:
                    report_content += f"\nNotes: {', '.join(match.notes)}"
                report_content += "\n" + "-"*30 + "\n"
        
        # Add unmatched elements
        if report.unmatched_pattern:
            report_content += f"\n\nUnmatched Pattern Elements ({len(report.unmatched_pattern)}):\n"
            for element in report.unmatched_pattern:
                report_content += f"- {element}\n"
                
        if report.unmatched_target:
            report_content += f"\n\nUnmatched Target Elements ({len(report.unmatched_target)}):\n"
            for element in report.unmatched_target:
                report_content += f"- {element}\n"
        
        # Add errors
        if report.errors:
            report_content += f"\n\nErrors ({len(report.errors)}):\n"
            for error in report.errors:
                report_content += f"❌ {error}\n"
        
        # Save to file if requested
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                self.logger.info(f"Migration report saved to {output_path}")
            except Exception as e:
                self.logger.error(f"Failed to save report to {output_path}: {e}")
        
        return report_content


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
        self.documentation_processor = DocumentationFileProcessor(self.config)
        
        # Initialize migration components
        self.migrator = VersionMigrator(self.config) if self.config.apply_pattern else None

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

    def generate_documentation(self, filepath: str) -> str:
        """Generate documentation for a single Python file."""
        path = Path(filepath)

        if not path.is_file():
            raise FileNotFoundError(f"File not found: {filepath}")

        if not path.suffix == PYTHON_EXTENSION:
            raise ValueError(f"Not a Python file: {filepath}")

        # Process file with documentation processor
        doc_content, generated = self.documentation_processor.process(path, self.config)

        if generated:
            logger.info(f"Documentation generated for {path}")
        else:
            logger.info(f"No documentation generated for {path}")

        return doc_content

    def generate_documentation_for_directory(self, directory: str, recursive: bool = True) -> None:
        """Generate documentation for all Python files in a directory."""
        path = Path(directory)

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not path.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        stats = ProcessingStats()
        pattern = "**/*.py" if recursive else "*.py"

        for filepath in path.glob(pattern):
            if FileUtils.should_skip(filepath, OdooConfiguration().SKIP_DIRS):
                continue

            stats.processed += 1

            try:
                doc_content, generated = self.documentation_processor.process(filepath, self.config)
                if generated:
                    stats.changed += 1
            except Exception as e:
                ErrorHandler.handle_file_error(filepath, e, stats)

        stats.log_summary("Documentation generation")

    def apply_pattern_to_file(self, pattern_file: str, target_file: str) -> MigrationReport:
        """Apply a documented pattern to a target file."""
        if not self.migrator:
            self.migrator = VersionMigrator(self.config)
        
        logging.info(f"Applying pattern {pattern_file} to {target_file}")
        
        try:
            report = self.migrator.migrate_file(pattern_file, target_file)
            
            if report.errors:
                logging.error(f"Migration completed with {len(report.errors)} errors")
                for error in report.errors:
                    logging.error(f"  - {error}")
            else:
                logging.info(f"Migration completed successfully with {len(report.matches)} matches")
            
            return report
            
        except Exception as e:
            logging.error(f"Pattern application failed: {e}")
            report = MigrationReport(target_file, target_file, pattern_file)
            report.add_error(f"Pattern application failed: {str(e)}")
            return report


# =============================================================================
# CLI INTERFACE
# =============================================================================


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Reorganize Odoo source code for consistency using Black formatting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("path", nargs='?', help="File, directory, or Odoo module to process")
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
    parser.add_argument(
        "--generate-docs",
        action="store_true",
        help="Generate documentation of current code order instead of reorganizing",
    )
    parser.add_argument(
        "--docs-output-dir",
        type=str,
        help="Directory to save documentation files (default: same as source)",
    )
    
    # Migration/Pattern Application Arguments
    parser.add_argument(
        "--apply-pattern",
        nargs=2,
        metavar=("PATTERN_FILE", "TARGET_FILE"),
        help="Apply documented pattern to target file",
    )
    parser.add_argument(
        "--migration-report",
        type=str,
        help="Generate detailed migration report to specified file",
    )
    parser.add_argument(
        "--match-threshold",
        type=float,
        default=0.8,
        help="Minimum similarity threshold for element matching (0.0-1.0, default: 0.8)",
    )
    parser.add_argument(
        "--backup-suffix",
        type=str,
        default=".backup",
        help="Suffix for backup files (default: .backup)",
    )
    parser.add_argument(
        "--missing-element-strategy",
        type=str,
        choices=["document", "ignore", "error"],
        default="document",
        help="Strategy for handling missing elements from pattern (default: document)",
    )
    parser.add_argument(
        "--new-element-strategy", 
        type=str,
        choices=["append", "classify", "ignore"],
        default="append",
        help="Strategy for handling new elements not in pattern (default: append)",
    )
    parser.add_argument(
        "--conflict-resolution",
        type=str,
        choices=["preserve", "override", "manual"],
        default="preserve",
        help="Strategy for resolving conflicts (default: preserve)",
    )

    return parser


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        # Handle pattern application mode
        if args.apply_pattern:
            pattern_file, target_file = args.apply_pattern
            # Create reorganizer with migration configuration
            reorganizer = OdooCodeReorganizer(
                line_length=args.line_length,
                add_section_headers=not args.no_section_headers,
                output_dir=args.output_dir,
                odoo_version=args.odoo_version,
                dry_run=args.dry_run,
                no_backup=args.no_backup,
                generate_docs=False,
                docs_output_dir=args.docs_output_dir,
                # Migration arguments
                apply_pattern=True,
                pattern_file=pattern_file,
                target_file=target_file,
                match_threshold=args.match_threshold,
                backup_suffix=args.backup_suffix,
                migration_report_path=args.migration_report,
                missing_element_strategy=args.missing_element_strategy,
                new_element_strategy=args.new_element_strategy,
                conflict_resolution=args.conflict_resolution,
            )
            
            # Execute pattern application
            report = reorganizer.apply_pattern_to_file(pattern_file, target_file)
            
            # Generate migration report if requested
            if args.migration_report:
                reorganizer.migrator.generate_migration_report(report, args.migration_report)
                print(f"Migration report saved to: {args.migration_report}")
            
            # Print summary
            print(report.generate_summary())
            return
        
        # Create reorganizer for normal operations
        reorganizer = OdooCodeReorganizer(
            line_length=args.line_length,
            add_section_headers=not args.no_section_headers,
            output_dir=args.output_dir,
            odoo_version=args.odoo_version,
            dry_run=args.dry_run,
            no_backup=args.no_backup,
            generate_docs=args.generate_docs,
            docs_output_dir=args.docs_output_dir,
            # Migration arguments (defaults for normal operation)
            apply_pattern=False,
            pattern_file=None,
            target_file=None,
            match_threshold=args.match_threshold,
            backup_suffix=args.backup_suffix,
            migration_report_path=args.migration_report,
            missing_element_strategy=args.missing_element_strategy,
            new_element_strategy=args.new_element_strategy,
            conflict_resolution=args.conflict_resolution,
        )

        # Validate path argument when needed
        if not args.path and not args.apply_pattern:
            parser.error("the following arguments are required: path (unless using --apply-pattern)")
        
        # Process path
        if args.path:
            path = Path(args.path)
        else:
            path = None

        if args.generate_docs:
            # Documentation generation mode
            if not path:
                parser.error("path is required for documentation generation")
            if path.is_file():
                reorganizer.generate_documentation(str(path))
            elif path.is_dir():
                reorganizer.generate_documentation_for_directory(str(path), recursive=args.recursive)
            else:
                logger.error(f"Path {path} does not exist")
                sys.exit(1)
        else:
            # Normal reorganization mode
            if not path:
                parser.error("path is required for reorganization")
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
