"""
Unit tests for rename command
"""

import ast
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest
from core.base_processor import ProcessingStatus, ProcessResult
from src.commands.rename import ASTRenameTransformer, FieldChange, RenameCommand
from src.core.config import Config


class TestRenameCommand:
    """Test rename command functionality"""

    def test_initialization(self):
        """Test rename command initialization"""
        config = Config()
        config.backup.enabled = True

        command = RenameCommand(config)

        assert command.config == config
        assert command.backup_manager is not None

    def test_initialization_no_backup(self):
        """Test initialization without backup"""
        config = Config()
        config.backup.enabled = False

        command = RenameCommand(config)

        assert command.backup_manager is None

    def test_load_changes_from_csv(self, tmp_path):
        """Test loading changes from CSV file"""
        config = Config()
        command = RenameCommand(config)

        # Create CSV file
        csv_file = tmp_path / "changes.csv"
        df = pd.DataFrame(
            [
                {
                    "old_name": "old_field",
                    "new_name": "new_field",
                    "type": "field",
                    "module": "sale",
                    "model": "sale.order",
                },
                {
                    "old_name": "old_method",
                    "new_name": "new_method",
                    "type": "method",
                    "module": "sale",
                    "model": "sale.order",
                },
            ]
        )
        df.to_csv(csv_file, index=False)

        # Load changes
        changes = command._load_changes(csv_file)

        assert len(changes) == 2
        assert changes[0].old_name == "old_field"
        assert changes[0].new_name == "new_field"
        assert changes[0].change_type == "field"
        assert changes[1].change_type == "method"

    def test_group_changes(self):
        """Test grouping changes by model"""
        config = Config()
        command = RenameCommand(config)

        changes = [
            FieldChange("field1", "field1_new", "field", "sale", "sale.order"),
            FieldChange("field2", "field2_new", "field", "sale", "sale.order"),
            FieldChange("field3", "field3_new", "field", "purchase", "purchase.order"),
        ]

        grouped = command._group_changes(changes)

        assert len(grouped) == 2
        assert "sale.sale.order" in grouped
        assert "purchase.purchase.order" in grouped
        assert len(grouped["sale.sale.order"]) == 2
        assert len(grouped["purchase.purchase.order"]) == 1

    def test_find_files_for_module(self, tmp_path):
        """Test finding relevant files in a module"""
        config = Config()
        config.renaming.file_types = ["python", "xml"]
        command = RenameCommand(config)

        # Create module structure
        module_path = tmp_path / "sale"
        (module_path / "models").mkdir(parents=True)
        (module_path / "views").mkdir(parents=True)
        (module_path / "wizards").mkdir(parents=True)
        (module_path / "data").mkdir(parents=True)

        (module_path / "models" / "sale.py").write_text("")
        (module_path / "models" / "sale_line.py").write_text("")
        (module_path / "views" / "sale_views.xml").write_text("")
        (module_path / "data" / "sale_data.xml").write_text("")
        (module_path / "wizards" / "sale_wizard.py").write_text("")

        # Find files
        files = command._find_files_for_module(module_path)

        # Should find all Python and XML files
        file_names = {f.name for f in files}
        assert "sale.py" in file_names
        assert "sale_line.py" in file_names
        assert "sale_views.xml" in file_names
        assert "sale_data.xml" in file_names
        assert "sale_wizard.py" in file_names

    def test_process_python_file_fields(self, tmp_path):
        """Test processing Python file for field renames"""
        config = Config()
        config.dry_run = False
        command = RenameCommand(config)

        # Create Python file
        test_file = tmp_path / "model.py"
        test_file.write_text(
            """
class TestModel(models.Model):
    _name = 'test.model'
    
    old_field = fields.Char()
    other_field = fields.Float()
"""
        )

        changes = [FieldChange("old_field", "new_field", "field", "test", "test.model")]

        result = command._process_python_file(test_file, changes)

        assert result.status == ProcessingStatus.SUCCESS
        assert result.changes_applied > 0

        # Verify file was updated
        content = test_file.read_text()
        assert "new_field" in content
        assert "old_field" not in content

    def test_process_python_file_methods(self, tmp_path):
        """Test processing Python file for method renames"""
        config = Config()
        config.dry_run = False
        command = RenameCommand(config)

        # Create Python file
        test_file = tmp_path / "model.py"
        test_file.write_text(
            """
class TestModel(models.Model):
    def old_method(self):
        return True
    
    def other_method(self):
        return False
"""
        )

        changes = [
            FieldChange("old_method", "new_method", "method", "test", "test.model")
        ]

        result = command._process_python_file(test_file, changes)

        assert result.status == ProcessingStatus.SUCCESS
        assert result.changes_applied > 0

        # Verify file was updated
        content = test_file.read_text()
        assert "new_method" in content
        assert "old_method" not in content

    def test_process_python_file_dry_run(self, tmp_path):
        """Test dry run mode doesn't modify files"""
        config = Config()
        config.dry_run = True
        command = RenameCommand(config)

        # Create Python file
        test_file = tmp_path / "model.py"
        original_content = """
class TestModel(models.Model):
    old_field = fields.Char()
"""
        test_file.write_text(original_content)

        changes = [FieldChange("old_field", "new_field", "field", "test", "test.model")]

        result = command._process_python_file(test_file, changes)

        assert result.status == ProcessingStatus.SUCCESS

        # Verify file was NOT updated
        assert test_file.read_text() == original_content

    def test_process_xml_file(self, tmp_path):
        """Test processing XML file for field references"""
        config = Config()
        config.dry_run = False
        command = RenameCommand(config)

        # Create XML file
        test_file = tmp_path / "view.xml"
        test_file.write_text(
            """
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_test" model="ir.ui.view">
        <field name="name">Test View</field>
        <field name="model">test.model</field>
        <field name="arch" type="xml">
            <form>
                <field name="old_field"/>
                <field name="other_field"/>
            </form>
        </field>
    </record>
</odoo>
"""
        )

        changes = [FieldChange("old_field", "new_field", "field", "test", "test.model")]

        result = command._process_xml_file(test_file, changes)

        assert result.status == ProcessingStatus.SUCCESS
        assert result.changes_applied > 0

        # Verify XML was updated
        content = test_file.read_text()
        assert 'name="new_field"' in content
        assert 'name="old_field"' not in content

    def test_process_file_with_backup(self, tmp_path):
        """Test backup is created before processing"""
        config = Config()
        config.backup.enabled = True
        config.backup.directory = str(tmp_path / "backups")
        config.dry_run = False

        command = RenameCommand(config)

        test_file = tmp_path / "test.py"
        test_file.write_text("old_field = fields.Char()")

        changes = [FieldChange("old_field", "new_field", "field", "test", "test.model")]

        with patch.object(command.backup_manager, "backup_file") as mock_backup:
            result = command._process_file(test_file, changes)

            mock_backup.assert_called_once_with(test_file)

    def test_execute_full_workflow(self, tmp_path):
        """Test complete execution workflow"""
        config = Config()
        config.repo_path = str(tmp_path)
        config.dry_run = False
        config.backup.enabled = False

        # Create module structure
        module_path = tmp_path / "sale"
        models_path = module_path / "models"
        models_path.mkdir(parents=True)

        model_file = models_path / "sale.py"
        model_file.write_text(
            """
class SaleOrder(models.Model):
    _name = 'sale.order'
    old_field = fields.Char()
"""
        )

        # Create CSV with changes
        csv_file = tmp_path / "changes.csv"
        df = pd.DataFrame(
            [
                {
                    "old_name": "old_field",
                    "new_name": "new_field",
                    "type": "field",
                    "module": "sale",
                    "model": "sale.order",
                }
            ]
        )
        df.to_csv(csv_file, index=False)

        # Execute
        command = RenameCommand(config)
        success = command.execute(csv_file)

        assert success is True

        # Verify file was updated
        content = model_file.read_text()
        assert "new_field" in content
        assert "old_field" not in content

    def test_execute_filter_by_modules(self, tmp_path):
        """Test filtering changes by module"""
        config = Config()
        config.repo_path = str(tmp_path)
        config.modules = ["sale"]  # Only process sale module

        # Create CSV with changes for multiple modules
        csv_file = tmp_path / "changes.csv"
        df = pd.DataFrame(
            [
                {
                    "old_name": "field1",
                    "new_name": "field1_new",
                    "type": "field",
                    "module": "sale",
                    "model": "sale.order",
                },
                {
                    "old_name": "field2",
                    "new_name": "field2_new",
                    "type": "field",
                    "module": "purchase",
                    "model": "purchase.order",
                },
            ]
        )
        df.to_csv(csv_file, index=False)

        command = RenameCommand(config)

        with patch.object(command, "_process_changes") as mock_process:
            mock_process.return_value = []
            command.execute(csv_file)

            # Should only process sale module
            args = mock_process.call_args[0][0]
            assert "sale.sale.order" in args
            assert "purchase.purchase.order" not in args


