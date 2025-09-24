# Odoo Python Model File Blueprint

## File Structure Schema

```
[File Header]
├── Encoding Declaration (optional)
├── Copyright/License (optional)
└── Module Docstring

[Imports Section]
├── Standard Library Imports
├── Third-party Library Imports
├── Odoo Imports
│   ├── from odoo import api, fields, models, _
│   └── from odoo.exceptions import ...
└── Local/Module Imports

[Module Constants]
└── _logger = logging.getLogger(__name__)

[Main Model Class]
├── Class Docstring
├── [PRIVATE ATTRIBUTES SECTION]
│   ├── _name
│   ├── _description
│   ├── _rec_name
│   ├── _order
│   ├── _inherit
│   ├── _inherits
│   ├── _table
│   ├── _auto
│   ├── _sql_constraints
│   └── _check_company_auto
│
├── [FIELDS SECTION]
│   ├── Basic Fields (name, active, sequence, state)
│   ├── Date/Time Fields
│   ├── Numeric Fields (integer, float, monetary)
│   ├── Text Fields (char, text, html)
│   ├── Binary Fields
│   ├── Selection Fields
│   ├── Boolean Fields
│   ├── Relational Fields
│   │   ├── Many2one fields
│   │   ├── One2many fields
│   │   └── Many2many fields
│   ├── Computed Fields
│   ├── Related Fields
│   └── Property Fields
│
└── [METHODS SECTION]
    ├── [COMPUTE METHODS]
    │   └── @api.depends decorated methods
    │
    ├── [INVERSE METHODS]
    │   └── Methods that inverse compute fields
    │
    ├── [SEARCH METHODS]
    │   └── Methods for computed field searching
    │
    ├── [CONSTRAINS METHODS]
    │   └── @api.constrains decorated methods
    │
    ├── [ONCHANGE METHODS]
    │   └── @api.onchange decorated methods
    │
    ├── [DEFAULT METHODS]
    │   └── _default_* methods
    │
    ├── [CRUD METHODS]
    │   ├── create()
    │   ├── write()
    │   ├── unlink()
    │   ├── copy()
    │   └── read()
    │
    ├── [ACTION METHODS]
    │   └── action_* methods (button actions)
    │
    ├── [BUSINESS METHODS]
    │   └── Core business logic methods
    │
    ├── [WORKFLOW METHODS]
    │   └── Methods handling state transitions
    │
    ├── [CRON METHODS]
    │   └── @api.model decorated scheduled methods
    │
    ├── [MAIL METHODS]
    │   └── Methods for mail integration
    │
    ├── [REPORT METHODS]
    │   └── Methods for report generation
    │
    ├── [HELPER/TOOL METHODS]
    │   └── @api.model decorated utility methods
    │
    └── [PRIVATE METHODS]
        └── _* prefixed internal methods

[Supporting Model Classes]
└── Additional models (Line models, Wizard models, etc.)
```

## Section Order Priority

### 1. Private Attributes (Model Definition)
**Order:** As defined by Odoo convention
- Must start with underscore
- Define model identity and behavior
- Set before any field declarations

### 2. Fields Declaration
**Recommended grouping order:**
1. **Identification fields** (name, active, sequence)
2. **State/Status fields** (state, stage_id)
3. **Basic data fields** (organized by type)
4. **Relational fields** (many2one → one2many → many2many)
5. **Computed fields**
6. **Related fields**

**Within each group, order by:**
- Required fields first
- Most important/frequently used
- Alphabetical (for similar importance)

### 3. Methods Organization
**Category order based on execution flow:**

1. **Compute Methods** - Define computed field values
2. **Inverse Methods** - Handle computed field updates
3. **Search Methods** - Enable searching on computed fields
4. **Constrains Methods** - Data validation rules
5. **Onchange Methods** - UI field interactions
6. **Default Methods** - Field default values
7. **CRUD Methods** - Override ORM operations
8. **Action Methods** - User-triggered actions (buttons)
9. **Business Methods** - Core business logic
10. **Workflow Methods** - State transitions
11. **Cron Methods** - Scheduled tasks
12. **Mail Methods** - Email/messaging
13. **Report Methods** - Report generation
14. **Helper Methods** - Utility functions
15. **Private Methods** - Internal helpers

## Naming Conventions

### Fields
- `snake_case` for all field names
- Suffix conventions:
  - `_id` for Many2one fields
  - `_ids` for One2many/Many2many fields
  - `_count` for computed counts
  - `_date` for date fields
  - `_datetime` for datetime fields

### Methods
- `snake_case` for all methods
- Prefix conventions:
  - `_compute_` for compute methods
  - `_inverse_` for inverse methods
  - `_search_` for search methods
  - `_check_` for constraint methods
  - `_onchange_` for onchange methods
  - `_default_` for default methods
  - `action_` for button actions
  - `_cron_` for scheduled methods
  - `_` for private methods

## Field Attribute Order

When declaring fields, attributes should follow this order:
1. `string` - Field label
2. `required` - If field is mandatory
3. `readonly` - If field is read-only
4. `index` - If field should be indexed
5. `default` - Default value
6. `states` - Field states
7. `copy` - If copied on duplication
8. `tracking` - For audit trail
9. `compute` - Compute method
10. `inverse` - Inverse method
11. `search` - Search method
12. `store` - If computed field is stored
13. `related` - For related fields
14. `domain` - Record filter
15. `context` - Default context
16. `help` - Help tooltip

## Method Decorator Order

When multiple decorators are used:
1. `@api.model` or `@api.model_create_multi`
2. `@api.depends`
3. `@api.constrains`
4. `@api.onchange`
5. `@api.returns`

## Best Practices

### Separation of Concerns
- Each method should have a single responsibility
- Business logic separated from UI logic
- Data validation in constraints, not in actions

### Method Size
- Compute methods: Focus on single field computation
- Action methods: Coordinate but delegate to business methods
- Business methods: Implement specific business rules
- Private methods: Reusable utilities under 20 lines

### Comments and Documentation
- Module docstring explaining purpose
- Class docstring for non-obvious models
- Method docstrings for complex business logic
- Inline comments only for non-obvious code

### Security Considerations
- CRUD methods should check access rights
- SQL queries should use parameter binding
- User input should be validated
- Sensitive data should be properly protected

## Anti-patterns to Avoid

1. **Mixed concerns in methods** - Don't combine UI, business, and data logic
2. **Computed fields without depends** - Always declare dependencies
3. **Direct SQL without security checks** - Use ORM when possible
4. **Hardcoded IDs or external references** - Use XML IDs
5. **Missing error handling** - Always handle predictable errors
6. **Fields without help text** - Add help for non-obvious fields
7. **Inconsistent naming** - Follow conventions consistently
8. **Missing constraints** - Add both Python and SQL constraints
9. **Synchronous external calls** - Use queue jobs for external APIs
10. **Missing transaction management** - Understand savepoint/rollback