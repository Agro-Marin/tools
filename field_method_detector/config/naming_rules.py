"""
AgroMarin Naming Rules Configuration
====================================

This module contains all the naming convention rules used by AgroMarin
for Odoo field and method transformations.

Based on AgroMarin coding guidelines for Odoo 18.0.
"""

import re
from config.settings import config

# Field Naming Rules - All AgroMarin conventions
FIELD_NAMING_RULES = [
    # Counter fields: *_count → count_* (general pattern)
    {
        "pattern": r"^(.+)_count$",
        "replacement": r"count_\1",
        "description": "Counter fields pattern",
        "examples": [
            "supplier_invoice_count → count_supplier_invoice",
            "product_count → count_product",
            "sale_order_count → count_sale_order",
            "quotations_count → count_quotations",
            "purchase_order_count → count_purchase_order",
        ],
        "field_types": ["Integer"],
        "weight": 0.9,  # Very high confidence - extremely consistent pattern in CSV
    },
    # Quantity fields: *_qty → qty_* AND qty_* variations
    {
        "pattern": r"^(.+)_qty$",
        "replacement": r"qty_\1",
        "description": "Quantity fields pattern",
        "examples": ["invoiced_qty → qty_invoiced", "ordered_qty → qty_ordered"],
        "weight": 0.8,
    },
    # HIGH CONFIDENCE Quantity field variations (AgroMarin standard)
    {
        "pattern": r"^qty_received$",
        "replacement": r"qty_transfered",
        "description": "Quantity received to transferred (AgroMarin standard)",
        "examples": ["qty_received → qty_transfered"],
        "weight": 0.95,  # High confidence - AgroMarin standard transformation
    },
    {
        "pattern": r"^qty_delivered$",
        "replacement": r"qty_transfered",
        "description": "Quantity delivered to transferred (AgroMarin standard)",
        "examples": ["qty_delivered → qty_transfered"],
        "weight": 0.95,  # High confidence - AgroMarin standard transformation
    },
    {
        "pattern": r"^product_qty$",
        "replacement": r"product_uom_qty",
        "description": "Product quantity to UOM quantity",
        "examples": ["product_qty → product_uom_qty"],
        "weight": 0.9,
    },
    # Date fields: *_date → date_* (updated with CSV patterns)
    {
        "pattern": r"^(.+)_date$",
        "replacement": r"date_\1",
        "description": "Date fields reordering pattern",
        "examples": [
            "commitment_date → date_commitment",
            "effective_date → date_effective",
            "reservation_date → date_reservation",
            "delay_alert_date → date_delay_alert",
            "order_date → date_order",
            "invoice_date → date_invoice",
        ],
        "field_types": ["Date", "Datetime"],
        "weight": 0.9,  # Increased confidence based on CSV evidence
    },
    # Date field variations
    {
        "pattern": r"^validity_date$",
        "replacement": r"date_validity",
        "description": "Validity date pattern",
        "examples": ["validity_date → date_validity"],
        "weight": 0.9,
    },
    {
        "pattern": r"^expiration_date$",
        "replacement": r"date_end",
        "description": "Expiration date to end date",
        "examples": ["expiration_date → date_end"],
        "weight": 0.8,
    },
    {
        "pattern": r"^scheduled_date$",
        "replacement": r"date_scheduled",
        "description": "Scheduled date pattern",
        "examples": ["scheduled_date → date_scheduled"],
        "weight": 0.8,
    },
    {
        "pattern": r"^forecast_expected_date$",
        "replacement": r"date_planned_forecast",
        "description": "Forecast expected date pattern",
        "examples": ["forecast_expected_date → date_planned_forecast"],
        "weight": 0.9,
    },
    {
        "pattern": r"^date_scheduled$",
        "replacement": r"date_planned",
        "description": "Scheduled to planned date",
        "examples": ["date_scheduled → date_planned"],
        "weight": 0.8,
    },
    # Amount (monetary) fields: *_amount → amount_*
    {
        "pattern": r"^(.+)_amount$",
        "replacement": r"amount_\1",
        "description": "Amount fields pattern",
        "examples": ["total_amount → amount_total", "untaxed_amount → amount_untaxed"],
        "weight": 0.8,
    },
    # HIGH CONFIDENCE Order line fields (AgroMarin standard)
    {
        "pattern": r"^order_line$",
        "replacement": r"line_ids",
        "description": "Order line to line_ids (AgroMarin standard)",
        "examples": ["order_line → line_ids"],
        "field_types": ["One2many"],
        "weight": 0.95,  # Very high confidence - standard Odoo pattern
    },
    {
        "pattern": r"^(.+)_order_line$",
        "replacement": r"\1_line_ids",
        "description": "Prefixed order line to line_ids pattern",
        "examples": [
            "purchase_order_line → purchase_line_ids",
            "sale_order_line → sale_line_ids",
        ],
        "field_types": ["One2many"],
        "weight": 0.92,
    },
    # Tax inclusive suffixes: specific monetary fields only
    {
        "pattern": r"^(amount_.+|price_.+|total_.+|untaxed_.+|taxed_.+)$",
        "replacement": r"\1_taxinc",
        "description": "Tax inclusive suffix for monetary fields",
        "examples": [
            "amount_to_invoice → amount_to_invoice_taxinc",
            "amount_invoiced → amount_invoiced_taxinc",
            "price_unit → price_unit_taxinc",
            "total_amount → total_amount_taxinc",
        ],
        "field_types": ["Monetary", "Float"],
        "weight": config.confidence_threshold
        + 0.25,  # Slightly higher confidence due to specificity
    },
    # Status/State field patterns
    {
        "pattern": r"^invoice_status$",
        "replacement": r"invoice_state",
        "description": "Invoice status to state",
        "examples": ["invoice_status → invoice_state"],
        "weight": 0.9,
    },
    # Time/Days patterns: *_days → *_time
    {
        "pattern": r"^(.+)_days$",
        "replacement": r"\1_time",
        "description": "Days to time pattern",
        "examples": ["expiration_days → expiration_time", "alert_days → alert_time"],
        "weight": 0.8,
    },
    # Free quantity pattern
    {
        "pattern": r"^free_qty_today$",
        "replacement": r"qty_free_today",
        "description": "Free quantity today pattern",
        "examples": ["free_qty_today → qty_free_today"],
        "weight": 0.9,
    },
    # Purchase line variations
    {
        "pattern": r"^purchase_line_id$",
        "replacement": r"purchase_line_ids",
        "description": "Purchase line ID to IDs",
        "examples": ["purchase_line_id → purchase_line_ids"],
        "weight": 0.8,
    },
    {
        "pattern": r"^purchase_line_ids$",
        "replacement": r"order_line_ids",
        "description": "Purchase line IDs to order line IDs",
        "examples": ["purchase_line_ids → order_line_ids"],
        "weight": 0.8,
    },
    # Typo corrections and specific fixes
    {
        "pattern": r"^order_line_idss$",
        "replacement": r"line_ids",
        "description": "Fix double s typo in order line",
        "examples": ["order_line_idss → line_ids"],
        "weight": 0.95,
    },
    {
        "pattern": r"^quotations_count$",
        "replacement": r"count_quotations",
        "description": "Quotations count pattern",
        "examples": ["quotations_count → count_quotations"],
        "weight": 0.85,
    },
    # Count field variations
    {
        "pattern": r"^supplier_invoice_count$",
        "replacement": r"count_supplier_invoice",
        "description": "Supplier invoice count",
        "examples": ["supplier_invoice_count → count_supplier_invoice"],
        "weight": 0.85,
    },
    {
        "pattern": r"^sales_count$",
        "replacement": r"count_sales",
        "description": "Sales count pattern",
        "examples": ["sales_count → count_sales"],
        "weight": 0.85,
    },
    {
        "pattern": r"^product_variant_count$",
        "replacement": r"count_product_variant",
        "description": "Product variant count",
        "examples": ["product_variant_count → count_product_variant"],
        "weight": 0.85,
    },
    # Partner/User field variations
    {
        "pattern": r"^order_partner_id$",
        "replacement": r"partner_id",
        "description": "Order partner to partner",
        "examples": ["order_partner_id → partner_id"],
        "weight": 0.8,
    },
    {
        "pattern": r"^sales_rep_id$",
        "replacement": r"user_id",
        "description": "Sales rep to user",
        "examples": ["sales_rep_id → user_id"],
        "weight": 0.8,
    },
    {
        "pattern": r"^user_id$",
        "replacement": r"salesman_id",
        "description": "User to salesman",
        "examples": ["user_id → salesman_id"],
        "weight": 0.7,
    },
    # Relational field validation patterns (validation only, no transformation)
    {
        "pattern": r"^(.+)_ids$",
        "field_types": ["One2many", "Many2many"],
        "description": "One2many/Many2many should have _ids suffix",
        "validation_only": True,
        "weight": 0.2,  # Bonus for following convention
    },
    {
        "pattern": r"^(.+)_id$",
        "field_types": ["Many2one"],
        "description": "Many2one should have _id suffix",
        "validation_only": True,
        "weight": 0.2,  # Bonus for following convention
    },
    {
        "pattern": r"^sale_orders_count$",
        "replacement": r"count_sale_orders",
        "description": "Sale orders count specific pattern",
        "examples": ["sale_orders_count → count_sale_orders"],
        "field_types": ["Integer"],
        "weight": 0.95,  # Very specific pattern
    },
    # Additional HIGH CONFIDENCE patterns for fields
    {
        "pattern": r"^(.+)_delivered$",
        "replacement": r"\1_transfered",
        "description": "General delivered to transferred pattern (fields)",
        "examples": ["product_delivered → product_transfered"],
        "weight": 0.90,
    },
    {
        "pattern": r"^(.+)_received$",
        "replacement": r"\1_transfered",
        "description": "General received to transferred pattern (fields)",
        "examples": ["product_received → product_transfered"],
        "weight": 0.90,
    },
]


