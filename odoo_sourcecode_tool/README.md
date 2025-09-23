# Odoo Source Code Tool

A comprehensive tool for managing Odoo source code with powerful code organization, refactoring, and analysis capabilities. Follows Odoo best practices and enforces standardized module structure.

## Features

### 1. Unified Reordering (`reorder`)
Comprehensive reordering for Python and XML files according to Odoo conventions:

- **Code Reordering**: Organize Python classes, methods, and fields by semantic meaning
- **Attribute Reordering**: Standardize field attribute order in Python files
- **XML Reordering**: Format and organize XML views, actions, and records
- **Menu Consolidation**: Enforce single `menu.xml` file for all menu items

Ordering strategies:
- **Semantic**: Groups by business meaning (recommended)
- **Type**: Groups by field/element type
- **Strict**: Alphabetical ordering

### 2. Change Detection (`detect`)
Analyze Git history to identify renamed fields and methods:
- Smart matching using AST parsing and confidence scoring
- Export changes to CSV for review
- Interactive validation mode
- Support for both fields and methods

### 3. Automated Renaming (`rename`)
Apply field/method renames across entire codebase:
- Updates both Python and XML files
- Preserves code structure and formatting
- Validates syntax after changes
- Dry-run mode for safety

### 4. Workflow Automation (`workflow`)
Chain multiple operations into complex workflows:
- YAML-based workflow configuration
- Support for conditional execution
- Integration with shell commands
- Reusable pipeline definitions

### 5. Backup Management (`backup`)
Automatic backup and restoration:
- Session-based backup system
- Compression support
- Configurable retention policies
- Easy restoration of previous states

## Installation

### Prerequisites
- Python 3.11 or higher
- Git (for detect functionality)

### Install dependencies
```bash
pip install --break-system-packages GitPython pandas lxml PyYAML click black isort rich
```

## Quick Start

### Initialize configuration
```bash
./odoo-tools init
```

### Reorder files (unified command)
```bash
# Reorder Python code
./odoo-tools reorder code models/sale_order.py

# Reorder field attributes
./odoo-tools reorder attributes models/ -r

# Reorder XML files
./odoo-tools reorder xml views/ -r

# Reorder everything in a module
./odoo-tools reorder all ./sale_management
```

### Detect field/method renames
```bash
# Detect changes between commits
./odoo-tools detect --from main --to HEAD --output changes.csv

# Interactive mode with custom threshold
./odoo-tools detect --from v14.0 --to v15.0 -i --threshold 0.8
```

### Apply renames
```bash
# Apply changes from CSV
./odoo-tools rename changes.csv --repo /path/to/odoo

# Dry run first
./odoo-tools rename changes.csv --repo /path/to/odoo --dry-run
```

### Run workflows
```bash
# Run predefined workflow
./odoo-tools workflow workflow.yaml --pipeline full_refactor
```

### Manage backups
```bash
# List backup sessions
./odoo-tools backup --sessions

# Restore from backup
./odoo-tools backup --restore <session-id>

# Clean old backups
./odoo-tools backup --clean
```

## Best Practices Enforcement

The tool enforces Odoo best practices based on official blueprints:

### Python Files
- **One class per file**: Each model class in its own file
- **File naming**: Files named after model (e.g., `sale_order.py` for `sale.order`)
- **Method organization**: Semantic grouping (compute → constrains → CRUD → actions → business → private)
- **Field organization**: Logical grouping with proper attribute ordering

### XML Files
- **Menu consolidation**: All menu items in single `views/menu.xml` file
- **View organization**: One XML file per model
- **Attribute ordering**: Standardized attribute order for all XML elements
- **No menus in view files**: Views focus purely on UI structure

### Module Structure
```
module_name/
├── __manifest__.py
├── models/
│   ├── sale_order.py        # One class per file
│   └── sale_order_line.py   # Separate file for each model
├── views/
│   ├── menu.xml             # ALL menus here
│   ├── sale_order_views.xml # Views only, no menus
│   └── sale_order_line_views.xml
├── security/
│   ├── ir.model.access.csv
│   └── security.xml
└── data/
    └── data.xml
```

## Configuration

