# Odoo Module Structure Blueprint

## Module Directory Structure

```
module_name/
├── __init__.py
├── __manifest__.py
│
├── controllers/
│   ├── __init__.py
│   └── main.py                 # HTTP controllers
│
├── data/
│   ├── ir_sequence_data.xml    # Sequences
│   ├── ir_cron_data.xml        # Scheduled actions
│   ├── mail_template_data.xml  # Email templates
│   ├── ir_config_parameter.xml # System parameters
│   └── demo_data.xml           # Demo records
│
├── demo/
│   └── demo.xml                # Demo data (referenced in manifest)
│
├── i18n/
│   ├── module_name.pot        # Translation template
│   ├── es.po                  # Spanish translations
│   └── fr.po                  # French translations
│
├── models/
│   ├── __init__.py
│   ├── res_partner.py         # Inherited models (res.*)
│   ├── res_company.py         # Inherited models
│   ├── sale_order.py          # Main business models
│   ├── sale_order_line.py     # Line models (ONE FILE PER CLASS)
│   ├── product_template.py    # Inherited business models
│   └── ir_attachment.py       # System model extensions
│
├── report/
│   ├── __init__.py
│   ├── report_name.py         # Report parser classes
│   ├── report_name.xml        # Report definitions
│   └── report_templates.xml   # Report QWeb templates
│
├── security/
│   ├── ir.model.access.csv    # Access rights
│   └── security.xml           # Record rules & groups
│
├── static/
│   ├── description/
│   │   ├── icon.png          # Module icon (128x128)
│   │   └── index.html        # Module description page
│   │
│   ├── src/
│   │   ├── css/
│   │   │   └── style.css     # Custom styles
│   │   ├── js/
│   │   │   └── widget.js     # JavaScript widgets
│   │   ├── scss/
│   │   │   └── style.scss    # SCSS styles
│   │   └── xml/
│   │       └── templates.xml # QWeb JS templates
│   │
│   └── img/
│       └── images.png        # Static images
│
├── tests/
│   ├── __init__.py
│   ├── test_sale_order.py    # Unit tests
│   └── test_workflow.py      # Integration tests
│
├── views/
│   ├── menu.xml                   # ALL MENUS IN THIS FILE ONLY
│   ├── res_partner_views.xml      # Inherited model views (NO MENUS)
│   ├── sale_order_views.xml       # Main model views (NO MENUS)
│   ├── sale_order_line_views.xml  # Line model views (NO MENUS)
│   ├── report_views.xml           # Report action definitions (NO MENUS)
│   └── templates.xml              # Website templates
│
├── wizard/
│   ├── __init__.py
│   ├── sale_order_wizard.py      # Wizard models
│   └── sale_order_wizard.xml     # Wizard views
│
└── README.md                      # Module documentation
```

## File Organization Rules

### Models Directory (`models/`)
**CRITICAL RULE: ONE CLASS PER FILE**
- Each model class must be in its own file
- File name must match the model's `_name` with dots replaced by underscores
- Examples:
  - `sale.order` → `sale_order.py`
  - `sale.order.line` → `sale_order_line.py`
  - `res.partner` → `res_partner.py` (for inherited models)

**File Naming Priority:**
1. System models (`res_*`, `ir_*`) - Odoo core extensions
2. Main business models - Primary module models
3. Line/detail models - Related one2many models
4. Mixin models - Abstract models for inheritance
5. Transient models - Temporary data models

### Views Directory (`views/`)
**CRITICAL RULE: Menu Consolidation**
- **ALL menu items MUST be in `menu.xml` only**
- **NO menu items in individual view files**
- This ensures centralized menu management

**Organization by Model:**
- One XML file per model for views only (no menus)
- Menu items consolidated in single `menu.xml` file
- File naming matches model file naming

**File Order in __manifest__.py:**
1. Security files
2. Data files
3. Views (in dependency order)
4. **menu.xml MUST be loaded LAST in views**
5. Templates
6. Reports
7. Wizards

### Security Directory (`security/`)
**Standard Files:**
- `ir.model.access.csv` - Access control lists
- `security.xml` - Groups and record rules
- Named after specific features if needed

