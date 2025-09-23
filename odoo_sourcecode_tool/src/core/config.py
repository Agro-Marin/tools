"""
Unified configuration system for Odoo Tools
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class OrderingConfig:
    """Configuration for code ordering operations"""

    strategy: str = "semantic"  # semantic, type, or strict
    add_section_headers: bool = True
    black_line_length: int = 88
    magic_trailing_comma: bool = True
    preserve_comments: bool = True
    single_class_per_file: bool = True  # Enforce one model class per file
    check_file_naming: bool = True  # Check that file names match model names
    consolidate_menus: bool = True  # Enforce all menus in single menu.xml file
    menu_file_name: str = "menu.xml"  # Standard name for menu file

    # isort configuration
    isort_sections: list[str] = field(
        default_factory=lambda: [
            "FUTURE",
            "STDLIB",
            "THIRDPARTY",
            "ODOO",
            "ODOO_ADDONS",
            "FIRSTPARTY",
            "LOCALFOLDER",
        ]
    )
    isort_known_odoo: list[str] = field(default_factory=lambda: ["odoo", "openerp"])
    isort_known_odoo_addons: list[str] = field(default_factory=lambda: ["odoo.addons"])
    isort_combine_as_imports: bool = True
    isort_force_alphabetical_sort_within_sections: bool = True
    isort_force_sort_within_sections: bool = True
    isort_lines_between_sections: int = 1
    isort_multi_line_output: int = 3  # Vertical Hanging Indent
    isort_include_trailing_comma: bool = True
    isort_force_grid_wrap: int = 0
    isort_use_parentheses: bool = True
    isort_ensure_newline_before_comments: bool = True
    isort_line_length: int = 85

    def get_isort_config(self) -> dict[str, Any]:
        """Export isort configuration as keyword arguments dictionary"""
        return {
            "sections": self.isort_sections,
            "known_odoo": self.isort_known_odoo,
            "known_odoo_addons": self.isort_known_odoo_addons,
            "combine_as_imports": self.isort_combine_as_imports,
            "force_alphabetical_sort_within_sections": self.isort_force_alphabetical_sort_within_sections,
            "force_sort_within_sections": self.isort_force_sort_within_sections,
            "lines_between_sections": self.isort_lines_between_sections,
            "multi_line_output": self.isort_multi_line_output,
            "include_trailing_comma": self.isort_include_trailing_comma,
            "force_grid_wrap": self.isort_force_grid_wrap,
            "use_parentheses": self.isort_use_parentheses,
            "ensure_newline_before_comments": self.isort_ensure_newline_before_comments,
            "line_length": self.isort_line_length,
        }


@dataclass
class DetectionConfig:
    """Configuration for change detection operations"""

    confidence_threshold: float = 0.75
    auto_approve_threshold: float = 0.90
    include_methods: bool = True
    include_fields: bool = True
    analyze_xml: bool = True


@dataclass
class RenamingConfig:
    """Configuration for renaming operations"""

    validate_syntax: bool = True
    file_types: list[str] = field(default_factory=lambda: ["python", "xml", "yaml"])
    parallel_processing: bool = False
    max_workers: int = 4


@dataclass
class BackupConfig:
    """Configuration for backup operations"""

    enabled: bool = True
    directory: str = ".backups"
    compression: bool = True
    keep_sessions: int = 10


@dataclass
class Config:
    """Main configuration class for Odoo Tools"""

    # General settings
    repo_path: str | None = None
    interactive: bool = False
    dry_run: bool = False
    verbose: bool = False
    quiet: bool = False

    # Module filtering
    modules: list[str] = field(default_factory=list)

    # Sub-configurations
    ordering: OrderingConfig = field(default_factory=OrderingConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    renaming: RenamingConfig = field(default_factory=RenamingConfig)
    backup: BackupConfig = field(default_factory=BackupConfig)

    # File paths
    config_file: str | None = None
    output_dir: str = "output"

    @classmethod
    def from_file(cls, filepath: Path) -> "Config":
        """Load configuration from YAML or JSON file"""
        if not filepath.exists():
            logger.warning(f"Config file not found: {filepath}")
            return cls()

        try:
            with open(filepath, "r") as f:
                if filepath.suffix in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                elif filepath.suffix == ".json":
                    data = json.load(f)
                else:
                    logger.error(f"Unsupported config file format: {filepath.suffix}")
                    return cls()

            return cls._from_dict(data)
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            return cls()

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Config":
        """Create Config instance from dictionary"""
        config = cls()

        # Load general settings
        for key in [
            "repo_path",
            "interactive",
            "dry_run",
            "verbose",
            "quiet",
            "output_dir",
        ]:
            if key in data:
                setattr(config, key, data[key])

        # Load modules list
        if "modules" in data:
            config.modules = data["modules"]

        # Load sub-configurations
        if "ordering" in data:
            config.ordering = OrderingConfig(**data["ordering"])
        if "detection" in data:
            config.detection = DetectionConfig(**data["detection"])
        if "renaming" in data:
            config.renaming = RenamingConfig(**data["renaming"])
        if "backup" in data:
            config.backup = BackupConfig(**data["backup"])

        return config

    @classmethod
    def load_hierarchy(cls, project_dir: Path | None = None) -> "Config":
        """Load configuration from hierarchy: env vars -> global -> project -> cli"""
        config = cls()

        # 1. Load global config
        global_config = Path.home() / ".odoo-tools" / "config.yaml"
        if global_config.exists():
            config = cls.from_file(global_config)
            logger.debug(f"Loaded global config from {global_config}")

        # 2. Load project config
        if project_dir:
            project_config = project_dir / ".odoo-tools.yaml"
            if project_config.exists():
                project_data = cls.from_file(project_config)
                config.merge(project_data)
                logger.debug(f"Loaded project config from {project_config}")

        # 3. Apply environment variables
        config.apply_env_vars()

        return config

    def merge(self, other: "Config") -> None:
        """Merge another config into this one (other takes precedence)"""
        if other.repo_path:
            self.repo_path = other.repo_path
        if other.modules:
            self.modules = other.modules
        if other.config_file:
            self.config_file = other.config_file

        # Merge boolean flags (only if explicitly set to True)
        for flag in ["interactive", "dry_run", "verbose", "quiet"]:
            if getattr(other, flag):
                setattr(self, flag, True)

        # Merge sub-configurations
        self._merge_dataclass(self.ordering, other.ordering)
        self._merge_dataclass(self.detection, other.detection)
        self._merge_dataclass(self.renaming, other.renaming)
        self._merge_dataclass(self.backup, other.backup)

    def _merge_dataclass(self, target: Any, source: Any) -> None:
        """Merge source dataclass into target"""
        for field_name in source.__dataclass_fields__:
            source_value = getattr(source, field_name)
            if source_value != getattr(target.__class__(), field_name):
                setattr(target, field_name, source_value)

    def apply_env_vars(self) -> None:
        """Apply environment variables to configuration"""
        # ODOO_TOOLS_REPO_PATH
        if repo_path := os.environ.get("ODOO_TOOLS_REPO_PATH"):
            self.repo_path = repo_path

        # ODOO_TOOLS_INTERACTIVE
        if os.environ.get("ODOO_TOOLS_INTERACTIVE", "").lower() in ["true", "1", "yes"]:
            self.interactive = True

        # ODOO_TOOLS_DRY_RUN
        if os.environ.get("ODOO_TOOLS_DRY_RUN", "").lower() in ["true", "1", "yes"]:
            self.dry_run = True

        # ODOO_TOOLS_VERBOSE
        if os.environ.get("ODOO_TOOLS_VERBOSE", "").lower() in ["true", "1", "yes"]:
            self.verbose = True

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors"""
        errors = []

        # Validate repo path if specified
        if self.repo_path and not Path(self.repo_path).exists():
            errors.append(f"Repository path does not exist: {self.repo_path}")

        # Validate ordering strategy
        if self.ordering.strategy not in ["semantic", "type", "strict"]:
            errors.append(f"Invalid ordering strategy: {self.ordering.strategy}")

        # Validate thresholds
        if not 0 <= self.detection.confidence_threshold <= 1:
            errors.append("Confidence threshold must be between 0 and 1")
        if not 0 <= self.detection.auto_approve_threshold <= 1:
            errors.append("Auto-approve threshold must be between 0 and 1")

        # Validate file types
        valid_file_types = ["python", "xml", "yaml", "csv", "javascript"]
        for ft in self.renaming.file_types:
            if ft not in valid_file_types:
                errors.append(f"Invalid file type: {ft}")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "repo_path": self.repo_path,
            "interactive": self.interactive,
            "dry_run": self.dry_run,
            "verbose": self.verbose,
            "quiet": self.quiet,
            "modules": self.modules,
            "output_dir": self.output_dir,
            "ordering": asdict(self.ordering),
            "detection": asdict(self.detection),
            "renaming": asdict(self.renaming),
            "backup": asdict(self.backup),
        }

    def save(self, filepath: Path) -> None:
        """Save configuration to file"""
        data = self.to_dict()

        with open(filepath, "w") as f:
            if filepath.suffix in [".yaml", ".yml"]:
                yaml.safe_dump(data, f, default_flow_style=False)
            elif filepath.suffix == ".json":
                json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported config file format: {filepath.suffix}")
