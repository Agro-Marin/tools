"""
Unit tests for order command
"""

import ast
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from core.base_processor import ProcessingStatus, ProcessResult
from src.commands.reorder import UnifiedReorderCommand
from src.core.config import Config, OrderingConfig


class TestUnifiedReorderCommand:
    """Test order command functionality"""

    def test_initialization(self):
        """Test order command initialization"""
        config = Config()
        config.ordering.strategy = "semantic"

        command = UnifiedReorderCommand(config)

        assert command.config == config
        assert command.backup_manager is not None

    def test_initialization_no_backup(self):
        """Test initialization without backup"""
        config = Config()
        config.backup.enabled = False

        command = UnifiedReorderCommand(config)

        assert command.backup_manager is None

    @patch("src.commands.order.Ordering")
    def test_execute_single_file(self, mock_ordering_class, tmp_path):
        """Test ordering a single Python file"""
        # Setup
        config = Config()
        config.ordering.strategy = "semantic"
        config.dry_run = False

        test_file = tmp_path / "test.py"
        test_file.write_text("def test():\n    pass")

        # Mock Ordering class
        mock_ordering = Mock()
        mock_ordering.order_file.return_value = ProcessResult(
            file_path=test_file,
            status=ProcessingStatus.SUCCESS,
            content="# Ordered\ndef test():\n    pass",
        )
        mock_ordering_class.return_value = mock_ordering

        # Execute
        command = UnifiedReorderCommand(config)
        success = command.execute("code", test_file)

        # Verify
        assert success is True
        mock_ordering.order_file.assert_called_once_with(test_file)

    @patch("src.commands.order.Ordering")
    def test_execute_directory_recursive(self, mock_ordering_class, tmp_path):
        """Test ordering a directory recursively"""
        # Setup directory structure
        config = Config()
        config.ordering.strategy = "type"
        config.ordering.recursive = True

        module_dir = tmp_path / "module"
        models_dir = module_dir / "models"
        models_dir.mkdir(parents=True)

        file1 = models_dir / "model1.py"
        file2 = models_dir / "model2.py"
        file1.write_text("class Model1:\n    pass")
        file2.write_text("class Model2:\n    pass")

        # Mock Ordering
        mock_ordering = Mock()
        mock_ordering.order_file.return_value = ProcessResult(
            file_path=file1, status=ProcessingStatus.SUCCESS
        )
        mock_ordering_class.return_value = mock_ordering

        # Execute
        command = UnifiedReorderCommand(config)
        success = command.execute("code", module_dir, recursive=True)

        # Verify
        assert success is True
        assert mock_ordering.order_file.call_count == 2

    @patch("src.commands.order.Ordering")
    def test_execute_with_backup(self, mock_ordering_class, tmp_path):
        """Test ordering with backup enabled"""
        # Setup
        config = Config()
        config.backup.enabled = True
        config.backup.directory = str(tmp_path / "backups")

        test_file = tmp_path / "test.py"
        test_file.write_text("original content")

        # Mock Ordering
        mock_ordering = Mock()
        mock_ordering.order_file.return_value = ProcessResult(
            file_path=test_file,
            status=ProcessingStatus.SUCCESS,
            content="ordered content",
        )
        mock_ordering_class.return_value = mock_ordering

        # Execute
        command = UnifiedReorderCommand(config)

        # Verify backup session is managed
        with patch.object(command.backup_manager, "start_session") as mock_start:
            with patch.object(command.backup_manager, "backup_file") as mock_backup:
                with patch.object(
                    command.backup_manager, "finalize_session"
                ) as mock_finalize:
                    success = command.execute("code", test_file)

                    mock_start.assert_called_once_with("code_ordering")
                    mock_backup.assert_called_once_with(test_file)
                    mock_finalize.assert_called_once()

    @patch("src.commands.order.Ordering")
    def test_execute_dry_run(self, mock_ordering_class, tmp_path):
        """Test dry run mode"""
        config = Config()
        config.dry_run = True

        test_file = tmp_path / "test.py"
        original_content = "def original():\n    pass"
        test_file.write_text(original_content)

        # Mock Ordering
        mock_ordering = Mock()
        mock_ordering.order_file.return_value = ProcessResult(
            file_path=test_file,
            status=ProcessingStatus.SUCCESS,
            content="def ordered():\n    pass",
        )
        mock_ordering_class.return_value = mock_ordering

        # Execute
        command = UnifiedReorderCommand(config)
        success = command.execute("code", test_file)

        # Verify file wasn't changed
        assert success is True
        assert test_file.read_text() == original_content

    @patch("src.commands.order.Ordering")
    def test_execute_with_errors(self, mock_ordering_class, tmp_path):
        """Test handling of ordering errors"""
        config = Config()

        test_file = tmp_path / "test.py"
        test_file.write_text("invalid python syntax {")

        # Mock Ordering with error
        mock_ordering = Mock()
        mock_ordering.order_file.return_value = ProcessResult(
            file_path=test_file,
            status=ProcessingStatus.ERROR,
            error_message="Syntax error",
        )
        mock_ordering_class.return_value = mock_ordering

        # Execute
        command = UnifiedReorderCommand(config)
        success = command.execute("code", test_file)

        # Should return False on error
        assert success is False

    @patch("src.commands.order.Ordering")
    @patch("subprocess.run")
    def test_execute_with_black_formatting(
        self, mock_subprocess, mock_ordering_class, tmp_path
    ):
        """Test Black formatting after ordering"""
        config = Config()
        config.ordering.apply_black = True
        config.ordering.black_line_length = 100

        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")

        # Mock Ordering
        mock_ordering = Mock()
        mock_ordering.order_file.return_value = ProcessResult(
            file_path=test_file,
            status=ProcessingStatus.SUCCESS,
            content="def test():\n    pass",
        )
        mock_ordering_class.return_value = mock_ordering

        # Mock subprocess for Black
        mock_subprocess.return_value = Mock(returncode=0)

        # Execute
        command = UnifiedReorderCommand(config)
        success = command.execute("code", test_file)

        # Verify Black was called with correct arguments
        mock_subprocess.assert_called_with(
            ["black", "-l", "100", str(test_file)], capture_output=True, text=True
        )

    @patch("src.commands.order.Ordering")
    @patch("subprocess.run")
    def test_execute_with_isort(self, mock_subprocess, mock_ordering_class, tmp_path):
        """Test isort formatting after ordering"""
        config = Config()
        config.ordering.apply_isort = True

        test_file = tmp_path / "test.py"
        test_file.write_text("import os\nimport sys")

        # Mock Ordering
        mock_ordering = Mock()
        mock_ordering.order_file.return_value = ProcessResult(
            file_path=test_file, status=ProcessingStatus.SUCCESS
        )
        mock_ordering_class.return_value = mock_ordering

        # Mock subprocess for isort
        mock_subprocess.return_value = Mock(returncode=0)

        # Execute
        command = UnifiedReorderCommand(config)
        success = command.execute("code", test_file)

        # Verify isort was called
        mock_subprocess.assert_called_with(
            ["isort", str(test_file)], capture_output=True, text=True
        )

    @patch("src.commands.order.Ordering")
    def test_execute_skip_init_files(self, mock_ordering_class, tmp_path):
        """Test that __init__.py files are skipped"""
        config = Config()

        init_file = tmp_path / "__init__.py"
        init_file.write_text("# Init file")

        # Execute
        command = UnifiedReorderCommand(config)
        success = command.execute("code", init_file)

        # Should skip __init__.py files
        assert success is True
        mock_ordering_class.assert_not_called()

    def test_find_python_files(self, tmp_path):
        """Test finding Python files in directory"""
        config = Config()
        command = UnifiedReorderCommand(config)

        # Create test structure
        (tmp_path / "models").mkdir()
        (tmp_path / "models" / "model.py").write_text("")
        (tmp_path / "models" / "__init__.py").write_text("")
        (tmp_path / "views").mkdir()
        (tmp_path / "views" / "view.xml").write_text("")
        (tmp_path / "test.py").write_text("")

        # Find files
        files = command._find_python_files(tmp_path, recursive=False)

        # Should find only top-level .py file (not __init__.py)
        assert len(files) == 1
        assert files[0].name == "test.py"

        # Test recursive
        files = command._find_python_files(tmp_path, recursive=True)

        # Should find all .py files except __init__.py
        assert len(files) == 2
        file_names = {f.name for f in files}
        assert "test.py" in file_names
        assert "model.py" in file_names
        assert "__init__.py" not in file_names

    @patch("src.commands.order.Ordering")
    def test_process_multiple_files_stats(self, mock_ordering_class, tmp_path):
        """Test statistics collection for multiple files"""
        config = Config()
        command = UnifiedReorderCommand(config)

        # Create test files
        file1 = tmp_path / "file1.py"
        file2 = tmp_path / "file2.py"
        file3 = tmp_path / "file3.py"

        for f in [file1, file2, file3]:
            f.write_text("pass")

        # Mock different results
        mock_ordering = Mock()
        mock_ordering.order_file.side_effect = [
            ProcessResult(file_path=file1, status=ProcessingStatus.SUCCESS),
            ProcessResult(file_path=file2, status=ProcessingStatus.NO_CHANGES),
            ProcessResult(
                file_path=file3, status=ProcessingStatus.ERROR, error_message="Error"
            ),
        ]
        mock_ordering_class.return_value = mock_ordering

        # Execute
        success = command.execute("code", tmp_path)

        # Should return False due to error
        assert success is False
        # Should process all files
        assert mock_ordering.order_file.call_count == 3
