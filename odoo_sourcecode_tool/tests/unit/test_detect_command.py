"""
Unit tests for detect command
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest
from git import Repo
from src.commands.detect import DetectCommand, RenameCandidate
from src.core.config import Config, DetectionConfig
from src.core.ordering import FieldInfo, MethodInfo, Ordering


class TestDetectCommand:
    """Test detect command functionality"""

    def test_initialization(self):
        """Test detect command initialization"""
        config = Config()
        config.repo_path = "/test/repo"

        with patch("src.commands.detect.GitManager"):
            command = DetectCommand(config)

            assert command.config == config
            assert command.ast_parser is not None

    @patch("src.commands.detect.GitManager")
    def test_execute_basic(self, mock_git_manager_class, tmp_path):
        """Test basic detection between commits"""
        # Setup
        config = Config()
        config.repo_path = str(tmp_path)
        config.detection.confidence_threshold = 0.7

        # Mock GitManager
        mock_git_manager = Mock()
        mock_git_manager.resolve_commit.side_effect = lambda x: f"sha_{x}"
        mock_git_manager.get_modified_files.return_value = ["module/models/model.py"]
        mock_git_manager.get_file_content_at_commit.side_effect = lambda f, c: {
            ("module/models/model.py", "sha_HEAD~1"): "old_field = fields.Char()",
            ("module/models/model.py", "sha_HEAD"): "new_field = fields.Char()",
        }.get((f, c), "")
        mock_git_manager_class.return_value = mock_git_manager

        # Execute
        command = DetectCommand(config)
        candidates = command.execute("HEAD~1", "HEAD")

        # Verify
        assert isinstance(candidates, list)
        mock_git_manager.get_modified_files.assert_called_once()

    @patch("src.commands.detect.GitManager")
    def test_extract_inventory(self, mock_git_manager_class, tmp_path):
        """Test inventory extraction from commits"""
        config = Config()
        config.repo_path = str(tmp_path)

        # Mock GitManager
        mock_git_manager = Mock()
        mock_git_manager.get_modified_files.return_value = ["sale/models/sale_order.py"]
        mock_git_manager.get_file_content_at_commit.return_value = """
class SaleOrder(models.Model):
    _name = 'sale.order'
    
    name = fields.Char()
    total_amount = fields.Float()
    
    def compute_total(self):
        pass
