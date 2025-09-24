"""
Ordering rules and templates for Odoo source code organization.

This module contains all configuration for:
- Python code ordering (methods, fields, attributes)
- XML element and attribute ordering
- Section headers and formatting
"""

# ============================================================
# PYTHON MODEL ATTRIBUTE ORDERING
# ============================================================

MODEL_ATTRIBUTES = [
    "_name",
    "_inherit",
    "_inherits",
    "_description",
    "_table",
    "_rec_name",
    "_order",
    "_check_company_auto",
    "_sql_constraints",
    "_inherit_children",
    "_parent_name",
    "_parent_store",
    "_parent_order",
    "_date_name",
    "_fold_name",
]

# ============================================================
# FIELD ATTRIBUTE ORDERING
# ============================================================

# Type-specific attributes that should come first
FIELD_TYPE_ATTRIBUTES = {
    "Boolean": [],
    "Char": ["size"],
    "Text": [],
    "Integer": [],
    "Float": ["digits"],
    "Monetary": ["currency_field"],
    "Date": [],
    "Datetime": [],
    "Binary": ["attachment"],
    "Selection": ["selection", "selection_add"],
    "Many2one": ["comodel_name", "ondelete", "domain"],
    "One2many": ["comodel_name", "inverse_name", "domain"],
    "Many2many": [
        "comodel_name",
        "relation",
        "column1",
        "column2",
        "domain",
    ],
    "Reference": ["selection"],
    "Html": ["sanitize", "sanitize_tags", "sanitize_attributes"],
    "Json": [],
}

# Generic field attributes in preferred order
FIELD_ATTRIBUTE_GENERIC = [
    # Core attributes
    "string",
    "help",
    "required",
    "readonly",
    "store",
    "index",
    "copy",
    "groups",
    "states",
    # Computation
    "compute",
    "inverse",
    "search",
    "related",
    "depends",
    "recursive",
    "compute_sudo",
    # Defaults and context
    "default",
    "context",
    # Tracking and UI
    "tracking",
    "change_default",
    # Delegation and inheritance
    "delegate",
    "inherited",
    # Company-related
    "company_dependent",
    "check_company",
]

# ============================================================
# PYTHON METHOD ORDERING
# ============================================================

SECTION_HEADERS = [
    "INHERITANCE",
    "FIELDS",
    "DEFAULTS",
    "COMPUTE",
    "CONSTRAINT",
    "ONCHANGE",
    "CRUD",
    "API_MODEL",
    "API_DEPENDS",
    "ACTIONS",
    "BUSINESS",
    "HELPERS",
    "PRIVATE",
    "INTERNAL",
    "OVERRIDES",
    "DEPRECATED",
]

METHOD_ORDER = {
    "INHERITANCE": 0,
    "FIELDS": 1,
    "DEFAULTS": 2,
    "COMPUTE": 3,
    "CONSTRAINT": 4,
    "ONCHANGE": 5,
    "CRUD": 6,
    "API_MODEL": 7,
    "API_DEPENDS": 8,
    "ACTIONS": 9,
    "BUSINESS": 10,
    "HELPERS": 11,
    "PRIVATE": 12,
    "INTERNAL": 13,
    "OVERRIDES": 14,
    "DEPRECATED": 15,
}

# ============================================================
# XML ATTRIBUTE ORDERING
# ============================================================


def get_xml_attribute_orders() -> dict[str, list[str]]:
    """Get XML attribute orders for different element types.

    Returns:
        Dictionary mapping element types to ordered attribute lists
    """
    return {
        # Default order for any element
        "_default": [
            "id",
            "name",
            "model",
            "string",
            "type",
            "class",
            "position",
            "attrs",
            "states",
            "invisible",
            "readonly",
            "required",
        ],
        # Specific orders for Odoo XML elements
        "record": ["id", "model", "forcecreate"],
        "field": [
            "name",
            "type",
            "string",
            "widget",
            "required",
            "readonly",
            "invisible",
            "attrs",
            "states",
            "help",
            "placeholder",
        ],
        "button": [
            "name",
            "string",
            "type",
            "class",
            "icon",
            "states",
            "attrs",
            "invisible",
            "confirm",
            "context",
        ],
        "tree": [
            "string",
            "default_order",
            "create",
            "edit",
            "delete",
            "duplicate",
            "import",
            "export_xlsx",
            "multi_edit",
            "sample",
        ],
        "form": ["string", "create", "edit", "delete", "duplicate"],
        "kanban": [
            "default_group_by",
            "class",
            "sample",
            "quick_create",
            "quick_create_view",
        ],
        "search": ["string"],
        "group": ["name", "string", "col", "colspan", "attrs", "invisible"],
        "notebook": ["colspan", "attrs", "invisible"],
        "page": ["name", "string", "attrs", "invisible"],
        "xpath": ["expr", "position"],
        "attribute": ["name"],
        "div": ["class", "attrs", "invisible"],
        "span": ["class", "attrs", "invisible"],
        "t": [
            "t-if",
            "t-elif",
            "t-else",
            "t-foreach",
            "t-as",
            "t-esc",
            "t-raw",
            "t-field",
            "t-options",
            "t-set",
            "t-value",
            "t-call",
            "t-call-assets",
        ],
        "template": ["id", "name", "inherit_id", "priority"],
        "menuitem": ["id", "name", "parent", "sequence", "action", "groups"],
        "act_window": ["id", "name", "model", "view_mode", "domain", "context"],
    }


# ============================================================
# VIEW STRUCTURE TEMPLATES
# ============================================================

FORM_VIEW_STRUCTURE = {
    "sections": ["header", "sheet", "chatter"],
    "sheet_order": ["title", "main_groups", "notebook", "footer_groups"],
    "title_elements": ["h1", "h2", "div.o_title"],
    "chatter_fields": ["message_follower_ids", "activity_ids", "message_ids"],
}

TREE_VIEW_STRUCTURE = {
    "sections": ["control", "buttons", "fields", "widgets"],
    "control_elements": ["control"],
    "widget_types": ["widget", "progressbar", "badge"],
}

SEARCH_VIEW_STRUCTURE = {
    "sections": ["fields", "filters", "separators", "groups"],
    "separator_after_filters": True,
    "group_prefix": "group_by_",
}

KANBAN_VIEW_STRUCTURE = {
    "sections": ["progressbar", "fields", "control", "templates"],
    "template_names": ["kanban-box"],
}
