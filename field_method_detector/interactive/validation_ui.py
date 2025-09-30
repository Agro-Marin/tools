"""
Interactive Validation User Interface
======================================

Provides comprehensive interactive validation for rename candidates with
cross-reference support and granular control over validation status.
"""

import logging
from collections import defaultdict

from analyzers.matching_engine import RenameCandidate
from core.models import ValidationStatus, ChangeScope, ImpactType
from utils.csv_manager import CSVManager
from config.settings import INTERACTIVE_COLORS

logger = logging.getLogger(__name__)


class ValidationUI:
    """
    Interactive validation interface for rename candidates with full granular control.

    Handles validation of all cross-references with individual impact control,
    replacing both legacy validators with a single comprehensive interface.
    """

    def __init__(self, csv_manager: CSVManager):
        self.csv_manager = csv_manager
        self.colors = INTERACTIVE_COLORS

    def run_validation_session(self, csv_filename: str):
        """
        Run complete validation session with granular control over all references.

        Args:
            csv_filename: Path to CSV file containing all candidates
        """

        # Read all candidates from CSV
        candidates = self.csv_manager.read_csv(csv_filename)

        if not candidates:
            print("❌ No se encontraron candidatos en el CSV")
            return

        # Count auto-approved candidates
        auto_approved = [
            c
            for c in candidates
            if c.validation_status == ValidationStatus.AUTO_APPROVED.value
        ]
        pending_candidates = [
            c
            for c in candidates
            if c.validation_status == ValidationStatus.PENDING.value
        ]

        if auto_approved:
            print(
                f"✅ {len(auto_approved)} candidatos ya auto-aprobados (confianza ≥90%)"
            )

        if not pending_candidates:
            print("🎉 Todos los candidatos han sido procesados automáticamente")
            self._show_validation_summary(candidates)
            return

        # Group only pending candidates for validation
        grouped = self._group_by_primary(pending_candidates)

        if not grouped:
            print("\n❌ No se encontraron cambios primarios para validar")
            return

        print(
            f"\n🔍 VALIDACIÓN INTERACTIVA - {len(grouped)} cambios pendientes de validar"
        )
        print(
            f"📊 Total candidates: {len(candidates)} ({len(auto_approved)} auto-aprobados, {len(pending_candidates)} pendientes)"
        )

        # Validate each group with full granular control
        total_groups = len(grouped)
        for group_num, (change_id, (primary_change, impacts)) in enumerate(
            grouped.items(), 1
        ):
            self._validate_change_group(
                primary_change, impacts, candidates, group_num, total_groups
            )

            # Show progress after each group
            if group_num < total_groups:
                progress_percent = group_num / total_groups * 100
                progress_bar = self._create_progress_bar(group_num, total_groups)
                print(
                    f"\n📊 Progreso: {group_num}/{total_groups} cambios completados ({progress_percent:.1f}%)"
                )
                print(f"   {progress_bar}")
                print(f"⏭️  Quedan {total_groups - group_num} cambios por validar")

        # Combine all candidates (auto-approved + manually validated) for CSV writing
        all_final_candidates = auto_approved + pending_candidates
        updated_count = self.csv_manager.write_csv(all_final_candidates, csv_filename)

        # Show final summary
        self._show_validation_summary(all_final_candidates)

        print(f"✅ CSV actualizado: {updated_count} registros en {csv_filename}")

    def _group_by_primary(self, candidates: list[RenameCandidate]) -> dict:
        """Group candidates by their primary declaration"""
        grouped = {}

        # Separate primary changes from impacts
        primary_changes = [
            c for c in candidates if c.impact_type == ImpactType.PRIMARY.value
        ]
        impact_changes = [
            c for c in candidates if c.impact_type != ImpactType.PRIMARY.value
        ]

        # Create groups using change_id as key
        for primary in primary_changes:
            impacts = [
                i for i in impact_changes if i.parent_change_id == primary.change_id
            ]
            grouped[primary.change_id] = (primary, impacts)

        return grouped

    def _validate_change_group(
        self,
        primary: RenameCandidate,
        impacts: list[RenameCandidate],
        all_candidates: list[RenameCandidate],
        group_num: int = 1,
        total_groups: int = 1,
    ):
        """Validate a change group with full granular control"""

        self._show_change_header(primary, impacts, group_num, total_groups)

        # Show confidence analysis
        self._show_confidence_analysis(primary, impacts)

        # Main validation choice
        choice = self._get_user_choice(
            [
                "(A)probar TODO (declaración + todas las referencias)",
                "(G)ranular (validar cada referencia individualmente)",
                "(P)rimario solo (solo la declaración)",
                "(R)echazar todo",
                "(V)er detalles completos",
                "(D)etalles de confianza",
                "(S)altar (mantener pendiente)",
            ],
            ["A", "G", "P", "R", "V", "D", "S"],
        )

        if choice == "A":  # Approve all
            primary.validation_status = ValidationStatus.APPROVED.value
            for impact in impacts:
                impact.validation_status = ValidationStatus.APPROVED.value
            print(
                f"✅ {self.colors['pass']}APROBADO TODO{self.colors['reset']}: {primary.old_name} → {primary.new_name}"
            )

        elif choice == "G":  # Granular validation
            primary.validation_status = ValidationStatus.APPROVED.value
            print(
                f"✅ Declaración primaria aprobada: {primary.old_name} → {primary.new_name}"
            )
            self._validate_individual_impacts(impacts)

        elif choice == "P":  # Primary only
            primary.validation_status = ValidationStatus.APPROVED.value
            for impact in impacts:
                impact.validation_status = ValidationStatus.REJECTED.value
            print(f"✅ Solo primario aprobado, {len(impacts)} referencias rechazadas")

        elif choice == "R":  # Reject all
            primary.validation_status = ValidationStatus.REJECTED.value
            for impact in impacts:
                impact.validation_status = ValidationStatus.REJECTED.value
            print(
                f"❌ {self.colors['error']}RECHAZADO TODO{self.colors['reset']}: {primary.old_name} → {primary.new_name}"
            )

        elif choice == "V":  # View details
            self._show_detailed_references(impacts)
            # Recurse for new decision
            self._validate_change_group(primary, impacts, all_candidates)

        elif choice == "D":  # Confidence details
            self._show_detailed_confidence_analysis(primary, impacts)
            # Recurse for new decision
            self._validate_change_group(primary, impacts, all_candidates)

        # 'S' = skip (maintain pending status)

    def _show_change_header(
        self,
        primary: RenameCandidate,
        impacts: list[RenameCandidate],
        group_num: int = 1,
        total_groups: int = 1,
    ):
        """Show header information for a change group"""

        print(f"\n{'='*70}")
        print(
            f"📋 CAMBIO {group_num}/{total_groups} - {primary.old_name} → {primary.new_name}"
        )
        print(f"📍 {primary.model} ({primary.module})")
        print(f"📊 Confianza primaria: {primary.confidence:.2f}")
        print(f"📎 {len(impacts)} referencias encontradas")

        if impacts:
            high_conf_refs = len([i for i in impacts if i.confidence >= 0.90])
            med_conf_refs = len([i for i in impacts if 0.70 <= i.confidence < 0.90])
            low_conf_refs = len([i for i in impacts if i.confidence < 0.70])

            print(f"   • Alta confianza (≥90%): {high_conf_refs}")
            print(f"   • Media confianza (70-89%): {med_conf_refs}")
            print(f"   • Baja confianza (<70%): {low_conf_refs}")

    def _show_confidence_analysis(
        self, primary: RenameCandidate, impacts: list[RenameCandidate]
    ):
        """Show confidence analysis overview"""

        if not impacts:
            return

        # Group by impact type
        by_type = defaultdict(list)
        for impact in impacts:
            by_type[impact.impact_type].append(impact)

        print("   📈 Referencias por tipo:")
        for impact_type, group_impacts in by_type.items():
            type_name = impact_type.replace("_", " ").title()
            avg_conf = sum(i.confidence for i in group_impacts) / len(group_impacts)
            high_conf = len([i for i in group_impacts if i.confidence >= 0.90])
            print(
                f"     • {type_name}: {len(group_impacts)} ({high_conf} alta conf, promedio: {avg_conf:.2f})"
            )

    def _validate_individual_impacts(self, impacts: list[RenameCandidate]):
        """Validate each impact individually with enhanced control"""

        if not impacts:
            print("   (No hay referencias para validar)")
            return

        # Group by type for better UX
        by_type = defaultdict(list)
        for impact in impacts:
            by_type[impact.impact_type].append(impact)

        for impact_type, group_impacts in by_type.items():
            type_name = impact_type.replace("_", " ").title()
            print(f"\n  📂 {type_name} ({len(group_impacts)} referencias)")

            # Option to bulk validate this type
            if len(group_impacts) > 1:
                bulk_choice = self._get_user_choice(
                    [
                        f"(T)odas en bloque para {type_name}",
                        "(I)ndividual (una por una)",
                        "(S)altar este tipo",
                    ],
                    ["T", "I", "S"],
                )

                if bulk_choice == "T":
                    self._bulk_validate_type(group_impacts, type_name)
                    continue
                elif bulk_choice == "S":
                    continue
                # 'I' falls through to individual validation

            # Individual validation
            for impact_num, impact in enumerate(group_impacts, 1):
                self._validate_single_impact(
                    impact, impact_num, len(group_impacts), type_name
                )

    def _bulk_validate_type(self, impacts: list[RenameCandidate], type_name: str):
        """Bulk validate all impacts of a specific type"""

        avg_conf = sum(i.confidence for i in impacts) / len(impacts)
        high_conf = len([i for i in impacts if i.confidence >= 0.90])

        print(
            f"    📊 {type_name}: {len(impacts)} referencias (promedio: {avg_conf:.2f}, {high_conf} alta confianza)"
        )

        choice = self._get_user_choice(
            [
                f"(A)probar todas las {len(impacts)} referencias de {type_name}",
                f"(R)echazar todas las {len(impacts)} referencias de {type_name}",
                "(I)ndividual (validar una por una)",
                "(S)altar (mantener pending)",
            ],
            ["A", "R", "I", "S"],
        )

        if choice == "A":
            for impact in impacts:
                impact.validation_status = ValidationStatus.APPROVED.value
            print(
                f"    ✅ {len(impacts)} referencias de {type_name} aprobadas en bloque"
            )
        elif choice == "R":
            for impact in impacts:
                impact.validation_status = ValidationStatus.REJECTED.value
            print(
                f"    ❌ {len(impacts)} referencias de {type_name} rechazadas en bloque"
            )
        elif choice == "I":
            for impact_num, impact in enumerate(impacts, 1):
                self._validate_single_impact(
                    impact, impact_num, len(impacts), type_name
                )
        # 'S' = skip

    def _validate_single_impact(
        self,
        impact: RenameCandidate,
        impact_num: int = 1,
        total_impacts: int = 1,
        type_name: str = "",
    ):
        """Validate a single impact with full control options"""

        self._show_impact_detail(impact, impact_num, total_impacts, type_name)

        choice = self._get_user_choice(
            [
                f"(A)probar esta referencia (confianza: {impact.confidence:.2f})",
                "(R)echazar esta referencia",
                "(E)ditar nombre destino",
                "(C)ambiar modelo destino",
                "(V)er contexto completo",
                "(S)altar (mantener pending)",
            ],
            ["A", "R", "E", "C", "V", "S"],
        )

        if choice == "A":
            impact.validation_status = ValidationStatus.APPROVED.value
            print(f"    ✅ Aprobada: {impact.context or 'referencia'}")
        elif choice == "R":
            impact.validation_status = ValidationStatus.REJECTED.value
            print(f"    ❌ Rechazada: {impact.context or 'referencia'}")
        elif choice == "E":
            new_name = input(f"    Nuevo nombre para '{impact.old_name}': ").strip()
            if new_name:
                impact.new_name = new_name
                impact.validation_status = ValidationStatus.APPROVED.value
                print(f"    ✅ Editado y aprobado: {impact.old_name} → {new_name}")
        elif choice == "C":
            new_model = input(f"    Nuevo modelo para '{impact.model}': ").strip()
            if new_model:
                impact.model = new_model
                impact.validation_status = ValidationStatus.APPROVED.value
                print(f"    ✅ Modelo cambiado y aprobado: {new_model}")
        elif choice == "V":
            self._show_full_impact_context(impact)
            # Recurse for new decision
            self._validate_single_impact(impact, impact_num, total_impacts, type_name)
        # 'S' = skip

    def _show_impact_detail(
        self,
        impact: RenameCandidate,
        impact_num: int = 1,
        total_impacts: int = 1,
        type_name: str = "",
    ):
        """Show details of a specific impact reference"""

        print(f"\n    ┌─ Referencia {impact_num}/{total_impacts} ({type_name}) ─")
        print(f"    🎯 {impact.model} → {impact.context or 'N/A'}")
        print(f"    📝 {impact.change_scope}: {impact.old_name} → {impact.new_name}")
        print(f"    📊 Confianza: {impact.confidence:.2f}")
        print(f"    🏷️  Estado: {impact.validation_status}")
        if impact.source_file:
            print(f"    📁 Archivo: {impact.source_file}:{impact.line_number or 'N/A'}")

    def _show_full_impact_context(self, impact: RenameCandidate):
        """Show full context information for an impact"""

        print(f"\n    {'─'*50}")
        print("    🔍 CONTEXTO COMPLETO")
        print(f"    {'─'*50}")
        print(f"    ID: {impact.change_id}")
        print(f"    Padre: {impact.parent_change_id}")
        print(f"    Módulo: {impact.module}")
        print(f"    Modelo: {impact.model}")
        print(f"    Tipo: {impact.item_type}")
        print(f"    Alcance: {impact.change_scope}")
        print(f"    Impacto: {impact.impact_type}")
        print(f"    Cambio: {impact.old_name} → {impact.new_name}")
        print(f"    Contexto: {impact.context or 'N/A'}")
        print(f"    Confianza: {impact.confidence:.3f}")
        print(f"    Estado: {impact.validation_status}")
        if impact.source_file:
            print(f"    Ubicación: {impact.source_file}:{impact.line_number or 'N/A'}")

        input("\n    Presiona Enter para continuar...")

    def _show_detailed_references(self, impacts: list[RenameCandidate]):
        """Show detailed information for all references"""

        print(f"\n{'='*70}")
        print("🔍 DETALLES COMPLETOS DE TODAS LAS REFERENCIAS")
        print(f"{'='*70}")

        if not impacts:
            print("(No hay referencias cruzadas)")
            input("\nPresiona Enter para continuar...")
            return

        for i, impact in enumerate(impacts, 1):
            print(f"\n{i}. {impact.impact_type.replace('_', ' ').title()}")
            print(f"   Modelo: {impact.model}")
            print(f"   Contexto: {impact.context or 'N/A'}")
            print(f"   Cambio: {impact.old_name} → {impact.new_name}")
            print(f"   Confianza: {impact.confidence:.2f}")
            print(f"   Estado: {impact.validation_status}")
            if impact.source_file:
                print(
                    f"   Ubicación: {impact.source_file}:{impact.line_number or 'N/A'}"
                )

        input("\nPresiona Enter para continuar...")

    def _show_detailed_confidence_analysis(
        self, primary: RenameCandidate, impacts: list[RenameCandidate]
    ):
        """Show detailed confidence analysis"""

        print(f"\n{'='*70}")
        print("📊 ANÁLISIS DETALLADO DE CONFIANZA")
        print(f"{'='*70}")

        # Primary analysis
        print(f"\n🔧 DECLARACIÓN PRIMARIA:")
        print(f"   Nombre: {primary.old_name} → {primary.new_name}")
        print(f"   Confianza: {primary.confidence:.3f}")
        print(f"   Regla aplicada: {primary.rule_applied or 'similarity'}")
        print(f"   Signature match: {'✅' if primary.signature_match else '❌'}")

        if not impacts:
            print("\n(No hay referencias cruzadas para analizar)")
            input("\nPresiona Enter para continuar...")
            return

        # Impact analysis
        print(f"\n📎 ANÁLISIS DE REFERENCIAS ({len(impacts)} total):")

        # Statistics by confidence range
        high_conf = [i for i in impacts if i.confidence >= 0.90]
        med_conf = [i for i in impacts if 0.70 <= i.confidence < 0.90]
        low_conf = [i for i in impacts if i.confidence < 0.70]

        print(f"\n📈 Distribución por confianza:")
        print(f"   Alta (≥90%): {len(high_conf)}")
        print(f"   Media (70-89%): {len(med_conf)}")
        print(f"   Baja (<70%): {len(low_conf)}")

        # Analysis by type
        by_type = defaultdict(list)
        for impact in impacts:
            by_type[impact.impact_type].append(impact)

        print(f"\n🏷️  Por tipo de impacto:")
        for impact_type, group_impacts in by_type.items():
            avg_conf = sum(i.confidence for i in group_impacts) / len(group_impacts)
            type_name = impact_type.replace("_", " ").title()
            print(
                f"   {type_name}: {len(group_impacts)} referencias, promedio {avg_conf:.2f}"
            )

        # Show lowest confidence items for review
        if low_conf:
            print(f"\n⚠️  Referencias de baja confianza que requieren atención:")
            sorted_low = sorted(low_conf, key=lambda x: x.confidence)
            for impact in sorted_low[:5]:  # Show worst 5
                print(
                    f"   • {impact.model}: {impact.context or 'N/A'} ({impact.confidence:.2f})"
                )

        input("\nPresiona Enter para continuar...")

    def _get_user_choice(self, options: list[str], valid_choices: list[str]) -> str:
        """Get user choice with validation"""
        print("\n   Opciones:")
        for option in options:
            print(f"     {option}")

        while True:
            response = input("\n   Selección: ").upper().strip()
            if response in valid_choices:
                return response
            else:
                print(f"   ❌ Opción inválida. Use: {'/'.join(valid_choices)}")

    def _show_validation_summary(self, candidates: list[RenameCandidate]):
        """Show final validation summary"""
        total = len(candidates)
        approved = len(
            [
                c
                for c in candidates
                if c.validation_status == ValidationStatus.APPROVED.value
            ]
        )
        auto_approved = len(
            [
                c
                for c in candidates
                if c.validation_status == ValidationStatus.AUTO_APPROVED.value
            ]
        )
        rejected = len(
            [
                c
                for c in candidates
                if c.validation_status == ValidationStatus.REJECTED.value
            ]
        )
        pending = len(
            [
                c
                for c in candidates
                if c.validation_status == ValidationStatus.PENDING.value
            ]
        )

        print(
            f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           📊 RESUMEN FINAL DE VALIDACIÓN                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

📈 Estadísticas completas:
   • Total detectado: {total}
   • Auto-aprobados: {auto_approved} (≥90% confianza)
   • Aprobados manualmente: {approved}
   • Rechazados: {rejected}
   • Pendientes: {pending}
   • TOTAL PARA APLICAR: {approved + auto_approved}
        """
        )

        # Module statistics for approved
        self._show_module_stats(candidates)

    def _show_module_stats(self, candidates: list[RenameCandidate]):
        """Show module statistics for approved candidates"""
        module_stats = defaultdict(int)
        for candidate in candidates:
            if candidate.validation_status in [
                ValidationStatus.APPROVED.value,
                ValidationStatus.AUTO_APPROVED.value,
            ]:
                module_stats[candidate.module] += 1

        if module_stats:
            print("📂 Por módulo (solo aprobados):")
            for module, count in sorted(module_stats.items()):
                print(f"   • {module}: {count} cambios")

    def _create_progress_bar(self, current: int, total: int, width: int = 30) -> str:
        """Create a visual progress bar"""
        filled = int(width * current / total)
        bar = "█" * filled + "░" * (width - filled)
        percent = current / total * 100
        return f"[{bar}] {percent:.1f}%"
