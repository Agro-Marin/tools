"""
Integration tests for complete workflows
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import pytest
import yaml
from src.commands.detect import DetectCommand
from src.commands.rename import RenameCommand
from src.commands.reorder import UnifiedReorderCommand
from src.commands.workflow import WorkflowCommand
from src.core.config import Config
from src.core.git_manager import GitManager


class TestWorkflowIntegration:
    """Integration tests for end-to-end workflows"""

    @pytest.fixture
    def test_repo(self, tmp_path):
        """Create a test Git repository with sample Odoo module"""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        # Initialize Git repo
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            capture_output=True,
        )

        # Create sample module structure
        sale_module = repo_path / "sale"
        sale_module.mkdir()

        models_dir = sale_module / "models"
        models_dir.mkdir()

        views_dir = sale_module / "views"
        views_dir.mkdir()

        # Create sample Python file
        sale_order_py = models_dir / "sale_order.py"
        sale_order_py.write_text(
            """
from odoo import models, fields, api

class SaleOrder(models.Model):
    _name = 'sale.order'
    _description = 'Sale Order'
    
    # Fields in wrong order
    total_amount = fields.Float('Total', compute='_compute_total')
    name = fields.Char('Name', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer')
    date_order = fields.Datetime('Order Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
    ], default='draft')
    
    # Methods in wrong order
    def action_confirm(self):
        self.state = 'confirmed'
    
    @api.depends('line_ids')
    def _compute_total(self):
        for order in self:
            order.total_amount = sum(order.line_ids.mapped('subtotal'))
    
    def action_cancel(self):
        self.state = 'draft'
"""
        )

        # Create sample XML file
        sale_order_view = views_dir / "sale_order_views.xml"
        sale_order_view.write_text(
            """
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_sale_order_form" model="ir.ui.view">
        <field name="name">sale.order.form</field>
        <field name="model">sale.order</field>
        <field name="arch" type="xml">
            <form>
                <header>
                    <field name="state" widget="statusbar"/>
                </header>
                <sheet>
                    <group>
                        <field name="name"/>
                        <field name="partner_id"/>
                        <field name="date_order"/>
                        <field name="total_amount"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>
</odoo>
"""
        )

        # Initial commit
        subprocess.run(["git", "add", "."], cwd=repo_path)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            capture_output=True,
        )

        return repo_path

    def test_order_workflow(self, test_repo):
        """Test code ordering workflow"""
        config = Config()
        config.repo_path = str(test_repo)
        config.ordering.strategy = "semantic"
        config.dry_run = False
        config.backup.enabled = False

        # Execute ordering
        order_cmd = UnifiedReorderCommand(config)
        success = order_cmd.execute(test_repo / "sale", recursive=True)

        assert success is True

        # Verify file was reordered
        sale_order_py = test_repo / "sale" / "models" / "sale_order.py"
        content = sale_order_py.read_text()

        # Check that fields are now in correct order (name should come before total_amount)
        name_pos = content.find("name = fields.Char")
        total_pos = content.find("total_amount = fields.Float")
        assert name_pos < total_pos

    def test_detect_rename_workflow(self, test_repo):
        """Test field/method detection and renaming workflow"""
        config = Config()
        config.repo_path = str(test_repo)
        config.detection.confidence_threshold = 0.5
        config.dry_run = False
        config.backup.enabled = False

        # Make changes to simulate renames
        sale_order_py = test_repo / "sale" / "models" / "sale_order.py"
        original_content = sale_order_py.read_text()

        # Rename partner_id to customer_id
        new_content = original_content.replace("partner_id", "customer_id")
        sale_order_py.write_text(new_content)

        # Commit the change
        subprocess.run(["git", "add", "."], cwd=test_repo)
        subprocess.run(
            ["git", "commit", "-m", "Rename partner_id to customer_id"],
            cwd=test_repo,
            capture_output=True,
        )

        # Detect changes
        detect_cmd = DetectCommand(config)
        candidates = detect_cmd.execute("HEAD~1", "HEAD")

        # Should detect the rename
        assert len(candidates) > 0
        field_renames = [c for c in candidates if c.item_type == "field"]
        assert any(
            c.old_name == "partner_id" and c.new_name == "customer_id"
            for c in field_renames
        )

        # Save to CSV
        csv_file = test_repo / "changes.csv"
        detect_cmd._save_results(candidates, csv_file)

        # Apply renames to XML files
        rename_cmd = RenameCommand(config)
        success = rename_cmd.execute(csv_file)

        assert success is True

        # Verify XML was updated
        sale_order_view = test_repo / "sale" / "views" / "sale_order_views.xml"
        xml_content = sale_order_view.read_text()
        assert "customer_id" in xml_content
        assert "partner_id" not in xml_content

    def test_full_refactoring_pipeline(self, test_repo):
        """Test complete refactoring pipeline"""
        # Create workflow file
        workflow_file = test_repo / "refactor_workflow.yaml"
        workflow_data = {
            "pipelines": {
                "full_refactor": {
                    "description": "Complete refactoring pipeline",
                    "steps": [
                        {
                            "command": "order",
                            "args": {
                                "path": "./sale",
                                "recursive": True,
                                "strategy": "semantic",
                            },
                        },
                        {"shell": "git add . && git commit -m 'Reorder code' || true"},
                        {
                            "command": "detect",
                            "args": {
                                "from_commit": "HEAD~1",
                                "to_commit": "HEAD",
                                "output": "detected_changes.csv",
                            },
                        },
                    ],
                }
            }
        }

        with open(workflow_file, "w") as f:
            yaml.dump(workflow_data, f)

        # Setup config
        config = Config()
        config.repo_path = str(test_repo)
        config.dry_run = False
        config.backup.enabled = True
        config.backup.directory = str(test_repo / ".backups")

        # Execute workflow
        workflow_cmd = WorkflowCommand(config)
        success = workflow_cmd.execute(workflow_file, pipeline_name="full_refactor")

        assert success is True

        # Verify backup was created
        backup_dir = test_repo / ".backups"
        assert backup_dir.exists()

        # Verify code was reordered
        sale_order_py = test_repo / "sale" / "models" / "sale_order.py"
        content = sale_order_py.read_text()

        # Fields should be in correct order
        name_pos = content.find("name = fields.Char")
        partner_pos = content.find("partner_id = fields.Many2one")
        assert name_pos > 0
        assert partner_pos > name_pos

    def test_module_specific_workflow(self, test_repo):
        """Test module-specific processing workflow"""
        # Create another module
        purchase_module = test_repo / "purchase"
        purchase_module.mkdir()
        models_dir = purchase_module / "models"
        models_dir.mkdir()

        purchase_order = models_dir / "purchase_order.py"
        purchase_order.write_text(
            """