"""
        mock_git_manager_class.return_value = mock_git_manager

        # Execute
        command = DetectCommand(config)
        inventory = command._extract_inventory_at_commit(
            "HEAD", ["sale/models/sale_order.py"]
        )

        # Verify
        assert "sale/models/sale_order.py" in inventory
        file_inv = inventory["sale/models/sale_order.py"]
        assert "sale.order" in file_inv
        model_inv = file_inv["sale.order"]
        assert len(model_inv["fields"]) == 2
        assert len(model_inv["methods"]) == 1

    def test_find_rename_candidates(self):
        """Test finding rename candidates between inventories"""
        config = Config()
        config.detection.confidence_threshold = 0.7

        command = DetectCommand(config)

        # Create old and new inventories
        old_inventory = {
            "module/models/model.py": {
                "test.model": {
                    "fields": [
                        FieldInfo(name="old_field", field_type="Char", required=False),
                        FieldInfo(
                            name="unchanged_field", field_type="Float", required=False
                        ),
                    ],
                    "methods": [
                        MethodInfo(name="old_method", params=["self"], returns=None),
                    ],
                }
            }
        }

        new_inventory = {
            "module/models/model.py": {
                "test.model": {
                    "fields": [
                        FieldInfo(name="new_field", field_type="Char", required=False),
                        FieldInfo(
                            name="unchanged_field", field_type="Float", required=False
                        ),
                    ],
                    "methods": [
                        MethodInfo(name="new_method", params=["self"], returns=None),
                    ],
                }
            }
        }

        # Find candidates
        candidates = command._find_rename_candidates(old_inventory, new_inventory)

        # Should find rename from old_field to new_field and old_method to new_method
        assert len(candidates) > 0
        field_candidates = [c for c in candidates if c.item_type == "field"]
        method_candidates = [c for c in candidates if c.item_type == "method"]

        assert len(field_candidates) >= 1
        assert len(method_candidates) >= 1

    def test_calculate_confidence(self):
        """Test confidence score calculation"""
        config = Config()
        command = DetectCommand(config)

        # Test field similarity
        field1 = FieldInfo(name="order_line", field_type="One2many", required=False)
        field2 = FieldInfo(name="order_line_ids", field_type="One2many", required=False)

        confidence = command._calculate_confidence(field1, field2, "field")

        # Should have high confidence (same type, similar name)
        assert confidence > 0.7

        # Test method similarity
        method1 = MethodInfo(name="compute_total", params=["self"], returns="float")
        method2 = MethodInfo(
            name="_compute_total_amount", params=["self"], returns="float"
        )

        confidence = command._calculate_confidence(method1, method2, "method")

        # Should have moderate confidence
        assert confidence > 0.5

    def test_interactive_validation(self):
        """Test interactive validation of candidates"""
        config = Config()
        config.interactive = True

        command = DetectCommand(config)

        candidates = [
            RenameCandidate(
                old_name="old_field",
                new_name="new_field",
                confidence=0.85,
                model="test.model",
                module="test_module",
                file_path="test_module/models/model.py",
                item_type="field",
            ),
            RenameCandidate(
                old_name="old_method",
                new_name="new_method",
                confidence=0.65,
                model="test.model",
                module="test_module",
                file_path="test_module/models/model.py",
                item_type="method",
            ),
        ]

        # Mock user input
        with patch("builtins.input", side_effect=["y", "n"]):
            validated = command._validate_candidates(candidates)

        # Should accept first, reject second
        assert len(validated) == 1
        assert validated[0].old_name == "old_field"

    def test_auto_approve_high_confidence(self):
        """Test auto-approval of high confidence candidates"""
        config = Config()
        config.interactive = False
        config.detection.auto_approve_threshold = 0.9

        command = DetectCommand(config)

        candidates = [
            RenameCandidate(
                old_name="field1",
                new_name="field1_new",
                confidence=0.95,  # Above auto-approve
                model="test.model",
                module="test",
                file_path="test/models/model.py",
                item_type="field",
            ),
            RenameCandidate(
                old_name="field2",
                new_name="field2_new",
                confidence=0.85,  # Below auto-approve
                model="test.model",
                module="test",
                file_path="test/models/model.py",
                item_type="field",
            ),
        ]

        validated = command._validate_candidates(candidates)

        # Should only auto-approve the high confidence one
        assert len(validated) == 1
        assert validated[0].confidence == 0.95

    @patch("src.commands.detect.GitManager")
    def test_save_to_csv(self, mock_git_manager_class, tmp_path):
        """Test saving results to CSV"""
        config = Config()
        config.repo_path = str(tmp_path)

        mock_git_manager_class.return_value = Mock()

        command = DetectCommand(config)

        candidates = [
            RenameCandidate(
                old_name="old_field",
                new_name="new_field",
                confidence=0.85,
                model="sale.order",
                module="sale",
                file_path="sale/models/sale_order.py",
                item_type="field",
            ),
        ]

        output_file = tmp_path / "changes.csv"
        command._save_results(candidates, output_file)

        # Verify CSV was created
        assert output_file.exists()

        # Load and verify content
        df = pd.read_csv(output_file)
        assert len(df) == 1
        assert df.iloc[0]["old_name"] == "old_field"
        assert df.iloc[0]["new_name"] == "new_field"
        assert df.iloc[0]["type"] == "field"
        assert df.iloc[0]["module"] == "sale"
        assert df.iloc[0]["model"] == "sale.order"
        assert df.iloc[0]["confidence"] == 0.85

    @patch("src.commands.detect.GitManager")
    def test_filter_by_modules(self, mock_git_manager_class, tmp_path):
        """Test filtering candidates by module"""
        config = Config()
        config.repo_path = str(tmp_path)
        config.modules = ["sale", "purchase"]

        mock_git_manager = Mock()
        mock_git_manager.get_modified_files.return_value = [
            "sale/models/sale.py",
            "stock/models/stock.py",
            "purchase/models/purchase.py",
        ]
        mock_git_manager_class.return_value = mock_git_manager

        command = DetectCommand(config)

        # Should only process files in specified modules
        with patch.object(command, "_extract_inventory_at_commit") as mock_extract:
            mock_extract.return_value = {}
            command.execute("HEAD~1", "HEAD")

            # Check that only sale and purchase files were processed
            calls = mock_extract.call_args_list
            processed_files = []
            for call in calls:
                processed_files.extend(call[0][1])

            assert "sale/models/sale.py" in processed_files
            assert "purchase/models/purchase.py" in processed_files
            assert "stock/models/stock.py" not in processed_files

    def test_rename_candidate_dataclass(self):
        """Test RenameCandidate dataclass"""
        candidate = RenameCandidate(
            old_name="old_name",
            new_name="new_name",
            confidence=0.75,
            model="test.model",
            module="test",
            file_path="test/models/model.py",
            item_type="field",
        )

        assert candidate.old_name == "old_name"
        assert candidate.new_name == "new_name"
        assert candidate.confidence == 0.75
        assert candidate.model == "test.model"
        assert candidate.module == "test"
        assert candidate.file_path == "test/models/model.py"
        assert candidate.item_type == "field"

    @patch("src.commands.detect.GitManager")
    def test_no_changes_detected(self, mock_git_manager_class, tmp_path):
        """Test when no changes are detected"""
        config = Config()
        config.repo_path = str(tmp_path)

        # Mock GitManager with no modified files
        mock_git_manager = Mock()
        mock_git_manager.get_modified_files.return_value = []
        mock_git_manager_class.return_value = mock_git_manager

        command = DetectCommand(config)
        candidates = command.execute("HEAD~1", "HEAD")

        # Should return empty list
        assert candidates == []

    @patch("src.commands.detect.GitManager")
    def test_xml_analysis(self, mock_git_manager_class, tmp_path):
        """Test XML file analysis is included when enabled"""
        config = Config()
        config.repo_path = str(tmp_path)
        config.detection.analyze_xml = True

        mock_git_manager = Mock()
        mock_git_manager.get_modified_files.return_value = [
            "sale/models/sale.py",
            "sale/views/sale_views.xml",
        ]
        mock_git_manager_class.return_value = mock_git_manager

        command = DetectCommand(config)

        # Both Python and XML files should be processed
        with patch.object(command, "_extract_inventory_at_commit") as mock_extract:
            mock_extract.return_value = {}
            command.execute("HEAD~1", "HEAD")

            # Verify both file types were included
            calls = mock_extract.call_args_list
            all_files = []
            for call in calls:
                all_files.extend(call[0][1])

            assert "sale/models/sale.py" in all_files
            assert "sale/views/sale_views.xml" in all_files
