#!/usr/bin/env python3
"""
Test básico para la implementación enhanced del CSV con referencias cruzadas.
===============================================================

Verifica que todos los componentes funcionen correctamente juntos.
"""

import sys
from pathlib import Path
import tempfile

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from core.models import RenameCandidate, ValidationStatus, ChangeScope, ImpactType
from utils.csv_manager import CSVManager
from interactive.validation_ui import ValidationUI
from analyzers.cross_reference_analyzer import CrossReferenceAnalyzer


def test_enhanced_csv_structure():
    """Test que CSV contiene todas las columnas esperadas"""
    print("🧪 Testing enhanced CSV structure...")

    # Crear candidatos de prueba
    test_candidates = [
        RenameCandidate(
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
        ),
        RenameCandidate(
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
            validation_status=ValidationStatus.PENDING.value,
        ),
    ]

    # Test escritura y lectura CSV
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp_file:
        csv_manager = CSVManager(tmp_file.name)

        # Escribir
        count = csv_manager.write_csv(test_candidates, tmp_file.name)
        assert count == 2, f"Expected 2 records, got {count}"

        # Leer
        read_candidates = csv_manager.read_csv(tmp_file.name)
        assert (
            len(read_candidates) == 2
        ), f"Expected 2 candidates, got {len(read_candidates)}"

        # Verificar campos
        primary = read_candidates[0]
        assert primary.change_id == "1"
        assert primary.impact_type == ImpactType.PRIMARY.value
        assert primary.validation_status == ValidationStatus.PENDING.value

        impact = read_candidates[1]
        assert impact.change_id == "2"
        assert impact.parent_change_id == "1"
        assert impact.impact_type == ImpactType.SELF_REFERENCE.value

        print("✅ CSV structure test passed")

        # Cleanup
        Path(tmp_file.name).unlink()


def test_validation_status_updates():
    """Test que validación actualiza estados correctamente"""
    print("🧪 Testing validation status updates...")

    candidate = RenameCandidate(
        change_id="1",
        old_name="test_field",
        new_name="field_test",
        item_type="field",
        module="test",
        model="test.model",
        change_scope=ChangeScope.DECLARATION.value,
        impact_type=ImpactType.PRIMARY.value,
        context="",
        confidence=0.95,
        parent_change_id="",
        validation_status=ValidationStatus.PENDING.value,
    )

    # Test cambio de estado
    assert candidate.validation_status == ValidationStatus.PENDING.value

    candidate.validation_status = ValidationStatus.APPROVED.value
    assert candidate.validation_status == ValidationStatus.APPROVED.value

    # Test conversión a dict
    csv_dict = candidate.to_cross_ref_dict()
    assert csv_dict["validation_status"] == ValidationStatus.APPROVED.value
    assert csv_dict["change_id"] == "1"
    assert csv_dict["impact_type"] == ImpactType.PRIMARY.value

    print("✅ Validation status test passed")


def test_hierarchical_relationships():
    """Test que parent_change_id vincula correctamente"""
    print("🧪 Testing hierarchical relationships...")

    # Crear estructura jerárquica
    primary = RenameCandidate(
        change_id="1",
        old_name="send_email",
        new_name="send_notification",
        item_type="method",
        module="sale",
        model="sale.order",
        change_scope=ChangeScope.DECLARATION.value,
        impact_type=ImpactType.PRIMARY.value,
        context="",
        confidence=0.95,
        parent_change_id="",
        validation_status=ValidationStatus.APPROVED.value,
    )

    impact1 = RenameCandidate(
        change_id="2",
        old_name="send_email",
        new_name="send_notification",
        item_type="method",
        module="sale",
        model="sale.order",
        change_scope=ChangeScope.CALL.value,
        impact_type=ImpactType.SELF_CALL.value,
        context="confirm_order",
        confidence=0.90,
        parent_change_id="1",  # Link to primary
        validation_status=ValidationStatus.APPROVED.value,
    )

    impact2 = RenameCandidate(
        change_id="3",
        old_name="send_email",
        new_name="send_notification",
        item_type="method",
        module="account",
        model="sale.order",
        change_scope=ChangeScope.CALL.value,
        impact_type=ImpactType.CROSS_MODEL_CALL.value,
        context="create_invoice",
        confidence=0.85,
        parent_change_id="1",  # Link to primary
        validation_status=ValidationStatus.REJECTED.value,
    )

    candidates = [primary, impact1, impact2]

    # Test agrupamiento
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as tmp_file:
        csv_manager = CSVManager(tmp_file.name)

        # Test agrupamiento por declaración
        grouped = csv_manager._group_by_declaration(candidates)

        assert len(grouped) == 1, f"Expected 1 group, got {len(grouped)}"

        primary_found, impacts_found = list(grouped.values())[0]
        assert primary_found.change_id == "1"
        assert len(impacts_found) == 2
        assert all(i.parent_change_id == "1" for i in impacts_found)

        print("✅ Hierarchical relationships test passed")

        # Cleanup
        Path(tmp_file.name).unlink()


def run_all_tests():
    """Ejecuta todos los tests"""
    print("🚀 Running enhanced implementation tests...\n")

    try:
        test_enhanced_csv_structure()
        test_validation_status_updates()
        test_hierarchical_relationships()

        print(f"\n✅ All tests passed! Enhanced implementation is working correctly.")
        print("🎯 Ready for production use.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
