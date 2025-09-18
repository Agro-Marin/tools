"""
Interactive Validation User Interface
======================================

Provides interactive validation for rename candidates with confidence scoring
display and user-friendly prompts.
"""

import logging

from analyzers.matching_engine import RenameCandidate
from config.settings import INTERACTIVE_COLORS

logger = logging.getLogger(__name__)


class InteractiveValidator:
    """Interactive validation interface for rename candidates"""

    def __init__(
        self, confidence_threshold: float = 0.75, auto_approve_threshold: float = 0.90
    ):
        """
        Initialize interactive validator.

        Args:
            confidence_threshold: Threshold for manual review
            auto_approve_threshold: Threshold for auto-approval
        """
        self.confidence_threshold = confidence_threshold
        self.auto_approve_threshold = auto_approve_threshold
        self.colors = INTERACTIVE_COLORS
        self.user_decisions = []

    def validate_candidates(
        self, candidates: list[RenameCandidate]
    ) -> tuple[list[RenameCandidate], dict]:
        """
        Run interactive validation workflow.

        Args:
            candidates: List of rename candidates to validate

        Returns:
            Tuple of (approved_candidates, validation_summary)
        """
        # Classify candidates by confidence
        auto_approved, needs_review, auto_rejected = self._classify_candidates(
            candidates
        )

        # Show initial summary
        self._show_initial_summary(auto_approved, needs_review, auto_rejected)

        approved_candidates = []

        # Auto-approve high confidence
        approved_candidates.extend(auto_approved)
        self._show_auto_approved(auto_approved)

        # Interactive review for medium confidence
        if needs_review:
            manually_approved = self._interactive_review(needs_review)
            approved_candidates.extend(manually_approved)

        # Show rejected summary
        if auto_rejected:
            self._show_auto_rejected(auto_rejected)

        # Generate final summary
        validation_summary = self._generate_validation_summary(
            auto_approved,
            manually_approved if needs_review else [],
            auto_rejected,
            len(approved_candidates),
        )

        return approved_candidates, validation_summary

    def _classify_candidates(
        self, candidates: list[RenameCandidate]
    ) -> tuple[list, list, list]:
        """Classify candidates by confidence level"""
        auto_approved = []
        needs_review = []
        auto_rejected = []

        for candidate in candidates:
            if candidate.confidence >= self.auto_approve_threshold:
                auto_approved.append(candidate)
            elif candidate.confidence >= 0.50:  # Minimum review threshold
                needs_review.append(candidate)
            else:
                auto_rejected.append(candidate)

        return auto_approved, needs_review, auto_rejected

    def _show_initial_summary(
        self, auto_approved: list, needs_review: list, auto_rejected: list
    ):
        """Show initial classification summary"""
        print(
            f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🔍 ODOO FIELD/METHOD CHANGE DETECTOR                      ║
║                              Modo Asistido                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

🎯 CONFIGURACIÓN:
   • Umbral auto-aprobación: {self.auto_approve_threshold:.1%}
   • Umbral revisión manual: {self.confidence_threshold:.1%}
   • Umbral mínimo: 50.0%

📊 CLASIFICACIÓN INICIAL:
   • {self.colors['pass']}✅ Auto-aprobados{self.colors['reset']}: {len(auto_approved)} cambios (≥{self.auto_approve_threshold:.0%} confianza)
   • {self.colors['fail']}🤔 Requieren revisión{self.colors['reset']}: {len(needs_review)} cambios (50-{self.auto_approve_threshold:.0%}% confianza)
   • {self.colors['error']}❌ Auto-rechazados{self.colors['reset']}: {len(auto_rejected)} cambios (<50% confianza)

Comandos disponibles durante la revisión:
  {self.colors['bold']}y/yes{self.colors['reset']} - Incluir cambio  
  {self.colors['bold']}n/no{self.colors['reset']}  - Omitir cambio
  {self.colors['bold']}s{self.colors['reset']}     - Omitir el resto (solo auto-aprobados)
  {self.colors['bold']}q{self.colors['reset']}     - Cancelar script
  {self.colors['bold']}d{self.colors['reset']}     - Mostrar análisis detallado
  {self.colors['bold']}h{self.colors['reset']}     - Mostrar ayuda
"""
        )

    def _show_auto_approved(self, auto_approved: list[RenameCandidate]):
        """Show auto-approved candidates"""
        if not auto_approved:
            return

        print(
            f"\n{self.colors['pass']}✅ AUTO-APROBADOS ({len(auto_approved)} cambios con ≥{self.auto_approve_threshold:.0%}% confianza){self.colors['reset']}"
        )
        for candidate in auto_approved:
            print(
                f"  {candidate.old_name} → {candidate.new_name} ({candidate.module}.{candidate.model}) [{candidate.confidence:.1%}]"
            )

    def _interactive_review(
        self, needs_review: list[RenameCandidate]
    ) -> list[RenameCandidate]:
        """Interactive review of medium confidence candidates"""
        manually_approved = []

        print(
            f"\n{self.colors['fail']}🤔 REVISIÓN MANUAL ({len(needs_review)} casos requieren validación){self.colors['reset']}"
        )

        for i, candidate in enumerate(needs_review, 1):
            decision = self._prompt_user_validation(candidate, i, len(needs_review))

            if decision == "approve":
                manually_approved.append(candidate)
            elif decision == "skip_all":
                print("⏭️ Omitiendo el resto de validaciones...")
                break
            elif decision == "quit":
                print("⏹️ Cancelando script...")
                exit(0)
            # 'reject' - do nothing, candidate not added to approved list

        return manually_approved

    def _prompt_user_validation(
        self, candidate: RenameCandidate, current: int, total: int
    ) -> str:
        """
        Prompt user for validation decision.

        Args:
            candidate: Rename candidate to validate
            current: Current item number
            total: Total items to review

        Returns:
            User decision: 'approve', 'reject', 'skip_all', 'quit'
        """
        # Create confidence visualization
        confidence_bar = self._create_confidence_bar(
            candidate.confidence, self.auto_approve_threshold
        )
        confidence_pct = candidate.confidence * 100
        threshold_pct = self.auto_approve_threshold * 100

        print(f"\n{'='*70}")
        print(f"🔍 Cambio {current}/{total} - Revisión Manual Requerida")
        print(f"{'='*70}")

        print(f"📁 Archivo: {candidate.file_path or 'N/A'}")
        print(f"📦 Módulo: {candidate.module}")
        print(f"🏗️  Modelo: {candidate.model}")
        print(f"🔧 Tipo: {candidate.item_type.title()}")
        print(
            f"📝 Cambio: {self.colors['error']}{candidate.old_name}{self.colors['reset']} → {self.colors['pass']}{candidate.new_name}{self.colors['reset']}"
        )

        # Show confidence analysis
        print(f"\n📊 Análisis de Confianza:")
        print(f"   Confianza calculada: {confidence_pct:.1f}%")
        print(f"   Umbral auto-aprobación: {threshold_pct:.1f}%")
        print(f"   {confidence_bar}")

        # Show reason for confidence level
        confidence_reason = self._get_confidence_reason(candidate)
        print(f"   Razón: {confidence_reason}")

        # Show gap to auto-approval
        gap = threshold_pct - confidence_pct
        if gap > 0:
            print(f"   ⚠️  Faltan {gap:.1f} puntos porcentuales para auto-aprobación")

        # Show additional context if available
        if candidate.rule_applied:
            print(f"\n🔬 Regla aplicada: {candidate.rule_applied}")

        while True:
            prompt = f"\n¿Incluir este cambio? [y/N/s(skip)/q(quit)/d(details)]: "
            response = input(prompt).lower().strip()

            if response in ["y", "yes", "sí", "si"]:
                print(
                    f"✅ {self.colors['pass']}INCLUIDO{self.colors['reset']}: {candidate.old_name} → {candidate.new_name}"
                )
                self.user_decisions.append(
                    {"candidate": candidate, "decision": "approved"}
                )
                return "approve"
            elif response in ["n", "no", ""] or response == "N":
                print(
                    f"❌ {self.colors['error']}OMITIDO{self.colors['reset']}: {candidate.old_name} → {candidate.new_name}"
                )
                self.user_decisions.append(
                    {"candidate": candidate, "decision": "rejected"}
                )
                return "reject"
            elif response in ["s", "skip"]:
                return "skip_all"
            elif response in ["q", "quit"]:
                return "quit"
            elif response in ["d", "details"]:
                self._show_detailed_analysis(candidate)
            elif response in ["h", "help"]:
                self._show_validation_help()
            else:
                print("❌ Opción inválida. Usa: y/n/s/q/d/h")

    def _create_confidence_bar(
        self, confidence: float, threshold: float, bar_length: int = 30
    ) -> str:
        """Create visual confidence bar with threshold indicator"""
        confidence_pos = int(confidence * bar_length)
        threshold_pos = int(threshold * bar_length)

        bar = ["─"] * bar_length

        # Mark confidence position
        if confidence_pos < bar_length:
            bar[confidence_pos] = "●"

        # Mark threshold position
        if threshold_pos < bar_length:
            bar[threshold_pos] = "|"

        # Color bar based on pass/fail
        if confidence >= threshold:
            confidence_color = self.colors["pass"]
            status = "PASA"
        else:
            confidence_color = self.colors["fail"]
            status = "NO PASA"

        bar_str = "".join(bar)
        return f"{confidence_color}{bar_str}{self.colors['reset']} ({status})"

    def _get_confidence_reason(self, candidate: RenameCandidate) -> str:
        """Get human-readable reason for confidence level"""
        confidence = candidate.confidence
        rule = candidate.rule_applied or "signature similarity"

        if confidence >= 0.95:
            return f"Signature exacta + regla '{rule}' aplicada perfectamente"
        elif confidence >= 0.85:
            return f"Signature exacta + regla '{rule}' aplicada parcialmente"
        elif confidence >= 0.75:
            return f"Signature similar + patrón '{rule}' detectado"
        elif confidence >= 0.60:
            return f"Signature coincidente + nombres relacionados por '{rule}'"
        else:
            return f"Similaridad básica detectada por '{rule}'"

    def _show_detailed_analysis(self, candidate: RenameCandidate):
        """Show detailed analysis for a candidate"""
        print(f"\n{'-'*50}")
        print("🔬 ANÁLISIS DETALLADO DE CONFIANZA")
        print(f"{'-'*50}")

        # Show scoring breakdown
        if candidate.scoring_breakdown:
            print("📊 Factores de puntuación:")
            for factor, score in candidate.scoring_breakdown.items():
                print(f"   • {factor.replace('_', ' ').title()}: +{score:.2f}")

        # Show signature details
        print(f"\n🔍 Detalles de signature:")
        print(
            f"   • Signature match: {'✅ Exacto' if candidate.signature_match else '❌ Diferente'}"
        )

        # Show validations
        if candidate.validations:
            print(f"\n✅ Validaciones:")
            for validation in candidate.validations:
                v_type = validation.get("type", "unknown")
                message = validation.get("message", "No message")
                print(f"   • {v_type}: {message}")

        # Show API changes
        if candidate.api_changes:
            print(f"\n🔄 Cambios de API detectados:")
            api = candidate.api_changes
            print(f"   • Tipo: {api.get('type', 'Unknown')}")
            print(f"   • Descripción: {api.get('description', 'No description')}")

        # Show comparison with threshold
        print(f"\n📏 Comparación con umbral:")
        print(f"   • Confianza actual: {candidate.confidence:.3f}")
        print(f"   • Umbral requerido: {self.auto_approve_threshold:.3f}")
        print(
            f"   • Diferencia: {candidate.confidence - self.auto_approve_threshold:+.3f}"
        )

    def _show_validation_help(self):
        """Show validation help"""
        threshold_pct = self.auto_approve_threshold * 100
        print(
            f"""
{'-'*50}
❓ AYUDA - COMANDOS DE VALIDACIÓN
{'-'*50}
{self.colors['bold']}y/yes{self.colors['reset']}  → Incluir este cambio en el CSV final
{self.colors['bold']}n/no{self.colors['reset']}   → Omitir este cambio (no se incluirá)
{self.colors['bold']}s/skip{self.colors['reset']} → Omitir TODOS los cambios restantes (solo auto-aprobados)
{self.colors['bold']}q/quit{self.colors['reset']} → Cancelar script completo
{self.colors['bold']}d{self.colors['reset']}      → Mostrar análisis técnico detallado
{self.colors['bold']}h{self.colors['reset']}      → Mostrar esta ayuda

💡 TIPS:
• La confianza se basa en: signature exacta + reglas de naming + contexto
• Umbral actual: auto-aprobación si confianza ≥ {threshold_pct:.0f}%
• En caso de duda, revisa el análisis detallado (d)
• Los cambios auto-aprobados ya están incluidos automáticamente
{'-'*50}
        """
        )

    def _show_auto_rejected(self, auto_rejected: list[RenameCandidate]):
        """Show auto-rejected candidates summary"""
        if not auto_rejected:
            return

        print(
            f"\n{self.colors['error']}❌ AUTO-RECHAZADOS ({len(auto_rejected)} cambios con <50% confianza){self.colors['reset']}"
        )

        # Group by reason for rejection
        rejection_groups = {}
        for candidate in auto_rejected:
            reason = candidate.rule_applied or "low_confidence"
            if reason not in rejection_groups:
                rejection_groups[reason] = []
            rejection_groups[reason].append(candidate)

        for reason, candidates in rejection_groups.items():
            print(f"\n  📝 {reason} ({len(candidates)} casos):")
            for candidate in candidates[:3]:  # Show first 3
                print(
                    f"    • {candidate.old_name} → {candidate.new_name} [{candidate.confidence:.1%}]"
                )
            if len(candidates) > 3:
                print(f"    ... y {len(candidates) - 3} más")

    def _generate_validation_summary(
        self,
        auto_approved: list,
        manually_approved: list,
        auto_rejected: list,
        total_approved: int,
    ) -> dict:
        """Generate validation session summary"""
        return {
            "total_detected": len(auto_approved)
            + len(manually_approved)
            + len(auto_rejected),
            "auto_approved": len(auto_approved),
            "manually_approved": len(manually_approved),
            "auto_rejected": len(auto_rejected),
            "total_approved": total_approved,
            "user_decisions": self.user_decisions,
            "thresholds": {
                "auto_approve": self.auto_approve_threshold,
                "confidence": self.confidence_threshold,
            },
        }

    def show_final_summary(
        self,
        approved_candidates: list[RenameCandidate],
        validation_summary: dict,
        output_file: str,
    ):
        """Show final summary of validation session"""
        stats = validation_summary

        print(
            f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              📊 RESUMEN FINAL                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

📈 Estadísticas:
   • Total detectado: {stats['total_detected']}
   • {self.colors['pass']}Auto-aprobados: {stats['auto_approved']}{self.colors['reset']} (≥{stats['thresholds']['auto_approve']:.0%} confianza)
   • {self.colors['fail']}Aprobados manualmente: {stats['manually_approved']}{self.colors['reset']} 
   • {self.colors['error']}Rechazados: {stats['auto_rejected']}{self.colors['reset']}
   • {self.colors['bold']}TOTAL INCLUIDOS: {stats['total_approved']}{self.colors['reset']}

💾 Archivo actualizado: {output_file}
        """
        )

        # Show breakdown by module
        if approved_candidates:
            module_stats = {}
            for candidate in approved_candidates:
                module = candidate.module
                module_stats[module] = module_stats.get(module, 0) + 1

            print("📂 Por módulo:")
            for module, count in sorted(module_stats.items()):
                print(f"   • {module}: {count} cambios")

        print()  # Final newline
