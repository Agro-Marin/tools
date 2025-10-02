#!/usr/bin/env python3
"""
Test script for inheritance-based change classification.

Tests the specific case of sale.order where multiple modules
(_action_cancel -> action_cancel) extend the same model.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.models import Model, Method, RenameCandidate, InheritanceType
from analyzers.inheritance_graph import InheritanceGraph, build_inheritance_graph
from analyzers.matching_engine import MatchingEngine


def create_test_models():
    """Create test models simulating sale.order across modules"""

    # sale.order in 'sale' module (base module with _name)
    sale_base = Model(
        name="sale.order",
        class_name="SaleOrder",
        file_path="/odoo/addons/sale/models/sale_order.py",
        line_number=10,
        inheritance_type=InheritanceType.NAME,
        inherits_from=[],
        fields=[],
        methods=[
            Method(
                name="action_cancel",  # New name (was _action_cancel)
                args=["self"],
                decorators=[],
                signature="def action_cancel(self)",
                definition="",
                line_number=100,
                source_file="/odoo/addons/sale/models/sale_order.py",
            )
        ],
        references=[],
    )

    # sale.order in 'sale_loyalty' module (extends with _inherit)
    sale_loyalty = Model(
        name="sale.order",
        class_name="SaleOrder",
        file_path="/odoo/addons/sale_loyalty/models/sale_order.py",
        line_number=10,
        inheritance_type=InheritanceType.INHERIT,
        inherits_from=["sale.order"],
        fields=[],
        methods=[
            Method(
                name="action_cancel",  # Same change
                args=["self"],
                decorators=[],
                signature="def action_cancel(self)",
                definition="",
                line_number=50,
                source_file="/odoo/addons/sale_loyalty/models/sale_order.py",
            )
        ],
        references=[],
    )

    # sale.order in 'sale_purchase' module (extends with _inherit)
    sale_purchase = Model(
        name="sale.order",
        class_name="SaleOrder",
        file_path="/odoo/addons/sale_purchase/models/sale_order.py",
        line_number=10,
        inheritance_type=InheritanceType.INHERIT,
        inherits_from=["sale.order"],
        fields=[],
        methods=[
            Method(
                name="action_cancel",  # Same change
                args=["self"],
                decorators=[],
                signature="def action_cancel(self)",
                definition="",
                line_number=75,
                source_file="/odoo/addons/sale_purchase/models/sale_order.py",
            )
        ],
        references=[],
    )

    # sale.order in 'sale_stock' module (extends with _inherit)
    sale_stock = Model(
        name="sale.order",
        class_name="SaleOrder",
        file_path="/odoo/addons/sale_stock/models/sale_order.py",
        line_number=10,
        inheritance_type=InheritanceType.INHERIT,
        inherits_from=["sale.order"],
        fields=[],
        methods=[
            Method(
                name="action_cancel",  # Same change
                args=["self"],
                decorators=[],
                signature="def action_cancel(self)",
                definition="",
                line_number=120,
                source_file="/odoo/addons/sale_stock/models/sale_order.py",
            )
        ],
        references=[],
    )

    return {
        "sale": [sale_base],
        "sale_loyalty": [sale_loyalty],
        "sale_purchase": [sale_purchase],
        "sale_stock": [sale_stock],
    }


def create_test_candidates():
    """Create test rename candidates simulating detected changes"""
    candidates = [
        RenameCandidate(
            change_id="1",
            old_name="_action_cancel",
            new_name="action_cancel",
            item_type="method",
            module="sale",
            model="sale.order",
            change_scope="declaration",
            impact_type="primary",
            context="",
            confidence=1.0,
            parent_change_id="",
            validation_status="auto_approved",
            source_file="/odoo/addons/sale/models/sale_order.py",
            line_number=100,
        ),
        RenameCandidate(
            change_id="2",
            old_name="_action_cancel",
            new_name="action_cancel",
            item_type="method",
            module="sale_loyalty",
            model="sale.order",
            change_scope="declaration",  # Should be super_call
            impact_type="primary",  # Should be inheritance
            context="",
            confidence=1.0,
            parent_change_id="",  # Should be "1"
            validation_status="auto_approved",
            source_file="/odoo/addons/sale_loyalty/models/sale_order.py",
            line_number=50,
        ),
        RenameCandidate(
            change_id="3",
            old_name="_action_cancel",
            new_name="action_cancel",
            item_type="method",
            module="sale_purchase",
            model="sale.order",
            change_scope="declaration",  # Should be super_call
            impact_type="primary",  # Should be inheritance
            context="",
            confidence=1.0,
            parent_change_id="",  # Should be "1"
            validation_status="auto_approved",
            source_file="/odoo/addons/sale_purchase/models/sale_order.py",
            line_number=75,
        ),
        RenameCandidate(
            change_id="4",
            old_name="_action_cancel",
            new_name="action_cancel",
            item_type="method",
            module="sale_stock",
            model="sale.order",
            change_scope="declaration",  # Should be super_call
            impact_type="primary",  # Should be inheritance
            context="",
            confidence=1.0,
            parent_change_id="",  # Should be "1"
            validation_status="auto_approved",
            source_file="/odoo/addons/sale_stock/models/sale_order.py",
            line_number=120,
        ),
    ]
    return candidates


def test_inheritance_classification():
    """Test the inheritance classification system"""
    print("=" * 80)
    print("Testing Inheritance-based Change Classification")
    print("=" * 80)

    # Step 1: Create test models
    print("\n1. Creating test models (sale, sale_loyalty, sale_purchase, sale_stock)...")
    all_models = create_test_models()
    print(f"   ✓ Created {sum(len(models) for models in all_models.values())} models")

    # Step 2: Build inheritance graph
    print("\n2. Building inheritance graph...")
    inheritance_graph = build_inheritance_graph(all_models)
    inheritance_graph.print_summary()

    # Step 3: Verify inheritance relationships
    print("\n3. Verifying inheritance relationships:")
    base_module = inheritance_graph.get_base_module("sale.order")
    extension_modules = inheritance_graph.get_extension_modules("sale.order")

    print(f"   Base module: {base_module}")
    print(f"   Extension modules: {extension_modules}")

    assert base_module == "sale", f"Expected base module 'sale', got '{base_module}'"
    assert set(extension_modules) == {
        "sale_loyalty",
        "sale_purchase",
        "sale_stock",
    }, f"Unexpected extension modules: {extension_modules}"
    print("   ✓ Inheritance relationships correct")

    # Step 4: Create test candidates
    print("\n4. Creating test candidates (before reclassification):")
    candidates = create_test_candidates()
    for c in candidates:
        print(
            f"   {c.change_id}. {c.module:15} | {c.change_scope:12} | {c.impact_type:12} | parent: {c.parent_change_id or 'none'}"
        )

    # Step 5: Reclassify using MatchingEngine
    print("\n5. Reclassifying candidates with MatchingEngine...")
    engine = MatchingEngine(inheritance_graph=inheritance_graph)
    reclassified = engine.reclassify_inherited_changes(candidates)

    # Step 6: Verify reclassification
    print("\n6. After reclassification:")
    primary_count = 0
    inheritance_count = 0

    for c in reclassified:
        is_primary = c.change_scope == "declaration" and c.impact_type == "primary"
        is_inheritance = c.change_scope == "super_call" and c.impact_type == "inheritance"

        status = "✓ PRIMARY" if is_primary else "✓ INHERITED" if is_inheritance else "✗ UNKNOWN"
        print(
            f"   {c.change_id}. {c.module:15} | {c.change_scope:12} | {c.impact_type:12} | parent: {c.parent_change_id or 'none':4} | {status}"
        )

        if is_primary:
            primary_count += 1
        if is_inheritance:
            inheritance_count += 1

    # Step 7: Validate results
    print("\n7. Validation:")
    print(f"   Primary changes: {primary_count}")
    print(f"   Inherited changes: {inheritance_count}")

    success = True
    if primary_count != 1:
        print(f"   ✗ FAIL: Expected 1 primary change, got {primary_count}")
        success = False
    else:
        print(f"   ✓ PASS: Exactly 1 primary change (base module)")

    if inheritance_count != 3:
        print(f"   ✗ FAIL: Expected 3 inherited changes, got {inheritance_count}")
        success = False
    else:
        print(f"   ✓ PASS: Exactly 3 inherited changes (extension modules)")

    # Verify parent relationships
    print("\n8. Verifying parent relationships:")
    primary = next(c for c in reclassified if c.module == "sale")
    extensions = [c for c in reclassified if c.module != "sale"]

    for ext in extensions:
        if ext.parent_change_id == primary.change_id:
            print(f"   ✓ {ext.module} correctly references parent '{primary.change_id}'")
        else:
            print(
                f"   ✗ {ext.module} has wrong parent '{ext.parent_change_id}' (expected '{primary.change_id}')"
            )
            success = False

    # Final result
    print("\n" + "=" * 80)
    if success:
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(test_inheritance_classification())
