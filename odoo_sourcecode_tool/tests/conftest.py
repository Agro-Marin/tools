"""
Pytest configuration and shared fixtures
"""

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_python_code() -> str:
    """Sample Odoo Python code for testing"""
    return """
from odoo import models, fields, api

class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['mail.thread']

    name = fields.Char('Order Reference', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer')
    date_order = fields.Datetime('Order Date', default=fields.Datetime.now)
    total_amount = fields.Float('Total', compute='_compute_total')

    @api.depends('order_line.price_total')
    def _compute_total(self):
        for order in self:
            order.total_amount = sum(order.order_line.mapped('price_total'))

    @api.constrains('date_order')
    def _check_date(self):
        if self.date_order > fields.Datetime.now():
            raise ValueError("Order date cannot be in the future")
"""


@pytest.fixture
def sample_xml_code() -> str:
    """Sample Odoo XML view for testing"""
    return """<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_sale_order_form" model="ir.ui.view">
        <field name="name">sale.order.form</field>
        <field name="model">sale.order</field>
        <field name="arch" type="xml">
            <form string="Sales Order">
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


@pytest.fixture
def test_repo(temp_dir: Path) -> Path:
    """Create a test Git repository"""
    import subprocess

    # Initialize Git repo
    subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=temp_dir)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir)

    # Create initial commit
    (temp_dir / "README.md").write_text("Test Repository")
    subprocess.run(["git", "add", "."], cwd=temp_dir)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir)

    return temp_dir


@pytest.fixture
def sample_odoo_module(temp_dir: Path) -> Path:
    """Create a sample Odoo module structure"""
    module_path = temp_dir / "sample_module"
    module_path.mkdir()

    # Create standard Odoo module directories
    (module_path / "models").mkdir()
    (module_path / "views").mkdir()
    (module_path / "security").mkdir()
    (module_path / "wizards").mkdir()

    # Create __manifest__.py
    manifest = module_path / "__manifest__.py"
    manifest.write_text(
        """
{
    'name': 'Sample Module',
    'version': '19.0.1.0.0',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/sample_views.xml',
    ],
}
"""
    )

    # Create __init__.py files
    (module_path / "__init__.py").write_text("from . import models")
    (module_path / "models" / "__init__.py").write_text("from . import sample_model")

    # Create unordered sample model for testing ordering
    model_file = module_path / "models" / "sample_model.py"
    model_file.write_text(
        """
from odoo import models, fields, api

class SampleModel(models.Model):
    _name = 'sample.model'
    _description = 'Sample Model'

    # Fields intentionally unordered
    active = fields.Boolean('Active', default=True)
    total = fields.Float('Total', compute='_compute_total')
    name = fields.Char('Name', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], default='draft')

    # Methods intentionally unordered
    def action_done(self):
        self.state = 'done'

    @api.depends('line_ids.subtotal')
    def _compute_total(self):
        for record in self:
            record.total = sum(record.line_ids.mapped('subtotal'))

    @api.model
    def create(self, vals):
        return super().create(vals)
"""
    )

    # Create view file
    view_file = module_path / "views" / "sample_views.xml"
    view_file.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_sample_model_form" model="ir.ui.view">
        <field name="name">sample.model.form</field>
        <field name="model">sample.model</field>
        <field name="arch" type="xml">
            <form>
                <header>
                    <field name="state" widget="statusbar"/>
                </header>
                <sheet>
                    <group>
                        <field name="name"/>
                        <field name="partner_id"/>
                        <field name="total"/>
                        <field name="active"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>
</odoo>
"""
    )

    # Create security file
    security_file = module_path / "security" / "ir.model.access.csv"
    security_file.write_text(
        """id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_sample_model,sample.model,model_sample_model,base.group_user,1,1,1,1
"""
    )

    return module_path


@pytest.fixture
def sample_workflow_file(temp_dir: Path) -> Path:
    """Create a sample workflow YAML file"""
    import yaml

    workflow_file = temp_dir / "test_workflow.yaml"
    workflow_data = {
        "pipelines": {
            "test_pipeline": {
                "description": "Test pipeline",
                "steps": [
                    {"command": "order", "args": {"path": ".", "recursive": True}},
                    {"shell": "echo 'Complete'"},
                ],
            }
        }
    }

    with open(workflow_file, "w") as f:
        yaml.dump(workflow_data, f)

    return workflow_file


@pytest.fixture
def sample_csv_changes(temp_dir: Path) -> Path:
    """Create a sample CSV file with changes"""
    csv_file = temp_dir / "sample_changes.csv"
    csv_content = """old_name,new_name,type,module,model,confidence
partner_id,customer_id,field,sample_module,sample.model,0.85
action_confirm,confirm,method,sample_module,sample.model,0.75
"""
    csv_file.write_text(csv_content)
    return csv_file
