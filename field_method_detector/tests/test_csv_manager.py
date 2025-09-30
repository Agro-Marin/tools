#!/usr/bin/env python3
"""
Test suite for CSVManager
=========================

Tests CSV reading, writing, and data integrity for the enhanced cross-reference format.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from core.models import RenameCandidate, ValidationStatus, ChangeScope, ImpactType
from utils.csv_manager import CSVManager


class TestCSVManager(unittest.TestCase):
    """Test suite for CSVManager functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        )
        self.temp_file.close()
        self.csv_manager = CSVManager(self.temp_file.name)

        # Create test candidates
        self.primary_candidate = RenameCandidate(
            change_id="1",
            old_name="amount_total",
            new_name="total_amount",
            item_type="field",
            module="sale",
            model="sale.order",
            change_scope=ChangeScope.DECLARATION.value,
            impact_type=ImpactType.PRIMARY.value,
            context="",
            confidence=0.95,
            parent_change_id="",
            validation_status=ValidationStatus.PENDING.value,
        )

        self.impact_candidate = RenameCandidate(
            change_id="2",
            old_name="amount_total",
            new_name="total_amount",
            item_type="field",
            module="sale",
            model="sale.order",
            change_scope=ChangeScope.REFERENCE.value,
            impact_type=ImpactType.SELF_REFERENCE.value,
            context="_compute_tax",
            confidence=0.90,
            parent_change_id="1",
            validation_status=ValidationStatus.AUTO_APPROVED.value,
        )

    def tearDown(self):
        """Clean up test fixtures"""
        Path(self.temp_file.name).unlink(missing_ok=True)
        # Clean up any backup files
        for backup in Path(self.temp_file.name).parent.glob("*.backup_*.csv"):
            backup.unlink()

    def test_csv_headers_completeness(self):
        """Test that CSV headers include all required fields"""
        expected_headers = [
            "change_id",
            "old_name",
            "new_name",
            "item_type",
            "module",
            "model",
            "change_scope",
            "impact_type",
            "context",
            "confidence",
            "parent_change_id",
            "validation_status",
        ]

        self.assertEqual(self.csv_manager.CSV_HEADERS, expected_headers)

    def test_write_and_read_round_trip(self):
        """Test writing candidates to CSV and reading them back"""
        candidates = [self.primary_candidate, self.impact_candidate]

        # Write to CSV
        written_count = self.csv_manager.write_csv(candidates, self.temp_file.name)
        self.assertEqual(written_count, 2)

        # Read from CSV
        read_candidates = self.csv_manager.read_csv(self.temp_file.name)
        self.assertEqual(len(read_candidates), 2)

        # Verify primary candidate
        primary = read_candidates[0]
        self.assertEqual(primary.change_id, "1")
        self.assertEqual(primary.old_name, "amount_total")
        self.assertEqual(primary.new_name, "total_amount")
        self.assertEqual(primary.impact_type, ImpactType.PRIMARY.value)
        self.assertEqual(primary.confidence, 0.95)
        self.assertEqual(primary.validation_status, ValidationStatus.PENDING.value)

        # Verify impact candidate
        impact = read_candidates[1]
        self.assertEqual(impact.change_id, "2")
        self.assertEqual(impact.parent_change_id, "1")
        self.assertEqual(impact.impact_type, ImpactType.SELF_REFERENCE.value)
        self.assertEqual(impact.context, "_compute_tax")
        self.assertEqual(impact.confidence, 0.90)
        self.assertEqual(impact.validation_status, ValidationStatus.AUTO_APPROVED.value)

    def test_confidence_conversion_robustness(self):
        """Test that confidence values are handled robustly"""
        # Create CSV with various confidence formats
        csv_content = """change_id,old_name,new_name,item_type,module,model,change_scope,impact_type,context,confidence,parent_change_id,validation_status
1,test_field,field_test,field,test,test.model,declaration,primary,,0.95,,pending
2,test_field,field_test,field,test,test.model,reference,self_reference,context,invalid,,pending
3,test_field,field_test,field,test,test.model,reference,self_reference,context,1.5,,pending
4,test_field,field_test,field,test,test.model,reference,self_reference,context,,,pending
"""

        with open(self.temp_file.name, "w") as f:
            f.write(csv_content)

        # Read candidates
        candidates = self.csv_manager.read_csv(self.temp_file.name)

        # Should have 4 candidates with sanitized confidence values
        self.assertEqual(len(candidates), 4)
        self.assertEqual(candidates[0].confidence, 0.95)  # Valid value
        self.assertEqual(candidates[1].confidence, 0.0)  # Invalid string -> 0.0
        self.assertEqual(candidates[2].confidence, 1.0)  # > 1.0 -> clamped to 1.0
        self.assertEqual(candidates[3].confidence, 0.0)  # Empty -> 0.0

    def test_invalid_data_handling(self):
        """Test handling of invalid or missing data"""
        # Create CSV with invalid data
        csv_content = """change_id,old_name,new_name,item_type,module,model,change_scope,impact_type,context,confidence,parent_change_id,validation_status
1,,,field,test,test.model,declaration,primary,,0.95,,pending
2,same_name,same_name,field,test,test.model,reference,self_reference,context,0.90,,pending
3,valid_old,valid_new,field,test,test.model,reference,self_reference,context,0.90,,pending
"""

        with open(self.temp_file.name, "w") as f:
            f.write(csv_content)

        # Read candidates
        candidates = self.csv_manager.read_csv(self.temp_file.name)

        # Should skip invalid rows and only have 1 valid candidate
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].old_name, "valid_old")
        self.assertEqual(candidates[0].new_name, "valid_new")

    def test_grouping_by_declaration(self):
        """Test the grouping functionality for primary declarations"""
        candidates = [self.primary_candidate, self.impact_candidate]

        grouped = self.csv_manager._group_by_declaration(candidates)

        # Should have one group with primary and one impact
        self.assertEqual(len(grouped), 1)

        primary_found, impacts_found = list(grouped.values())[0]
        self.assertEqual(primary_found.change_id, "1")
        self.assertEqual(len(impacts_found), 1)
        self.assertEqual(impacts_found[0].change_id, "2")
        self.assertEqual(impacts_found[0].parent_change_id, "1")

    def test_write_candidates_creates_backup(self):
        """Test that write_candidates creates backup if file exists"""
        # Create initial file
        candidates = [self.primary_candidate]
        self.csv_manager.write_candidates(candidates)

        # Verify file exists
        self.assertTrue(Path(self.temp_file.name).exists())

        # Write again - should create backup
        new_candidates = [self.impact_candidate]
        self.csv_manager.write_candidates(new_candidates)

        # Check for backup files
        backup_files = list(Path(self.temp_file.name).parent.glob("*.backup_*.csv"))
        self.assertGreater(len(backup_files), 0, "Backup file should be created")


def run_tests():
    """Run all CSV manager tests"""
    unittest.main()


if __name__ == "__main__":
    run_tests()
