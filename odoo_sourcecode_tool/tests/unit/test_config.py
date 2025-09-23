"""
Unit tests for configuration system
"""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml
from core.config import (
    BackupConfig,
    Config,
    DetectionConfig,
    OrderingConfig,
    RenamingConfig,
)


class TestConfig:
    """Test configuration functionality"""

    def test_default_config(self):
        """Test default configuration creation"""
        config = Config()

        assert config.repo_path is None
        assert config.interactive is False
        assert config.dry_run is False
        assert config.verbose is False
        assert config.quiet is False
        assert config.modules == []

        # Check sub-configurations
        assert isinstance(config.ordering, OrderingConfig)
        assert isinstance(config.detection, DetectionConfig)
        assert isinstance(config.renaming, RenamingConfig)
        assert isinstance(config.backup, BackupConfig)

    def test_ordering_config_defaults(self):
        """Test ordering configuration defaults"""
        config = OrderingConfig()

        assert config.add_section_headers is True
        assert config.black_line_length == 88
        assert config.magic_trailing_comma is True
        assert config.preserve_comments is True

    def test_detection_config_defaults(self):
        """Test detection configuration defaults"""
        config = DetectionConfig()

        assert config.confidence_threshold == 0.75
        assert config.auto_approve_threshold == 0.90
        assert config.include_methods is True
        assert config.include_fields is True
        assert config.analyze_xml is True

    def test_renaming_config_defaults(self):
        """Test renaming configuration defaults"""
        config = RenamingConfig()

        assert config.validate_syntax is True
        assert config.file_types == ["python", "xml", "yaml"]
        assert config.parallel_processing is False
        assert config.max_workers == 4

    def test_backup_config_defaults(self):
        """Test backup configuration defaults"""
        config = BackupConfig()

        assert config.enabled is True
        assert config.directory == ".backups"
        assert config.compression is True
        assert config.keep_sessions == 10

    def test_load_from_yaml(self, tmp_path):
        """Test loading configuration from YAML file"""
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            "repo_path": "/test/repo",
            "interactive": True,
            "modules": ["sale", "purchase"],
            "ordering": {"black_line_length": 120},
            "detection": {"confidence_threshold": 0.6},
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = Config.from_file(config_file)

        assert config.repo_path == "/test/repo"
        assert config.interactive is True
        assert config.modules == ["sale", "purchase"]
        assert config.ordering.black_line_length == 120
        assert config.detection.confidence_threshold == 0.6

    def test_load_from_json(self, tmp_path):
        """Test loading configuration from JSON file"""
        config_file = tmp_path / "test_config.json"
        config_data = {
            "repo_path": "/test/repo",
            "dry_run": True,
            "backup": {"enabled": False, "keep_sessions": 5},
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = Config.from_file(config_file)

        assert config.repo_path == "/test/repo"
        assert config.dry_run is True
        assert config.backup.enabled is False
        assert config.backup.keep_sessions == 5

    def test_merge_configs(self):
        """Test merging configurations"""
        config1 = Config()
        config2 = Config()

        config2.repo_path = "/new/repo"
        config2.interactive = True

        config1.merge(config2)

        assert config1.repo_path == "/new/repo"
        assert config1.interactive is True

    def test_environment_variables(self):
        """Test environment variable application"""
        # Set environment variables
        os.environ["ODOO_TOOLS_REPO_PATH"] = "/env/repo"
        os.environ["ODOO_TOOLS_INTERACTIVE"] = "true"
        os.environ["ODOO_TOOLS_DRY_RUN"] = "1"
        os.environ["ODOO_TOOLS_VERBOSE"] = "yes"

        try:
            config = Config()
            config.apply_env_vars()

            assert config.repo_path == "/env/repo"
            assert config.interactive is True
            assert config.dry_run is True
            assert config.verbose is True
        finally:
            # Clean up environment
            for key in [
                "ODOO_TOOLS_REPO_PATH",
                "ODOO_TOOLS_INTERACTIVE",
                "ODOO_TOOLS_DRY_RUN",
                "ODOO_TOOLS_VERBOSE",
            ]:
                if key in os.environ:
                    del os.environ[key]

    def test_validation(self, tmp_path):
        """Test configuration validation"""
        config = Config()

        # Valid configuration
        config.repo_path = str(tmp_path)
        errors = config.validate()
        assert len(errors) == 0

        # Invalid repo path
        config.repo_path = "/nonexistent/path"
        errors = config.validate()
        assert any("Repository path does not exist" in e for e in errors)

        # Invalid file types
        config.detection.confidence_threshold = 0.75
        config.renaming.file_types = ["python", "invalid_type"]
        errors = config.validate()
        assert any("Invalid file type: invalid_type" in e for e in errors)

    def test_save_config(self, tmp_path):
        """Test saving configuration to file"""
        config = Config()
        config.repo_path = "/test/repo"
        config.modules = ["sale"]

        # Save to YAML
        yaml_file = tmp_path / "saved_config.yaml"
        config.save(yaml_file)

        # Load and verify
        loaded_config = Config.from_file(yaml_file)
        assert loaded_config.repo_path == "/test/repo"
        assert loaded_config.modules == ["sale"]

        # Save to JSON
        json_file = tmp_path / "saved_config.json"
        config.save(json_file)

        # Load and verify
        loaded_config = Config.from_file(json_file)
        assert loaded_config.repo_path == "/test/repo"
        assert loaded_config.modules == ["sale"]

    def test_hierarchy_loading(self, tmp_path, monkeypatch):
        """Test hierarchical configuration loading"""
        # Create global config directory
        global_dir = tmp_path / ".odoo-tools"
        global_dir.mkdir()
        global_config = global_dir / "config.yaml"

        with open(global_config, "w") as f:
            yaml.dump({"repo_path": "/global/repo", "verbose": True}, f)

        # Create project config
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        project_config = project_dir / ".odoo-tools.yaml"

        with open(project_config, "w") as f:
            yaml.dump({"repo_path": "/project/repo", "interactive": True}, f)

        # Mock home directory
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        # Load hierarchy
        config = Config.load_hierarchy(project_dir)

        # Project config should override global
        assert config.repo_path == "/project/repo"
        # Global settings should be preserved if not overridden
        assert config.verbose is True
        # Project-specific settings
        assert config.interactive is True