### Data Directory (`data/`)
**Loading Order:**
1. Groups and categories
2. Sequences
3. System parameters
4. Email templates
5. Scheduled actions
6. Initial data records

## __manifest__.py Structure

```python
{
    'name': 'Module Name',
    'version': '17.0.1.0.0',
    'category': 'Sales/Sales',
    'sequence': 10,
    'summary': 'Brief module description',
    'description': '''
        Long description
        Multiple lines
    ''',
    'author': 'Your Company',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',

    # Dependencies
    'depends': [
        'base',
        'sale',
        'account',
    ],

    # Module conflicts
    'conflicts': [],

    # Always loaded
    'data': [
        # Security FIRST
        'security/security.xml',
        'security/ir.model.access.csv',

        # Data files
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',

        # Views
        'views/sale_order_views.xml',
        'views/sale_order_line_views.xml',
        'views/menu.xml',

        # Reports
        'report/report_templates.xml',

        # Wizards
        'wizard/sale_order_wizard.xml',
    ],

    # Demo data
    'demo': [
        'demo/demo.xml',
    ],

    # QWeb templates
    'qweb': [
        'static/src/xml/templates.xml',
    ],

    # Module metadata
    'installable': True,
    'application': False,
    'auto_install': False,

    # Hook methods
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',

    # Assets
    'assets': {
        'web.assets_backend': [
            'module_name/static/src/scss/style.scss',
            'module_name/static/src/js/widget.js',
        ],
        'web.assets_frontend': [
            'module_name/static/src/css/website.css',
        ],
    },

    # External dependencies
    'external_dependencies': {
        'python': ['pandas', 'numpy'],
        'bin': ['wkhtmltopdf'],
    },
}
```

## Module Naming Conventions

### Module Name
- Use lowercase
- Use underscores for spaces
- Be descriptive but concise
- Examples: `sale_commission`, `account_invoice_merge`

### Technical Prefixes
Common prefixes for module types:
- `base_` - Core functionality extensions
- `account_` - Accounting related
- `sale_` - Sales related
- `purchase_` - Purchase related
- `stock_` - Inventory related
- `hr_` - Human resources
- `website_` - Website features
- `l10n_` - Localization (l10n_us, l10n_mx)
- `theme_` - Website themes

### Version Numbering
Format: `major.minor.patch.revision`
- `17.0.1.0.0` for Odoo 17
- First two digits = Odoo version
- Third = major version
- Fourth = minor version
- Fifth = patch/fix

## Import Organization

### In `__init__.py` files
```python
# Order of imports
from . import controllers
from . import models
from . import report
from . import wizard

# In models/__init__.py - order matters!
from . import res_company  # Base models first
from . import res_partner  # User/partner extensions
from . import product_template  # Dependencies
from . import sale_order  # Main models
from . import sale_order_line  # Detail models
```

## Best Practices

### Module Design
1. **Single Responsibility** - One business domain per module
2. **Minimal Dependencies** - Only required dependencies
3. **Reusability** - Design for potential reuse
4. **Upgradeability** - Consider migration paths

### File Organization
1. **One Model Per File** - Enforces clarity and maintainability
2. **Logical Grouping** - Related functionality together
3. **Consistent Naming** - Follow conventions strictly
4. **Clear Hierarchy** - Dependencies flow downward

### Security First
1. Always include access rights
2. Define groups before using them
3. Include record rules for multi-company
4. Test security thoroughly

### Documentation
1. README.md with installation and usage
2. Docstrings in Python code
3. Comments in XML for complex logic
4. Changelog for version history

## Anti-patterns to Avoid

1. **Multiple models in one file** - Violates single responsibility
2. **Circular dependencies** - Causes import errors
3. **Hardcoded IDs** - Use XML IDs instead
4. **Missing security** - Always define access rights
5. **Monolithic modules** - Split large modules
6. **Poor naming** - Be consistent and descriptive
7. **Missing translations** - Always make strings translatable
8. **Direct file manipulation** - Use Odoo's attachment system
9. **Synchronous external calls** - Use queue_job when possible
10. **Missing tests** - Always include test coverage