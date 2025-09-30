"""
Cross-Reference Analyzer for Rename Detection
=============================================

Analyzes cross-references between field/method renames and generates
impact candidates with proper parent-child relationships.
"""

import logging
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
import uuid

from core.models import (
    RenameCandidate,
    Model,
    Reference,
    CallType,
    ValidationStatus,
    ChangeScope,
    ImpactType,
)
from config.settings import config

logger = logging.getLogger(__name__)


@dataclass
class ImpactCandidate:
    """Represents a potential impact from a rename"""

    reference: Reference
    target_model: str
    confidence: float
    impact_type: str
    change_scope: str
    context: str


class CrossReferenceAnalyzer:
    """
    Analyzes cross-references and generates impact candidates for renames.

    This component takes primary rename candidates and analyzes all references
    to generate the complete set of impacts that need to be applied.
    """

    def __init__(self):
        self.confidence_weights = {
            # Base confidence based on reference type
            "self_reference": 0.90,  # High confidence for same-model references
            "self_call": 0.90,  # High confidence for same-model calls
            "cross_model": 0.80,  # Medium confidence for cross-model references
            "cross_model_call": 0.80,  # Medium confidence for cross-model calls
            "inheritance": config.confidence_threshold
            + 0.25,  # Medium confidence for inheritance
            "decorator": 0.85,  # High confidence for decorators
            "super_call": 0.85,  # High confidence for super calls
        }

    def generate_all_rename_candidates(
        self, primary_changes: List[RenameCandidate], all_models: Dict[str, List[Model]]
    ) -> List[RenameCandidate]:
        """
        Convierte cambios primarios + todas sus referencias a RenameCandidate con IDs secuenciales.

        Esta es la función principal que implementa el flujo del plan para generar
        todas las 179+ referencias con IDs secuenciales simples.

        Args:
            primary_changes: Lista de cambios primarios detectados
            all_models: Diccionario de todos los modelos organizados por módulo

        Returns:
            Lista de todos los candidatos (primarios + impactos) con IDs secuenciales
        """
        from analyzers.matching_engine import MatchingEngine

        all_candidates = []

        for primary_change in primary_changes:
            logger.debug(
                f"Processing primary change: {primary_change.old_name} -> {primary_change.new_name}"
            )

            # 1. NO sobreescribir change_id - mantener el único que viene del MatchingEngine
            # Solo configurar campos que no afecten el ID único
            primary_change.change_scope = ChangeScope.DECLARATION.value
            primary_change.impact_type = ImpactType.PRIMARY.value
            primary_change.context = ""
            primary_change.parent_change_id = ""
            primary_change.validation_status = self._auto_validate_primary(
                primary_change
            )

            all_candidates.append(primary_change)

            # 2. Buscar todas las referencias cruzadas
            cross_references = self._find_all_cross_references(
                primary_change, all_models
            )

            # 3. Convertir cada referencia a RenameCandidate con ID único global
            for reference in cross_references:
                impact_candidate = self._reference_to_candidate(
                    reference, primary_change, MatchingEngine.get_next_change_id()
                )
                all_candidates.append(impact_candidate)

            logger.debug(
                f"Generated {len(cross_references)} cross-references for {primary_change.old_name}"
            )

        logger.info(
            f"Total candidates generated: {len(all_candidates)} (including {len(primary_changes)} primary)"
        )
        return all_candidates

    def generate_impact_candidates(
        self,
        primary_candidates: List[RenameCandidate],
        all_models: Dict[str, List[Model]],
    ) -> List[RenameCandidate]:
        """
        Generate impact candidates for primary rename candidates.

        Args:
            primary_candidates: List of primary rename candidates
            all_models: Dictionary mapping module names to lists of models

        Returns:
            List of all candidates (primary + impacts)
        """
        all_candidates = []

        for primary in primary_candidates:
            logger.debug(
                f"Analyzing impacts for {primary.old_name} -> {primary.new_name}"
            )

            # Add the primary candidate
            all_candidates.append(primary)

            # Find all impacts for this rename
            impacts = self._find_impacts_for_rename(primary, all_models)

            # Convert impacts to candidates
            impact_candidates = self._convert_impacts_to_candidates(primary, impacts)
            all_candidates.extend(impact_candidates)

            logger.debug(
                f"Found {len(impact_candidates)} impacts for {primary.old_name}"
            )

        return all_candidates

    def _find_impacts_for_rename(
        self, primary: RenameCandidate, all_models: Dict[str, List[Model]]
    ) -> List[ImpactCandidate]:
        """Find all impacts for a primary rename candidate"""
        impacts = []

        # Search through all models for references to the renamed item
        for module_name, models in all_models.items():
            for model in models:
                for reference in model.references:
                    # Check if this reference matches our rename
                    if self._reference_matches_rename(reference, primary):
                        impact = self._create_impact_candidate(
                            reference, primary, model
                        )
                        if impact:
                            impacts.append(impact)

        return impacts

    def _reference_matches_rename(
        self, reference: Reference, primary: RenameCandidate
    ) -> bool:
        """Check if a reference matches the primary rename"""
        # Must match the name and type
        if (
            reference.reference_name != primary.old_name
            or reference.reference_type != primary.item_type
        ):
            return False

        # For self-references, must be in the same model
        if reference.call_type == CallType.SELF:
            return reference.source_model == primary.model

        # For cross-model references, check target model
        if reference.call_type == CallType.CROSS_MODEL:
            # If target model is specified, it must match
            if reference.target_model:
                return reference.target_model == primary.model
            else:
                # Target model not specified - this would need resolution
                # For now, assume it could match
                return True

        # For decorators, check if they're in the same model
        if reference.call_type == CallType.DECORATOR:
            return reference.source_model == primary.model

        # For super calls, check inheritance relationships
        if reference.call_type == CallType.SUPER:
            # This would need inheritance graph analysis
            # For now, assume it could match if same item type
            return True

        return False

    def _create_impact_candidate(
        self, reference: Reference, primary: RenameCandidate, source_model: Model
    ) -> Optional[ImpactCandidate]:
        """Create an impact candidate from a reference"""

        # Determine impact type and change scope
        impact_type, change_scope = self._determine_impact_type_and_scope(
            reference, primary
        )

        # Calculate confidence
        confidence = self._calculate_impact_confidence(reference, primary)

        # Determine context
        context = self._determine_context(reference, impact_type)

        return ImpactCandidate(
            reference=reference,
            target_model=reference.source_model,
            confidence=confidence,
            impact_type=impact_type,
            change_scope=change_scope,
            context=context,
        )

    def _determine_impact_type_and_scope(
        self, reference: Reference, primary: RenameCandidate
    ) -> Tuple[str, str]:
        """Determine the impact type and change scope for a reference"""
        impact_type = self._determine_impact_type(reference, primary)
        change_scope = self._determine_change_scope(reference)
        return impact_type, change_scope

    def _determine_impact_type(
        self, reference: Reference, primary: RenameCandidate
    ) -> str:
        """Determine the impact type based on reference characteristics"""

        if reference.call_type == CallType.SELF:
            if reference.source_model == primary.model:
                # Same model reference
                if reference.reference_type == "method":
                    return "self_call"
                else:
                    return "self_reference"

        elif reference.call_type == CallType.CROSS_MODEL:
            # Cross-model reference
            if reference.reference_type == "method":
                return "cross_model_call"
            else:
                return "cross_model"

        elif reference.call_type == CallType.SUPER:
            return "inheritance"

        elif reference.call_type == CallType.DECORATOR:
            return "decorator"

        # Default case
        return "self_reference"

    def _determine_change_scope(self, reference: Reference) -> str:
        """Determine the change scope based on reference type"""

        if reference.call_type == CallType.SUPER:
            return "super_call"
        elif reference.reference_type == "method":
            return "call"
        else:
            return "reference"

    def _calculate_impact_confidence(
        self, reference: Reference, primary: RenameCandidate
    ) -> float:
        """Calculate confidence score for an impact"""

        # Start with base confidence from impact type
        if reference.call_type == CallType.SELF:
            base_confidence = self.confidence_weights["self_reference"]
            if reference.reference_type == "method":
                base_confidence = self.confidence_weights["self_call"]
        elif reference.call_type == CallType.CROSS_MODEL:
            base_confidence = self.confidence_weights["cross_model"]
            if reference.reference_type == "method":
                base_confidence = self.confidence_weights["cross_model_call"]
        elif reference.call_type == CallType.SUPER:
            base_confidence = self.confidence_weights["super_call"]
        elif reference.call_type == CallType.DECORATOR:
            base_confidence = self.confidence_weights["decorator"]
        else:
            base_confidence = 0.70  # Default moderate confidence

        # Adjust based on primary candidate confidence
        # If primary has low confidence, impacts should also have lower confidence
        adjusted_confidence = base_confidence * (0.8 + 0.2 * primary.confidence)

        return min(1.0, adjusted_confidence)

    def _determine_context(self, reference: Reference, impact_type: str) -> str:
        """Determine the context for applying this impact"""

        if impact_type == "decorator":
            # For decorators, context is the type of decorator
            return "api.depends"  # Simplified - could be enhanced to detect actual decorator

        elif impact_type in [
            "self_reference",
            "self_call",
            "cross_model",
            "cross_model_call",
        ]:
            # For references and calls, context is the method where they occur
            return reference.source_method or ""

        elif impact_type == "inheritance":
            # For inheritance, context is the method with super() call
            return reference.source_method or ""

        return ""

    def _convert_impacts_to_candidates(
        self, primary: RenameCandidate, impacts: List[ImpactCandidate]
    ) -> List[RenameCandidate]:
        """Convert impact candidates to RenameCandidate objects"""
        candidates = []

        for impact in impacts:
            candidate = RenameCandidate.create_impact_candidate(
                parent_change_id=primary.change_id,
                old_name=primary.old_name,
                new_name=primary.new_name,
                item_type=primary.item_type,
                module=primary.module,  # Could be different for cross-model impacts
                model=impact.target_model,
                change_scope=impact.change_scope,
                impact_type=impact.impact_type,
                context=impact.context,
                confidence=impact.confidence,
                source_file=impact.reference.source_file,
                line_number=impact.reference.line_number,
            )
            candidates.append(candidate)

        return candidates

    def _auto_validate_primary(self, primary_change: RenameCandidate) -> str:
        """Auto-aprueba cambios primarios con alta confianza"""
        if primary_change.confidence >= 0.90:
            return ValidationStatus.AUTO_APPROVED.value
        else:
            return ValidationStatus.PENDING.value

    def _find_all_cross_references(
        self, primary_change: RenameCandidate, all_models: Dict[str, List[Model]]
    ) -> List[Reference]:
        """Busca todas las referencias cruzadas para un cambio primario"""
        references = []

        # Buscar en todos los modelos
        for module_name, models in all_models.items():
            for model in models:
                for reference in model.references:
                    if self._reference_matches_rename(reference, primary_change):
                        references.append(reference)

        return references

    def _reference_to_candidate(
        self, reference: Reference, primary: RenameCandidate, change_id: str
    ) -> RenameCandidate:
        """Convierte Reference a RenameCandidate"""

        # Determinar tipo de impacto y alcance
        impact_type, change_scope = self._determine_impact_type_and_scope(
            reference, primary
        )

        # Calcular confianza
        confidence = self._calculate_reference_confidence(reference, primary)

        # Determinar contexto
        context = self._determine_context(reference, impact_type)

        # Determinar módulo (extraer del source_model)
        module = (
            reference.source_model.split(".")[0]
            if reference.source_model
            else primary.module
        )

        return RenameCandidate(
            change_id=change_id,
            old_name=primary.old_name,
            new_name=primary.new_name,
            item_type=primary.item_type,
            module=module,
            model=(
                reference.target_model
                if reference.target_model
                else reference.source_model
            ),
            change_scope=change_scope,
            impact_type=impact_type,
            context=context,
            confidence=confidence,
            parent_change_id=primary.change_id,
            validation_status=self._auto_validate_reference(reference, confidence),
            source_file=reference.source_file,
            line_number=reference.line_number,
            # Heredar del primario
            signature_match=primary.signature_match,
            rule_applied=primary.rule_applied,
        )

    def _calculate_reference_confidence(
        self, reference: Reference, primary: RenameCandidate
    ) -> float:
        """Calcula confianza para una referencia específica"""
        # Usar el método existente
        return self._calculate_impact_confidence(reference, primary)

    def _auto_validate_reference(self, reference: Reference, confidence: float) -> str:
        """Auto-aprueba referencias con alta confianza"""
        if confidence >= 0.90:
            return ValidationStatus.AUTO_APPROVED.value
        else:
            return ValidationStatus.PENDING.value


def analyze_cross_references(
    primary_candidates: List[RenameCandidate], all_models: Dict[str, List[Model]]
) -> List[RenameCandidate]:
    """
    Convenience function to analyze cross-references for rename candidates.

    Args:
        primary_candidates: List of primary rename candidates
        all_models: Dictionary of all models organized by module

    Returns:
        List of all candidates including primary declarations and impacts
    """
    analyzer = CrossReferenceAnalyzer()
    return analyzer.generate_all_rename_candidates(primary_candidates, all_models)


if __name__ == "__main__":
    # Example usage
    logger.basicConfig(level=logging.DEBUG)

    # This would typically be called from the main detection script
    print("Cross-Reference Analyzer initialized")
    print("Use analyze_cross_references() to process rename candidates")
