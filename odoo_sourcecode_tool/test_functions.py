#!/usr/bin/env python3
"""Test module functions extraction"""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.ordering import Ordering
from core.config import Config

test_code = '''
"""Module with functions"""

def function_one():
    """First function"""
    return 1

def function_two():
    """Second function"""
    return 2

class TestClass:
    """A class"""
    pass
'''

# Parse and test
tree = ast.parse(test_code)
config = Config()
ordering = Ordering(config, test_code)
ordering.set_tree(tree)

# Check what extract_elements returns
elements = ordering.extract_elements()
print("Elements extracted:")
for key, value in elements.items():
    if value:
        print(f"  {key}: {len(value) if isinstance(value, list) else 'dict'} items")
        if key == "functions" and isinstance(value, list):
            for func in value:
                print(f"    - {func.name if hasattr(func, 'name') else 'unknown'}")

# Test reorganize_node
print("\nReorganized output:")
result = ordering.reorganize_node(tree, level="module")
print(result)
