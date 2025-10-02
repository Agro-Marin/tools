#!/usr/bin/env python3
"""
Test AST visitor inheritance detection for sale.order
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from analyzers.ast_visitor import extract_models

def test_file(file_path: str):
    """Test inheritance detection for a file"""
    print(f"\n{'='*80}")
    print(f"Testing: {file_path}")
    print('='*80)

    with open(file_path, 'r') as f:
        content = f.read()

    models = extract_models(content, file_path)

    print(f"Found {len(models)} models:")
    for model in models:
        print(f"\n  Model: {model.name}")
        print(f"    Inheritance Type: {model.inheritance_type.value}")
        print(f"    Inherits From: {model.inherits_from}")
        print(f"    Methods: {len(model.methods)}")

        # Check for _action_confirm method
        action_confirm = [m for m in model.methods if '_action_confirm' in m.name or 'action_confirm' in m.name]
        if action_confirm:
            print(f"    Has action_confirm methods:")
            for method in action_confirm:
                print(f"      - {method.name}")

if __name__ == "__main__":
    # Test sale module (should be NAME)
    test_file("/home/suniagajose/Instancias/odoo/addons/sale/models/sale_order.py")

    # Test delivery module (should be INHERIT)
    test_file("/home/suniagajose/Instancias/odoo/addons/delivery/models/sale_order.py")