The tool uses a hierarchical configuration system:
1. Environment variables (`ODOO_TOOLS_*`)
2. Global config (`~/.odoo-tools/config.yaml`)
3. Project config (`.odoo-tools.yaml`)
4. Command-line arguments

### Example configuration (.odoo-tools.yaml)
```yaml
# Repository settings
repo_path: /path/to/odoo
modules:
  - sale
  - purchase
  - stock

# Ordering settings
ordering:
  strategy: semantic
  add_section_headers: true
  single_class_per_file: true    # Enforce one class per file
  check_file_naming: true         # Verify file names match model names
  consolidate_menus: true         # All menus in menu.xml
  menu_file_name: menu.xml        # Standard menu file name
  black_line_length: 88
  magic_trailing_comma: true
  preserve_comments: true

# Detection settings
detection:
  confidence_threshold: 0.75
  auto_approve_threshold: 0.90
  include_methods: true
  include_fields: true
  analyze_xml: true

# Renaming settings
renaming:
  validate_syntax: true
  file_types:
    - python
    - xml
    - yaml
  parallel_processing: false
  max_workers: 4

# Backup settings
backup:
  enabled: true
  directory: .backups
  compression: true
  keep_sessions: 10

# General settings
dry_run: false
verbose: false
quiet: false
interactive: false
output_dir: output
```

## Blueprints and Standards

The tool follows and enforces Odoo development standards defined in:
- `templates/odoo_model_blueprint.md` - Python model file structure
- `templates/odoo_module_blueprint.md` - Complete module organization
- `templates/odoo_views_blueprint.md` - XML view file standards
- `templates/odoo_qweb_blueprint.md` - QWeb template guidelines

These blueprints define:
- Proper file and directory structure
- Naming conventions
- Code organization patterns
- Security best practices
- Performance optimizations

## Command Reference

### reorder
```bash
# Reorder Python code with semantic strategy
./odoo-tools reorder code ./module --strategy semantic

# Reorder attributes in field definitions
./odoo-tools reorder attributes ./module/models -r

# Reorder XML with pretty printing
./odoo-tools reorder xml ./module/views -r

# Reorder everything
./odoo-tools reorder all ./module
```

### detect
```bash
# Detect with auto-detected base commit
./odoo-tools detect --to HEAD --output changes.csv

# Detect with specific commits
./odoo-tools detect --from abc123 --to def456 --output changes.csv

# Filter by modules
./odoo-tools detect --modules sale,purchase --output changes.csv
```

### rename
```bash
# Apply renames with validation
./odoo-tools rename changes.csv --validate

# Apply to specific modules
./odoo-tools rename changes.csv --modules sale,purchase

# Parallel processing
./odoo-tools rename changes.csv --parallel --workers 4
```

### workflow
```bash
# List available pipelines
./odoo-tools workflow workflow.yaml --list

# Run specific pipeline
./odoo-tools workflow workflow.yaml --pipeline refactor

# Run with parameters
./odoo-tools workflow workflow.yaml --pipeline custom --params key=value
```

### backup
```bash
# Create manual backup
./odoo-tools backup --create "Before major refactoring"

# List sessions with details
./odoo-tools backup --sessions --verbose

# Restore specific files
./odoo-tools backup --restore session-id --files models/sale_order.py
```

## Environment Variables

- `ODOO_TOOLS_REPO_PATH` - Default repository path
- `ODOO_TOOLS_INTERACTIVE` - Enable interactive mode
- `ODOO_TOOLS_DRY_RUN` - Enable dry-run mode
- `ODOO_TOOLS_VERBOSE` - Enable verbose output

## Migration from Legacy Tools

This unified tool replaces and enhances:
- `code_ordering/` → `reorder code`
- `field_method_detector/` → `detect`
- `field_method_renaming/` → `rename`
- `odoo_field_attribute_reorder.py` → `reorder attributes`
- XML formatting → `reorder xml`

All functionality has been consolidated, improved, and standardized in this single comprehensive tool.

## Contributing

Contributions are welcome! Please ensure:
1. Code follows the project's style guidelines
2. Tests are included for new features
3. Documentation is updated
4. Blueprints are followed for Odoo-specific code

## License

[License information here]