# Method Naming Rules - All AgroMarin conventions
METHOD_NAMING_RULES = [
    # HIGH CONFIDENCE Compute methods
    {
        "pattern": r"^compute_(.+)$",
        "replacement": r"_compute_\1",
        "description": "Compute method pattern",
        "examples": ["compute_total → _compute_total"],
        "decorators": ["@api.depends"],
        "weight": 0.95,  # Very high confidence - standard Odoo pattern
    },
    # HIGH CONFIDENCE Quantity compute methods (AgroMarin standard)
    {
        "pattern": r"^_compute_qty_delivered$",
        "replacement": r"_compute_qty_transfered",
        "description": "Compute qty delivered to transferred (AgroMarin standard)",
        "examples": ["_compute_qty_delivered → _compute_qty_transfered"],
        "weight": 0.95,  # Very high confidence - matches field rename pattern
    },
    {
        "pattern": r"^_compute_qty_received$",
        "replacement": r"_compute_qty_transfered",
        "description": "Compute qty received to transferred (AgroMarin standard)",
        "examples": ["_compute_qty_received → _compute_qty_transfered"],
        "weight": 0.95,  # Very high confidence - matches field rename pattern
    },
    # Inverse methods: inverse_* → _inverse_*
    {
        "pattern": r"^inverse_(.+)$",
        "replacement": r"_inverse_\1",
        "description": "Inverse method pattern",
        "examples": ["inverse_name → _inverse_name"],
        "weight": 0.9,
    },
    # Search methods: search_* → _search_*
    {
        "pattern": r"^search_(.+)$",
        "replacement": r"_search_\1",
        "description": "Search method pattern",
        "examples": ["search_name → _search_name"],
        "weight": 0.9,
    },
    # Default methods: default_* → _default_*
    {
        "pattern": r"^default_(.+)$",
        "replacement": r"_default_\1",
        "description": "Default method pattern",
        "examples": ["default_state → _default_state"],
        "weight": 0.9,
    },
    # HIGH CONFIDENCE Onchange methods
    {
        "pattern": r"^onchange_(.+)$",
        "replacement": r"_onchange_\1",
        "description": "Onchange method pattern",
        "examples": ["onchange_partner → _onchange_partner"],
        "decorators": ["@api.onchange"],
        "weight": 0.95,  # Very high confidence - standard Odoo pattern
    },
    # HIGH CONFIDENCE Quantity onchange methods (AgroMarin standard)
    {
        "pattern": r"^_onchange_qty_delivered$",
        "replacement": r"_onchange_qty_transfered",
        "description": "Onchange qty delivered to transferred (AgroMarin standard)",
        "examples": ["_onchange_qty_delivered → _onchange_qty_transfered"],
        "weight": 0.95,
    },
    {
        "pattern": r"^_onchange_qty_received$",
        "replacement": r"_onchange_qty_transfered",
        "description": "Onchange qty received to transferred (AgroMarin standard)",
        "examples": ["_onchange_qty_received → _onchange_qty_transfered"],
        "weight": 0.95,
    },
    # Constraint methods: check_* → _check_* OR validate_* → _check_*
    {
        "pattern": r"^(?:check|validate)_(.+)$",
        "replacement": r"_check_\1",
        "description": "Constraint method pattern",
        "examples": ["check_date → _check_date", "validate_amount → _check_amount"],
        "decorators": ["@api.constrains"],
        "weight": 0.9,
    },
    # Action methods: * → action_* (if not already prefixed)
    {
        "pattern": r"^(?!action_)(.+)_(confirm|cancel|validate|approve|send|create|update|delete|process)$",
        "replacement": r"action_\1_\2",
        "description": "Action method pattern",
        "examples": ["order_confirm → action_order_confirm"],
        "decorators": ["@api.multi"],
        "weight": 0.7,
    },
    # Action view methods: view_* → action_view_*
    {
        "pattern": r"^(?!action_)(view_.+)$",
        "replacement": r"action_\1",
        "description": "Action view method pattern",
        "examples": ["view_draft_invoices → action_view_draft_invoices"],
        "weight": 0.8,
    },
    # Generic action methods: method_name → action_method_name (if not already prefixed and not covered by other patterns)
    {
        "pattern": r"^(?!action_|_)([a-z][a-z_]*[a-z])$",
        "replacement": r"action_\1",
        "description": "Generic action method pattern",
        "examples": [
            "view_something → action_view_something",
            "open_wizard → action_open_wizard",
        ],
        "weight": 0.6,
    },
    # Specific method transformations
    {
        "pattern": r"^_validate_order$",
        "replacement": r"_action_confirm_and_send",
        "description": "Validate order to action confirm and send",
        "examples": ["_validate_order → _action_confirm_and_send"],
        "weight": 0.9,
    },
    {
        "pattern": r"^update_order_line_ids_info$",
        "replacement": r"update_order_line_info",
        "description": "Update order line IDs info to update order line info",
        "examples": ["update_order_line_ids_info → update_order_line_info"],
        "weight": 0.9,
    },
    {
        "pattern": r"^sellable_lines_domain$",
        "replacement": r"get_lines_sellable_domain",
        "description": "Sellable lines domain to get lines sellable domain",
        "examples": ["sellable_lines_domain → get_lines_sellable_domain"],
        "weight": 0.9,
    },
    {
        "pattern": r"^get_lines_sellable_domain$",
        "replacement": r"get_domain_sellable",
        "description": "Get lines sellable domain to get domain sellable",
        "examples": ["get_lines_sellable_domain → get_domain_sellable"],
        "weight": 0.8,
    },
    {
        "pattern": r"^process_prompt_for_agent$",
        "replacement": r"execute",
        "description": "Process prompt for agent to execute",
        "examples": ["process_prompt_for_agent → execute"],
        "weight": 0.9,
    },
    # Helper methods: get_*/prepare_*/find_* → _get_*/_prepare_*/_find_*
    {
        "pattern": r"^(get|prepare|find)_(.+)$",
        "replacement": r"_\1_\2",
        "description": "Helper methods pattern",
        "examples": [
            "get_total → _get_total",
            "prepare_values → _prepare_values",
            "find_record → _find_record",
        ],
        "weight": 0.6,
    },
    # Compute method specific transformations
    {
        "pattern": r"^_compute_qty_received$",
        "replacement": r"_compute_qty_transfered",
        "description": "Compute quantity received to transferred",
        "examples": ["_compute_qty_received → _compute_qty_transfered"],
        "decorators": ["@api.depends"],
        "weight": 1.0,
    },
    {
        "pattern": r"^_compute_qty_delivered$",
        "replacement": r"_compute_qty_transfered",
        "description": "Compute quantity delivered to transferred",
        "examples": ["_compute_qty_delivered → _compute_qty_transfered"],
        "decorators": ["@api.depends"],
        "weight": 1.0,
    },
    # Real patterns from CSV analysis - Date method patterns
    {
        "pattern": r"^_compute_(.+)_date$",
        "replacement": r"_compute_date_\1",
        "description": "Compute date method reordering",
        "examples": [
            "_compute_validity_date → _compute_date_validity",
            "_compute_effective_date → _compute_date_effective",
            "_compute_delay_alert_date → _compute_date_delay_alert",
            "_compute_reservation_date → _compute_date_reservation",
        ],
        "decorators": ["@api.depends"],
        "weight": 0.9,
    },
    {
        "pattern": r"^_onchange_(.+)_date$",
        "replacement": r"_onchange_date_\1",
        "description": "Onchange date method reordering",
        "examples": [
            "_onchange_commitment_date → _onchange_date_commitment",
        ],
        "decorators": ["@api.onchange"],
        "weight": 0.9,
    },
    {
        "pattern": r"^_search_(.+)_date$",
        "replacement": r"_search_date_\1",
        "description": "Search date method reordering",
        "examples": ["_search_delay_alert_date → _search_date_delay_alert"],
        "weight": 0.9,
    },
    # Real patterns from CSV analysis - Count method patterns
    {
        "pattern": r"^_compute_(.+)_count$",
        "replacement": r"_compute_count_\1",
        "description": "Compute count method reordering",
        "examples": [
            "_compute_supplier_invoice_count → _compute_count_supplier_invoice",
            "_compute_product_count → _compute_count_product",
            "_compute_sale_order_count → _compute_count_sale_order",
            "_compute_purchase_order_count → _compute_count_purchase_order",
            "_compute_quotation_count → _compute_count_quotation",
        ],
        "decorators": ["@api.depends"],
        "weight": 0.9,  # Very consistent pattern in CSV
    },
    # Additional HIGH CONFIDENCE patterns for specific AgroMarin transformations
    {
        "pattern": r"^_compute_(.+)_delivered$",
        "replacement": r"_compute_\1_transfered",
        "description": "Compute delivered methods to transferred",
        "examples": ["_compute_product_delivered → _compute_product_transfered"],
        "weight": 0.93,
    },
    {
        "pattern": r"^_compute_(.+)_received$",
        "replacement": r"_compute_\1_transfered",
        "description": "Compute received methods to transferred",
        "examples": ["_compute_product_received → _compute_product_transfered"],
        "weight": 0.93,
    },
    {
        "pattern": r"^(.+)_delivered$",
        "replacement": r"\1_transfered",
        "description": "General delivered to transferred pattern (methods)",
        "examples": ["product_delivered → product_transfered"],
        "weight": 0.90,
    },
    {
        "pattern": r"^(.+)_received$",
        "replacement": r"\1_transfered",
        "description": "General received to transferred pattern (methods)",
        "examples": ["product_received → product_transfered"],
        "weight": 0.90,
    },
]


