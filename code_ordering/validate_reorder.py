#!/usr/bin/env python3
"""
Validation Tool for Odoo Code Reordering

This tool validates that the reordering process preserves all code elements.
It compares an original file with its reordered version to ensure:
- All imports are preserved
- All classes are preserved
- All fields are preserved
- All methods are preserved
- All functions are preserved
- All module-level variables are preserved

Usage:
    python validate_reorder.py original.py reordered.py [--order order.json]

Author: Agromarin Tools
Version: 1.0.0
"""

import argparse
import ast
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ElementInfo:
    """Information about a code element."""

    name: str
    type: str
    line_number: int
    source: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of validation comparison."""

    is_valid: bool = True
    original_count: Dict[str, int] = field(default_factory=dict)
    reordered_count: Dict[str, int] = field(default_factory=dict)
    missing: Dict[str, List[str]] = field(default_factory=dict)
    added: Dict[str, List[str]] = field(default_factory=dict)
    order_changes: Dict[str, Dict] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class CodeAnalyzer:
    """Analyzes Python code to extract all elements."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.content = filepath.read_text(encoding="utf-8")
        self.tree = ast.parse(self.content)
        self.lines = self.content.splitlines()

    def extract_all_elements(self) -> Dict[str, List[ElementInfo]]:
        """Extract all code elements from the file."""
        elements = {
            "imports": [],
            "classes": [],
            "functions": [],
            "variables": [],
            "fields": [],
            "methods": [],
            "decorators": [],
            "assignments": [],
        }

        # Extract imports
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    elements["imports"].append(
                        ElementInfo(
                            name=alias.name, type="import", line_number=node.lineno
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    import_name = f"from {module} import {alias.name}"
                    elements["imports"].append(
                        ElementInfo(
                            name=import_name,
                            type="import_from",
                            line_number=node.lineno,
                        )
                    )

        # Extract top-level elements
        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node)
                elements["classes"].append(class_info)

                # Extract class contents
                for class_node in node.body:
                    if isinstance(class_node, ast.FunctionDef):
                        method_info = self._extract_function_info(class_node)
                        method_info.type = f"method_of_{node.name}"
                        elements["methods"].append(method_info)
                    elif isinstance(class_node, ast.Assign):
                        for target in class_node.targets:
                            if isinstance(target, ast.Name):
                                field_info = ElementInfo(
                                    name=f"{node.name}.{target.id}",
                                    type=f"field_of_{node.name}",
                                    line_number=class_node.lineno,
                                )
                                elements["fields"].append(field_info)

            elif isinstance(node, ast.FunctionDef):
                func_info = self._extract_function_info(node)
                elements["functions"].append(func_info)

            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_info = ElementInfo(
                            name=target.id,
                            type="module_variable",
                            line_number=node.lineno,
                        )
                        elements["variables"].append(var_info)

        return elements

    def _extract_class_info(self, node: ast.ClassDef) -> ElementInfo:
        """Extract information about a class."""
        decorators = [ast.unparse(d) for d in node.decorator_list]
        bases = [ast.unparse(b) for b in node.bases]

        return ElementInfo(
            name=node.name,
            type="class",
            line_number=node.lineno,
            decorators=decorators,
            parameters=bases,
        )

    def _extract_function_info(self, node: ast.FunctionDef) -> ElementInfo:
        """Extract information about a function or method."""
        decorators = [ast.unparse(d) for d in node.decorator_list]
        params = [arg.arg for arg in node.args.args]

        return ElementInfo(
            name=node.name,
            type="function",
            line_number=node.lineno,
            decorators=decorators,
            parameters=params,
        )


class ReorderValidator:
    """Validates that reordering preserves all code elements."""

    def __init__(
        self,
        original_file: Path,
        reordered_file: Path,
        order_file: Optional[Path] = None,
    ):
        self.original_file = original_file
        self.reordered_file = reordered_file
        self.order_file = order_file
        self.result = ValidationResult()

    def validate(self) -> ValidationResult:
        """Perform complete validation."""
        logger.info(f"Validating: {self.original_file} vs {self.reordered_file}")

        try:
            # Analyze both files
            original_analyzer = CodeAnalyzer(self.original_file)
            reordered_analyzer = CodeAnalyzer(self.reordered_file)

            original_elements = original_analyzer.extract_all_elements()
            reordered_elements = reordered_analyzer.extract_all_elements()

            # Compare each element type
            for element_type in original_elements:
                self._compare_elements(
                    element_type,
                    original_elements[element_type],
                    reordered_elements[element_type],
                )

            # Load and analyze order file if provided
            if self.order_file and self.order_file.exists():
                self._analyze_order_compliance(self.order_file)

            # Generate summary
            self._generate_summary()

        except Exception as e:
            self.result.is_valid = False
            self.result.errors.append(f"Validation error: {str(e)}")
            logger.error(f"Validation failed: {e}")

        return self.result

    def _compare_elements(
        self,
        element_type: str,
        original: List[ElementInfo],
        reordered: List[ElementInfo],
    ):
        """Compare elements of a specific type."""
        original_names = {elem.name for elem in original}
        reordered_names = {elem.name for elem in reordered}

        # Count elements
        self.result.original_count[element_type] = len(original_names)
        self.result.reordered_count[element_type] = len(reordered_names)

        # Find missing elements
        missing = original_names - reordered_names
        if missing:
            self.result.missing[element_type] = sorted(missing)
            self.result.is_valid = False
            self.result.errors.append(f"Missing {element_type}: {missing}")

        # Find added elements
        added = reordered_names - original_names
        if added:
            self.result.added[element_type] = sorted(added)
            self.result.warnings.append(f"Added {element_type}: {added}")

        # Check order changes
        if original_names == reordered_names and len(original_names) > 1:
            original_order = [elem.name for elem in original]
            reordered_order = [elem.name for elem in reordered]

            if original_order != reordered_order:
                self.result.order_changes[element_type] = {
                    "original": original_order[:10],  # First 10 for brevity
                    "reordered": reordered_order[:10],
                    "total_reordered": sum(
                        1
                        for i, (o, r) in enumerate(zip(original_order, reordered_order))
                        if o != r
                    ),
                }

    def _analyze_order_compliance(self, order_file: Path):
        """Analyze if the reordering follows the specified order."""
        try:
            with open(order_file, "r") as f:
                order_data = json.load(f)

            # Add order compliance analysis here if needed
            self.result.warnings.append(f"Order file loaded: {order_file.name}")

        except Exception as e:
            self.result.warnings.append(f"Could not analyze order file: {e}")

    def _generate_summary(self):
        """Generate validation summary."""
        if self.result.is_valid:
            logger.info("✅ VALIDATION PASSED: All elements preserved")
        else:
            logger.error("❌ VALIDATION FAILED: Missing elements detected")

        # Log statistics
        logger.info("\nElement counts:")
        logger.info("  Type          | Original | Reordered | Status")
        logger.info("  --------------|----------|-----------|--------")

        for element_type in self.result.original_count:
            orig_count = self.result.original_count[element_type]
            reord_count = self.result.reordered_count.get(element_type, 0)
            status = "✅" if orig_count == reord_count else "❌"
            logger.info(
                f"  {element_type:13} | {orig_count:8} | {reord_count:9} | {status}"
            )

        # Log errors
        if self.result.errors:
            logger.error("\nErrors:")
            for error in self.result.errors:
                logger.error(f"  - {error}")

        # Log warnings
        if self.result.warnings:
            logger.warning("\nWarnings:")
            for warning in self.result.warnings:
                logger.warning(f"  - {warning}")

        # Log order changes
        if self.result.order_changes:
            logger.info("\nOrder changes detected (this is expected):")
            for element_type, changes in self.result.order_changes.items():
                logger.info(
                    f"  - {element_type}: {changes.get('total_reordered', 0)} elements reordered"
                )


def main():
    """Main entry point for the validation tool."""
    parser = argparse.ArgumentParser(
        description="Validate Odoo code reordering preserves all elements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("original", help="Path to the original file (or backup)")
    parser.add_argument("reordered", help="Path to the reordered file")
    parser.add_argument(
        "--order", help="Path to the order JSON file used for reordering"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Validate files exist
    original_file = Path(args.original)
    reordered_file = Path(args.reordered)

    if not original_file.exists():
        logger.error(f"Original file not found: {original_file}")
        sys.exit(1)

    if not reordered_file.exists():
        logger.error(f"Reordered file not found: {reordered_file}")
        sys.exit(1)

    order_file = Path(args.order) if args.order else None
    if order_file and not order_file.exists():
        logger.warning(f"Order file not found: {order_file}")
        order_file = None

    # Run validation
    validator = ReorderValidator(original_file, reordered_file, order_file)
    result = validator.validate()

    # Output JSON if requested
    if args.json:
        output = {
            "is_valid": result.is_valid,
            "original_count": result.original_count,
            "reordered_count": result.reordered_count,
            "missing": result.missing,
            "added": result.added,
            "errors": result.errors,
            "warnings": result.warnings,
        }
        print(json.dumps(output, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
