"""
CSV Structure Validator
=======================

Validates the integrity of CSV files with cross-reference structure,
ensuring data consistency and proper parent-child relationships.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Set
from config.settings import config

logger = logging.getLogger(__name__)


class CSVStructureValidator:
    """Validates CSV structure and data integrity"""

    # Required fields that must be present and non-empty
    REQUIRED_FIELDS = [
        "change_id",
        "old_name",
        "new_name",
        "item_type",
        "module",
        "model",
        "change_scope",
        "impact_type",
        "confidence",
    ]

    # Valid enum values for each field
    VALID_ENUMS = {
        "item_type": ["field", "method"],
        "change_scope": ["declaration", "reference", "call", "super_call"],
        "impact_type": [
            "primary",
            "self_reference",
            "self_call",
            "cross_model",
            "cross_model_call",
            "inheritance",
            "decorator",
        ],
    }

    # Fields that require context when certain conditions are met
    CONTEXT_REQUIRED_SCOPES = ["reference", "call", "super_call"]

    def __init__(self, csv_file_path: str):
        """
        Initialize validator.

        Args:
            csv_file_path: Path to the CSV file to validate
        """
        self.csv_file_path = Path(csv_file_path)

    def validate_csv_structure(self) -> Dict[str, any]:
        """
        Validate CSV structure and return comprehensive report.

        Returns:
            Dictionary with validation results and statistics
        """
        if not self.csv_file_path.exists():
            return {
                "valid": False,
                "error": f"File does not exist: {self.csv_file_path}",
                "file_path": str(self.csv_file_path),
            }

        try:
            errors = []
            warnings = []
            statistics = {}

            with open(self.csv_file_path, "r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)

                # Validate headers
                header_errors = self._validate_headers(reader.fieldnames)
                errors.extend(header_errors)

                # If headers are invalid, stop validation
                if header_errors:
                    return {
                        "valid": False,
                        "errors": errors,
                        "file_path": str(self.csv_file_path),
                    }

                # Validate data rows
                rows_data = list(reader)
                row_errors, row_warnings, stats = self._validate_rows(rows_data)
                errors.extend(row_errors)
                warnings.extend(row_warnings)
                statistics.update(stats)

                # Validate relationships
                relationship_errors = self._validate_relationships(rows_data)
                errors.extend(relationship_errors)

            # Create validation report
            report = {
                "valid": len(errors) == 0,
                "file_path": str(self.csv_file_path),
                "file_size": self.csv_file_path.stat().st_size,
                "total_errors": len(errors),
                "total_warnings": len(warnings),
                "errors": errors,
                "warnings": warnings,
                "statistics": statistics,
            }

            # Log results
            if report["valid"]:
                logger.info(f"CSV validation passed: {self.csv_file_path}")
                if warnings:
                    logger.warning(f"CSV validation has {len(warnings)} warnings")
            else:
                logger.error(
                    f"CSV validation failed: {len(errors)} errors, {len(warnings)} warnings"
                )

            return report

        except Exception as e:
            return {
                "valid": False,
                "error": f"Exception during validation: {str(e)}",
                "file_path": str(self.csv_file_path),
            }

    def _validate_headers(self, fieldnames: List[str]) -> List[str]:
        """Validate CSV headers"""
        errors = []

        if not fieldnames:
            errors.append("No headers found in CSV file")
            return errors

        # Check for missing required fields
        missing_fields = set(self.REQUIRED_FIELDS) - set(fieldnames)
        if missing_fields:
            errors.append(f"Missing required headers: {sorted(missing_fields)}")

        # Check for unexpected fields (warnings, not errors)
        expected_headers = set(self.REQUIRED_FIELDS + ["parent_change_id", "context"])
        unexpected_fields = set(fieldnames) - expected_headers
        if unexpected_fields:
            # This is just informational, not an error
            logger.info(
                f"Unexpected headers found (may be legacy): {sorted(unexpected_fields)}"
            )

        return errors

    def _validate_rows(
        self, rows: List[Dict[str, str]]
    ) -> tuple[List[str], List[str], Dict[str, any]]:
        """Validate individual rows and collect statistics"""
        errors = []
        warnings = []

        # Statistics tracking
        stats = {
            "total_rows": len(rows),
            "primary_changes": 0,
            "impact_changes": 0,
            "change_scope_distribution": {},
            "impact_type_distribution": {},
            "module_distribution": {},
            "model_distribution": {},
            "avg_confidence": 0.0,
            "confidence_ranges": {"high": 0, "medium": 0, "low": 0},
        }

        confidence_sum = 0
        valid_confidence_count = 0

        for row_num, row in enumerate(rows, start=2):  # Start at 2 (header is row 1)
            # Validate required fields
            for field in self.REQUIRED_FIELDS:
                value = row.get(field, "").strip()
                if not value:
                    errors.append(f"Row {row_num}: Missing required field '{field}'")

            # Validate enum values
            for field, valid_values in self.VALID_ENUMS.items():
                value = row.get(field, "").strip()
                if value and value not in valid_values:
                    errors.append(
                        f"Row {row_num}: Invalid {field} '{value}'. Valid: {valid_values}"
                    )

            # Validate confidence range
            confidence_str = row.get("confidence", "").strip()
            if confidence_str:
                try:
                    confidence = float(confidence_str)
                    if confidence < 0.0 or confidence > 1.0:
                        errors.append(
                            f"Row {row_num}: Confidence must be 0.0-1.0, got {confidence}"
                        )
                    else:
                        confidence_sum += confidence
                        valid_confidence_count += 1

                        # Confidence ranges
                        if confidence >= 0.90:
                            stats["confidence_ranges"]["high"] += 1
                        elif confidence >= config.confidence_threshold:
                            stats["confidence_ranges"]["medium"] += 1
                        else:
                            stats["confidence_ranges"]["low"] += 1

                except ValueError:
                    errors.append(
                        f"Row {row_num}: Invalid confidence value '{confidence_str}'"
                    )

            # Validate context requirements
            change_scope = row.get("change_scope", "").strip()
            context = row.get("context", "").strip()
            if change_scope in self.CONTEXT_REQUIRED_SCOPES and not context:
                warnings.append(
                    f"Row {row_num}: Context recommended for change_scope '{change_scope}'"
                )

            # Validate logical consistency
            impact_type = row.get("impact_type", "").strip()
            parent_change_id = row.get("parent_change_id", "").strip()

            if impact_type == "primary" and parent_change_id:
                warnings.append(
                    f"Row {row_num}: Primary changes should not have parent_change_id"
                )
            elif impact_type != "primary" and not parent_change_id:
                errors.append(
                    f"Row {row_num}: Non-primary changes must have parent_change_id"
                )

            # Collect statistics
            if impact_type == "primary":
                stats["primary_changes"] += 1
            else:
                stats["impact_changes"] += 1

            # Distribution statistics
            for field, dist_key in [
                ("change_scope", "change_scope_distribution"),
                ("impact_type", "impact_type_distribution"),
                ("module", "module_distribution"),
                ("model", "model_distribution"),
            ]:
                value = row.get(field, "").strip()
                if value:
                    stats[dist_key][value] = stats[dist_key].get(value, 0) + 1

        # Calculate average confidence
        if valid_confidence_count > 0:
            stats["avg_confidence"] = confidence_sum / valid_confidence_count

        return errors, warnings, stats

    def _validate_relationships(self, rows: List[Dict[str, str]]) -> List[str]:
        """Validate parent-child relationships"""
        errors = []

        # Collect all change_ids and parent_change_ids
        change_ids: Set[str] = set()
        parent_change_ids: Set[str] = set()

        for row_num, row in enumerate(rows, start=2):
            change_id = row.get("change_id", "").strip()
            parent_change_id = row.get("parent_change_id", "").strip()
            impact_type = row.get("impact_type", "").strip()

            if change_id:
                if change_id in change_ids:
                    errors.append(f"Row {row_num}: Duplicate change_id '{change_id}'")
                else:
                    change_ids.add(change_id)

            if parent_change_id:
                parent_change_ids.add(parent_change_id)

        # Check for orphaned references
        orphaned_parents = parent_change_ids - change_ids
        if orphaned_parents:
            errors.append(
                f"Orphaned parent_change_ids (no corresponding primary change): {sorted(orphaned_parents)}"
            )

        # Check for primary changes without impacts (informational)
        primary_ids = {
            row.get("change_id", "").strip()
            for row in rows
            if row.get("impact_type", "").strip() == "primary"
        }
        referenced_parents = parent_change_ids

        unused_primaries = primary_ids - referenced_parents
        if unused_primaries:
            # This is informational, not an error - some primary changes may not have impacts
            logger.info(
                f"Primary changes without impacts: {len(unused_primaries)} changes"
            )

        return errors

    def generate_validation_report(self, output_file: str = None) -> bool:
        """
        Generate detailed validation report and save to file.

        Args:
            output_file: Path to save report file

        Returns:
            True if successful
        """
        validation_result = self.validate_csv_structure()

        output_path = (
            Path(output_file)
            if output_file
            else self.csv_file_path.with_suffix(".validation.txt")
        )

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("CSV Structure Validation Report\n")
                f.write("=" * 40 + "\n\n")

                f.write(f"File: {validation_result['file_path']}\n")
                f.write(
                    f"File Size: {validation_result.get('file_size', 'Unknown')} bytes\n"
                )
                f.write(
                    f"Validation Status: {'PASS' if validation_result['valid'] else 'FAIL'}\n\n"
                )

                # Statistics
                if "statistics" in validation_result:
                    stats = validation_result["statistics"]
                    f.write("Statistics:\n")
                    f.write(f"  Total Rows: {stats['total_rows']}\n")
                    f.write(f"  Primary Changes: {stats['primary_changes']}\n")
                    f.write(f"  Impact Changes: {stats['impact_changes']}\n")
                    f.write(f"  Average Confidence: {stats['avg_confidence']:.3f}\n")
                    f.write(
                        f"  Confidence Distribution: High={stats['confidence_ranges']['high']}, Medium={stats['confidence_ranges']['medium']}, Low={stats['confidence_ranges']['low']}\n\n"
                    )

                # Errors
                if validation_result.get("errors"):
                    f.write(f"Errors ({len(validation_result['errors'])}):\n")
                    for error in validation_result["errors"]:
                        f.write(f"  ❌ {error}\n")
                    f.write("\n")

                # Warnings
                if validation_result.get("warnings"):
                    f.write(f"Warnings ({len(validation_result['warnings'])}):\n")
                    for warning in validation_result["warnings"]:
                        f.write(f"  ⚠️  {warning}\n")
                    f.write("\n")

                # Distribution details
                if "statistics" in validation_result:
                    stats = validation_result["statistics"]

                    f.write("Distribution Analysis:\n")

                    for dist_name, dist_data in [
                        ("Change Scope", stats["change_scope_distribution"]),
                        ("Impact Type", stats["impact_type_distribution"]),
                        ("Module", stats["module_distribution"]),
                        ("Model", stats["model_distribution"]),
                    ]:
                        if dist_data:
                            f.write(f"  {dist_name}:\n")
                            sorted_items = sorted(
                                dist_data.items(), key=lambda x: x[1], reverse=True
                            )
                            for name, count in sorted_items:
                                f.write(f"    {name}: {count}\n")
                            f.write("\n")

            logger.info(f"Validation report saved to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error generating validation report: {e}")
            return False


def validate_csv_file(csv_path: str, report_path: str = None) -> bool:
    """
    Convenience function to validate CSV file.

    Args:
        csv_path: Path to CSV file to validate
        report_path: Optional path to save validation report

    Returns:
        True if validation passes
    """
    validator = CSVStructureValidator(csv_path)
    result = validator.validate_csv_structure()

    if report_path:
        validator.generate_validation_report(report_path)

    return result["valid"]