# API Style Detection Patterns
API_STYLE_PATTERNS = [
    # Old API → New API field types
    {
        "old_pattern": r"fields\.([a-z]+)\(",
        "new_pattern": r"fields\.([A-Z][a-z]+)\(",
        "description": "Old API to New API field type conversion",
        "examples": [
            "fields.char() → fields.Char()",
            "fields.many2one() → fields.Many2one()",
        ],
    }
]


# Contextual similarity patterns (for edge cases)
CONTEXTUAL_PATTERNS = [
    # Tree view → List view (Odoo 18.0)
    {
        "old_pattern": r"^tree$",
        "new_pattern": r"^list$",
        "description": "Tree view to List view conversion (Odoo 18.0)",
        "context": "xml_views",
        "weight": 0.95,
    },
    # Field order inversion: validity_date → date_validity
    {
        "old_pattern": r"^(.+)_(.+)$",
        "new_pattern": r"^(.+)_(.+)$",  # Match pattern, validation will check order
        "description": "Field component inversion",
        "validation": "same_components",
    },
]


class NamingRuleEngine:
    """Engine for applying and validating naming rules"""

    def __init__(self):
        self.field_rules = FIELD_NAMING_RULES
        self.method_rules = METHOD_NAMING_RULES
        self.api_patterns = API_STYLE_PATTERNS
        self.contextual_patterns = CONTEXTUAL_PATTERNS

    def apply_field_rule(
        self, old_name: str, field_type: str | None = None
    ) -> list[dict]:
        """Apply field naming rules to predict new name"""
        matches = []

        for rule in self.field_rules:
            if rule.get("validation_only", False):
                # Skip validation-only rules for prediction
                continue

            if re.match(rule["pattern"], old_name):
                predicted_name = re.sub(rule["pattern"], rule["replacement"], old_name)
                matches.append(
                    {
                        "predicted_name": predicted_name,
                        "rule": rule,
                        "confidence": rule["weight"],
                    }
                )

        return matches

    def apply_method_rule(
        self, old_name: str, decorators: list[str] | None = None
    ) -> list[dict]:
        """Apply method naming rules to predict new name"""
        matches = []

        for rule in self.method_rules:
            if re.match(rule["pattern"], old_name):
                predicted_name = re.sub(rule["pattern"], rule["replacement"], old_name)

                # Bonus if decorators match expected ones
                confidence = rule["weight"]
                if decorators and rule.get("decorators"):
                    if any(dec in decorators for dec in rule["decorators"]):
                        confidence += 0.1

                matches.append(
                    {
                        "predicted_name": predicted_name,
                        "rule": rule,
                        "confidence": min(confidence, 1.0),
                    }
                )

        return matches

    def validate_field_conventions(
        self, field_name: str, field_type: str
    ) -> list[dict]:
        """Validate field follows naming conventions"""
        validations = []

        for rule in self.field_rules:
            if not rule.get("validation_only", False):
                continue

            if rule.get("field_types") and field_type in rule["field_types"]:
                if re.match(rule["pattern"], field_name):
                    validations.append(
                        {
                            "type": "convention_followed",
                            "rule": rule["description"],
                            "bonus": rule["weight"],
                        }
                    )
                else:
                    validations.append(
                        {
                            "type": "convention_violation",
                            "rule": rule["description"],
                            "penalty": -rule["weight"],
                        }
                    )

        return validations

    def detect_api_style_change(
        self, old_definition: str, new_definition: str
    ) -> dict | None:
        """Detect Old API → New API style changes"""
        for pattern in self.api_patterns:
            old_match = re.search(pattern["old_pattern"], old_definition)
            new_match = re.search(pattern["new_pattern"], new_definition)

            if old_match and new_match:
                return {
                    "type": "api_upgrade",
                    "old_style": old_match.group(1),
                    "new_style": new_match.group(1),
                    "description": pattern["description"],
                    "bonus": 0.1,
                }

        return None

    def is_transformation(self, old_name: str, new_name: str) -> bool:
        """Check if old_name -> new_name follows a known naming rule transformation"""
        # Check field rules
        for rule in self.field_rules:
            if rule.get("validation_only", False):
                # Skip validation-only rules for transformation checking
                continue
            if re.match(rule["pattern"], old_name):
                predicted_name = re.sub(rule["pattern"], rule["replacement"], old_name)
                if predicted_name == new_name and rule["weight"] >= 0.9:
                    return True

        # Check method rules
        for rule in self.method_rules:
            if rule.get("validation_only", False):
                # Skip validation-only rules for transformation checking
                continue
            if re.match(rule["pattern"], old_name):
                predicted_name = re.sub(rule["pattern"], rule["replacement"], old_name)
                if predicted_name == new_name and rule["weight"] >= 0.9:
                    return True

        return False

    def check_contextual_similarity(self, old_name: str, new_name: str) -> dict | None:
        """Check for contextual similarity patterns"""
        for pattern in self.contextual_patterns:
            if re.match(pattern["old_pattern"], old_name) and re.match(
                pattern["new_pattern"], new_name
            ):
                if pattern.get("validation") == "same_components":
                    # Check if field components are the same
                    old_parts = set(old_name.split("_"))
                    new_parts = set(new_name.split("_"))
                    if old_parts == new_parts:
                        return {
                            "type": "contextual_match",
                            "pattern": pattern["description"],
                            "confidence": 0.6,
                        }
                else:
                    return {
                        "type": "contextual_match",
                        "pattern": pattern["description"],
                        "confidence": 0.7,
                    }

        return None

    def validate_rename(
        self,
        old_name: str,
        new_name: str,
        item_type: str,
        field_type: str | None = None,
        decorators: list[str] | None = None,
        old_definition: str = "",
        new_definition: str = "",
    ) -> dict:
        """Complete validation of a rename against all rules"""

        validation_result = {
            "follows_rule": False,
            "rule_applied": None,
            "confidence_score": 0.0,
            "scoring_breakdown": {},
            "validations": [],
            "api_changes": None,
        }

        if item_type == "field":
            # Apply field rules
            rule_matches = self.apply_field_rule(old_name, field_type)
            for match in rule_matches:
                if match["predicted_name"] == new_name:
                    validation_result["follows_rule"] = True
                    validation_result["rule_applied"] = match["rule"]["description"]
                    validation_result["scoring_breakdown"]["naming_rule"] = match[
                        "confidence"
                    ]
                    break

            # Validate conventions
            if field_type:
                conventions = self.validate_field_conventions(new_name, field_type)
                validation_result["validations"].extend(conventions)

                convention_score = sum(
                    v.get("bonus", v.get("penalty", 0)) for v in conventions
                )
                validation_result["scoring_breakdown"]["convention_compliance"] = max(
                    0, convention_score
                )

        elif item_type == "method":
            # Apply method rules
            rule_matches = self.apply_method_rule(old_name, decorators)
            for match in rule_matches:
                if match["predicted_name"] == new_name:
                    validation_result["follows_rule"] = True
                    validation_result["rule_applied"] = match["rule"]["description"]
                    validation_result["scoring_breakdown"]["naming_rule"] = match[
                        "confidence"
                    ]
                    break

        # Check API style changes
        if old_definition and new_definition:
            api_change = self.detect_api_style_change(old_definition, new_definition)
            if api_change:
                validation_result["api_changes"] = api_change
                validation_result["scoring_breakdown"]["api_consistency"] = (
                    api_change.get("bonus", 0)
                )

        # Check contextual similarity if no rule matched
        if not validation_result["follows_rule"]:
            contextual = self.check_contextual_similarity(old_name, new_name)
            if contextual:
                validation_result["rule_applied"] = contextual["pattern"]
                validation_result["scoring_breakdown"]["contextual_match"] = contextual[
                    "confidence"
                ]

        # Calculate final confidence score
        base_scores = validation_result["scoring_breakdown"]
        total_confidence = sum(base_scores.values())

        # Add base signature match score if not already included
        if validation_result.get("follows_rule"):
            total_confidence += 0.4  # Base signature match score

        validation_result["confidence_score"] = min(total_confidence, 1.0)  # Cap at 1.0
        validation_result["confidence"] = validation_result[
            "confidence_score"
        ]  # Alias for consistency

        return validation_result


# Global instance
naming_engine = NamingRuleEngine()