class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    
    # Unordered fields
    vendor_id = fields.Many2one('res.partner')
    amount = fields.Float()
    name = fields.Char()
"""
        )

        # Commit
        subprocess.run(["git", "add", "."], cwd=test_repo)
        subprocess.run(
            ["git", "commit", "-m", "Add purchase module"],
            cwd=test_repo,
            capture_output=True,
        )

        # Configure to process only sale module
        config = Config()
        config.repo_path = str(test_repo)
        config.modules = ["sale"]
        config.dry_run = False
        config.backup.enabled = False

        # Order code
        order_cmd = UnifiedReorderCommand(config)
        order_cmd.execute(test_repo, recursive=True)

        # Sale module should be ordered
        sale_content = (test_repo / "sale" / "models" / "sale_order.py").read_text()
        assert "name = fields.Char" in sale_content

        # Purchase module should remain unchanged
        purchase_content = purchase_order.read_text()
        vendor_pos = purchase_content.find("vendor_id")
        name_pos = purchase_content.find("name = fields.Char")
        assert vendor_pos < name_pos  # Still in original order

    def test_dry_run_workflow(self, test_repo):
        """Test dry run mode doesn't modify files"""
        # Save original content
        sale_order_py = test_repo / "sale" / "models" / "sale_order.py"
        original_content = sale_order_py.read_text()

        # Configure dry run
        config = Config()
        config.repo_path = str(test_repo)
        config.dry_run = True
        config.ordering.strategy = "semantic"

        # Execute ordering in dry run
        order_cmd = UnifiedReorderCommand(config)
        success = order_cmd.execute(test_repo / "sale", recursive=True)

        assert success is True

        # File should not be modified
        current_content = sale_order_py.read_text()
        assert current_content == original_content

    def test_error_recovery_workflow(self, test_repo):
        """Test workflow handles errors gracefully"""
        # Create invalid Python file
        invalid_file = test_repo / "sale" / "models" / "invalid.py"
        invalid_file.write_text("This is not valid Python syntax {{{")

        config = Config()
        config.repo_path = str(test_repo)
        config.dry_run = False
        config.backup.enabled = False

        # Try to order - should handle error
        order_cmd = UnifiedReorderCommand(config)
        success = order_cmd.execute(test_repo / "sale", recursive=True)

        # Should return False but not crash
        assert success is False

        # Other files should still be processed
        sale_order_py = test_repo / "sale" / "models" / "sale_order.py"
        assert sale_order_py.exists()

    def test_backup_and_restore_workflow(self, test_repo):
        """Test backup creation and restoration"""
        config = Config()
        config.repo_path = str(test_repo)
        config.backup.enabled = True
        config.backup.directory = str(test_repo / ".backups")
        config.dry_run = False

        # Save original content
        sale_order_py = test_repo / "sale" / "models" / "sale_order.py"
        original_content = sale_order_py.read_text()

        # Execute ordering with backup
        order_cmd = UnifiedReorderCommand(config)
        success = order_cmd.execute(test_repo / "sale", recursive=True)

        assert success is True

        # Verify backup was created
        backup_dir = test_repo / ".backups"
        assert backup_dir.exists()

        # Find backup session
        sessions = list(backup_dir.glob("*"))
        assert len(sessions) > 0

        # Verify file was modified
        modified_content = sale_order_py.read_text()
        assert modified_content != original_content

        # Simulate restoration (would need BackupManager)
        # This is just to verify backup exists and contains the file
        session_dir = sessions[0]
        if session_dir.suffix != ".gz":  # Not compressed
            backup_file = session_dir / "sale" / "models" / "sale_order.py"
            if backup_file.exists():
                backup_content = backup_file.read_text()
                assert backup_content == original_content
