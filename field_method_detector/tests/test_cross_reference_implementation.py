"""
Test suite for Cross-Reference Implementation
===========================================

Tests to verify that the CSV structure with cross-references
works correctly end-to-end.
"""

import pytest
import tempfile
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.models import RenameCandidate
from utils.csv_manager import CSVManager
from utils.csv_validator import CSVStructureValidator
from analyzers.cross_reference_analyzer import CrossReferenceAnalyzer


class TestCrossReferenceImplementation:
    """Test suite for the cross-reference implementation"""

    def test_rename_candidate_factory_methods(self):
        """Test that factory methods create proper candidates"""
        # Test primary declaration factory
        primary = RenameCandidate.create_primary_declaration(
            change_id="1",
            old_name="old_field",
            new_name="new_field",
            item_type="field",
            module="sale",
            model="sale.order",
            confidence=0.95,
        )

        assert primary.change_id == "1"
        assert primary.old_name == "old_field"
        assert primary.new_name == "new_field"
        assert primary.change_scope == "declaration"
        assert primary.impact_type == "primary"
        assert primary.context == ""
        assert primary.parent_change_id == ""
        assert primary.is_primary_change() == True

        # Test impact candidate factory
        impact = RenameCandidate.create_impact_candidate(
            parent_change_id="1",
            old_name="old_field",
            new_name="new_field",
            item_type="field",
            module="sale",
            model="sale.order",
            change_scope="reference",
            impact_type="self_reference",
            context="_compute_totals",
            confidence=0.85,
        )

        assert impact.parent_change_id == "1"
        assert impact.change_scope == "reference"
        assert impact.impact_type == "self_reference"
        assert impact.context == "_compute_totals"
        assert impact.is_primary_change() == False
        assert impact.needs_context() == True

    def test_csv_round_trip(self):
        """Test writing and reading CSV format"""
        candidates = [
            RenameCandidate.create_primary_declaration(
                change_id="1",
                old_name="amount_total",
                new_name="total_amount",
                item_type="field",
                module="sale",
                model="sale.order",
                confidence=0.95,
            ),
            RenameCandidate.create_impact_candidate(
                parent_change_id="1",
                old_name="amount_total",
                new_name="total_amount",
                item_type="field",
                module="sale",
                model="sale.order",
                change_scope="reference",
                impact_type="self_reference",
                context="_compute_tax",
                confidence=0.90,
            ),
            RenameCandidate.create_impact_candidate(
                parent_change_id="1",
                old_name="amount_total",
                new_name="total_amount",
                item_type="field",
                module="account",
                model="sale.order",
                change_scope="reference",
                impact_type="cross_model",
                context="create_from_sale",
                confidence=0.85,
            ),
        ]

        # Write to temporary CSV
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as tmp_file:
            csv_path = tmp_file.name

        try:
            csv_manager = CSVManager(csv_path)
            written_count = csv_manager.write_candidates(candidates)

            assert written_count == 3

            # Read back and verify
            read_candidates = csv_manager.read_csv()

            assert len(read_candidates) == 3

            # Verify primary candidate
            primary = next(c for c in read_candidates if c.is_primary_change())
            assert primary.change_id == "1"
            assert primary.old_name == "amount_total"
            assert primary.impact_type == "primary"

            # Verify impact candidates
            impacts = [c for c in read_candidates if not c.is_primary_change()]
            assert len(impacts) == 2

            self_ref = next(c for c in impacts if c.impact_type == "self_reference")
            assert self_ref.context == "_compute_tax"
            assert self_ref.parent_change_id == "1"

            cross_ref = next(c for c in impacts if c.impact_type == "cross_model")
            assert cross_ref.context == "create_from_sale"
            assert cross_ref.module == "account"

        finally:
            Path(csv_path).unlink(missing_ok=True)

    def test_csv_structure_validation(self):
        """Test that CSV structure validator works with CSV format"""
        candidates = [
            RenameCandidate.create_primary_declaration(
                change_id="1",
                old_name="test_field",
                new_name="new_test_field",
                item_type="field",
                module="test",
                model="test.model",
                confidence=0.95,
            ),
            RenameCandidate.create_impact_candidate(
                parent_change_id="1",
                old_name="test_field",
                new_name="new_test_field",
                item_type="field",
                module="test",
                model="test.model",
                change_scope="reference",
                impact_type="self_reference",
                context="test_method",
                confidence=0.90,
            ),
        ]

        # Write to temporary CSV
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as tmp_file:
            csv_path = tmp_file.name

        try:
            csv_manager = CSVManager(csv_path)
            csv_manager.write_candidates(candidates)

            # Validate structure
            validator = CSVStructureValidator(csv_path)
            result = validator.validate_csv_structure()

            assert result["valid"] == True
            assert result["statistics"]["total_rows"] == 2
            assert result["statistics"]["primary_changes"] == 1
            assert result["statistics"]["impact_changes"] == 1

        finally:
            Path(csv_path).unlink(missing_ok=True)

    def test_csv_manager_write_candidates_method(self):
        """Test the main write_candidates method"""
        candidates = [
            RenameCandidate.create_primary_declaration(
                change_id="1",
                old_name="send_email",
                new_name="send_notification",
                item_type="method",
                module="sale",
                model="sale.order",
                confidence=0.95,
            )
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as tmp_file:
            csv_path = tmp_file.name

        try:
            csv_manager = CSVManager(csv_path)
            count = csv_manager.write_candidates(candidates)

            assert count == 1
            assert Path(csv_path).exists()

            # Verify content
            read_candidates = csv_manager.read_csv()
            assert len(read_candidates) == 1
            assert read_candidates[0].old_name == "send_email"
            assert read_candidates[0].item_type == "method"

        finally:
            Path(csv_path).unlink(missing_ok=True)


if __name__ == "__main__":
    # Run basic tests
    test_suite = TestCrossReferenceImplementation()

    print("🧪 Testing cross-reference implementation...")

    try:
        test_suite.test_rename_candidate_factory_methods()
        print("✅ Factory methods test passed")

        test_suite.test_csv_round_trip()
        print("✅ CSV round-trip test passed")

        test_suite.test_csv_structure_validation()
        print("✅ CSV validation test passed")

        test_suite.test_csv_manager_write_candidates_method()
        print("✅ CSVManager write_candidates test passed")

        print(
            "\n🎉 All tests passed! Cross-reference implementation is working correctly."
        )

    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