class TestASTRenameTransformer:
    """Test AST transformer for renaming"""

    def test_rename_field_assignment(self):
        """Test renaming field in assignment"""
        field_changes = {"old_field": "new_field"}
        transformer = ASTRenameTransformer(field_changes, {})

        code = "old_field = fields.Char()"
        tree = ast.parse(code)
        new_tree = transformer.visit(tree)

        assert len(transformer.changes_made) == 1
        assert "field:old_field" in transformer.changes_made

        # Verify transformation
        new_code = ast.unparse(new_tree)
        assert "new_field" in new_code

    def test_rename_method_def(self):
        """Test renaming method definition"""
        method_changes = {"old_method": "new_method"}
        transformer = ASTRenameTransformer({}, method_changes)

        code = "def old_method(self): pass"
        tree = ast.parse(code)
        new_tree = transformer.visit(tree)

        assert len(transformer.changes_made) == 1
        assert "method:old_method" in transformer.changes_made

        # Verify transformation
        new_code = ast.unparse(new_tree)
        assert "new_method" in new_code

    def test_rename_attribute_access(self):
        """Test renaming field in attribute access"""
        field_changes = {"old_field": "new_field"}
        transformer = ASTRenameTransformer(field_changes, {})

        code = "self.old_field = 'value'"
        tree = ast.parse(code)
        new_tree = transformer.visit(tree)

        assert len(transformer.changes_made) == 1

        # Verify transformation
        new_code = ast.unparse(new_tree)
        assert "self.new_field" in new_code

    def test_rename_string_constant(self):
        """Test renaming field name in string constant"""
        field_changes = {"old_field": "new_field"}
        transformer = ASTRenameTransformer(field_changes, {})

        code = "fields = ['old_field', 'other_field']"
        tree = ast.parse(code)
        new_tree = transformer.visit(tree)

        assert len(transformer.changes_made) == 1

        # Verify transformation
        new_code = ast.unparse(new_tree)
        assert "'new_field'" in new_code

    def test_no_changes(self):
        """Test when no changes match"""
        field_changes = {"nonexistent": "new_name"}
        transformer = ASTRenameTransformer(field_changes, {})

        code = "some_field = fields.Char()"
        tree = ast.parse(code)
        transformer.visit(tree)

        assert len(transformer.changes_made) == 0
