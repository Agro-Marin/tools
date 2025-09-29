"""
Model Flattener for Odoo Inheritance Resolution
==============================================

This module provides functionality to "flatten" Odoo models by resolving
inheritance relationships and creating complete views of models with all
inherited fields, methods, and references.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from .model_registry import (
    ModelRegistry,
    ModelDefinition,
    FieldDefinition,
    MethodDefinition,
)

logger = logging.getLogger(__name__)


@dataclass
class FlattenedField:
    """A field in a flattened model with inheritance source info"""

    name: str
    field_type: str
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, str] = field(default_factory=dict)
    signature: str = ""
    definition: str = ""
    line_number: int = 0
    source_file: str = ""
    defined_in_model: str = ""  # Which model originally defined this field
    is_inherited: bool = False


@dataclass
class FlattenedMethod:
    """A method in a flattened model with inheritance source info"""

    name: str
    args: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    signature: str = ""
    definition: str = ""
    line_number: int = 0
    source_file: str = ""
    defined_in_model: str = ""  # Which model originally defined this method
    is_inherited: bool = False
    is_overridden: bool = False  # True if this method overrides a parent method


@dataclass
class CrossReference:
    """Represents a cross-reference between models (field/method usage)"""

    reference_type: str  # 'field' or 'method'
    reference_name: str
    source_method: str
    source_model: str
    source_file: str
    line_number: int = 0
    target_model: str = ""  # Model where the referenced item is actually defined


@dataclass
class FlattenedModel:
    """Complete flattened view of an Odoo model with all inheritance resolved"""

    model_name: str
    base_model_file: str = ""  # File where the base model (_name) is defined
    inheritance_chain: List[str] = field(
        default_factory=list
    )  # Ordered list of models in inheritance chain
    all_fields: List[FlattenedField] = field(default_factory=list)
    all_methods: List[FlattenedMethod] = field(default_factory=list)
    cross_references: List[CrossReference] = field(default_factory=list)

    def get_field_by_name(self, name: str) -> Optional[FlattenedField]:
        """Get a field by name"""
        for field_def in self.all_fields:
            if field_def.name == name:
                return field_def
        return None

    def get_method_by_name(self, name: str) -> Optional[FlattenedMethod]:
        """Get a method by name"""
        for method_def in self.all_methods:
            if method_def.name == name:
                return method_def
        return None

    def get_fields_defined_in_file(self, file_path: str) -> List[FlattenedField]:
        """Get all fields defined in a specific file"""
        return [f for f in self.all_fields if f.source_file == file_path]

    def get_methods_defined_in_file(self, file_path: str) -> List[FlattenedMethod]:
        """Get all methods defined in a specific file"""
        return [m for m in self.all_methods if m.source_file == file_path]


class ModelFlattener:
    """Flattens Odoo models by resolving inheritance relationships"""

    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self._flattened_cache: Dict[str, FlattenedModel] = {}

    def get_flattened_model(
        self, model_name: str, use_cache: bool = True
    ) -> Optional[FlattenedModel]:
        """
        Get a complete flattened view of a model with all inheritance resolved.

        Args:
            model_name: Name of the model to flatten (e.g., 'sale.order')
            use_cache: Whether to use cached results

        Returns:
            FlattenedModel with all fields/methods from inheritance chain, or None if model not found
        """
        if use_cache and model_name in self._flattened_cache:
            return self._flattened_cache[model_name]

        model_definitions = self.registry.get_models_for_name(model_name)
        if not model_definitions:
            logger.warning(f"Model {model_name} not found in registry")
            return None

        logger.debug(
            f"Flattening model {model_name} with {len(model_definitions)} definitions"
        )

        # Build inheritance chain
        inheritance_chain = self._build_inheritance_chain(model_name, model_definitions)

        # Create flattened model
        flattened = FlattenedModel(
            model_name=model_name, inheritance_chain=inheritance_chain
        )

        # Find base model file
        base_model = self._find_base_model(model_definitions)
        if base_model:
            flattened.base_model_file = base_model.source_file

        # Flatten fields and methods in inheritance order
        self._flatten_fields(flattened, model_definitions)
        self._flatten_methods(flattened, model_definitions)

        # Extract cross-references
        self._extract_cross_references(flattened, model_definitions)

        # Cache result
        if use_cache:
            self._flattened_cache[model_name] = flattened

        logger.debug(
            f"Flattened {model_name}: {len(flattened.all_fields)} fields, {len(flattened.all_methods)} methods"
        )

        return flattened

    def _build_inheritance_chain(
        self, model_name: str, definitions: List[ModelDefinition]
    ) -> List[str]:
        """Build ordered inheritance chain for a model"""
        # For now, implement simple inheritance chain
        # In the future, this could be enhanced to handle complex inheritance graphs

        chain = []

        # Add base model first
        base_model = self._find_base_model(definitions)
        if base_model:
            chain.append(f"{base_model.source_file}:{base_model.class_name}")

        # Add inheritance models in order they appear
        for definition in definitions:
            if definition.is_inheritance():
                chain.append(f"{definition.source_file}:{definition.class_name}")

        return chain

    def _find_base_model(
        self, definitions: List[ModelDefinition]
    ) -> Optional[ModelDefinition]:
        """Find the base model definition (the one with _name)"""
        for definition in definitions:
            if definition.is_base_model():
                return definition
        return None

    def _flatten_fields(
        self, flattened: FlattenedModel, definitions: List[ModelDefinition]
    ) -> None:
        """
        Flatten all fields from inheritance chain into a unified view.

        This is the core algorithm that resolves field inheritance in Odoo models.
        It processes fields in inheritance order (base model first, then inheritance
        models) and handles field overriding correctly.

        Algorithm:
        1. Create temporary registry to track fields by name
        2. Establish processing order: base model → inheritance models
        3. For each model definition in order:
           - Process all fields in that model
           - Mark fields as inherited if they come from inheritance models
           - Override earlier fields with later definitions (inheritance semantics)
        4. Convert final registry to list

        Field Override Behavior:
        - If a field appears in both base and inheritance models, inheritance wins
        - If multiple inheritance models define the same field, last one wins
        - Original field source information is preserved for tracking

        Args:
            flattened: Target FlattenedModel to populate with fields
            definitions: List of ModelDefinition objects for the same model name

        Side Effects:
            - Modifies flattened.all_fields with resolved field list
            - Fields maintain source traceability (file, line, model)

        Example:
            Base model 'sale.order' defines: amount_total (Monetary)
            Inheritance model defines: amount_total (Float)
            Result: amount_total (Float) from inheritance model wins
        """
        # Registry to track fields by name (allows override detection)
        field_registry: Dict[str, FlattenedField] = {}

        # Establish inheritance processing order (critical for correct overriding)
        # Base model (_name) must be processed first, then inheritance models (_inherit)
        base_model = self._find_base_model(definitions)
        inheritance_models = [d for d in definitions if d.is_inheritance()]

        ordered_definitions = []
        if base_model:
            ordered_definitions.append(base_model)
        ordered_definitions.extend(inheritance_models)

        logger.debug(
            f"Flattening fields in order: {[d.class_name for d in ordered_definitions]}"
        )

        # Process each model definition in inheritance order
        for definition in ordered_definitions:
            is_inherited_context = definition != base_model

            for field_def in definition.fields:
                # Check if this field name already exists (override detection)
                existing_field = field_registry.get(field_def.name)
                if existing_field:
                    logger.debug(
                        f"Field '{field_def.name}' overridden: {existing_field.source_file} → {field_def.source_file}"
                    )

                # Create flattened field with inheritance metadata
                flattened_field = FlattenedField(
                    name=field_def.name,
                    field_type=field_def.field_type,
                    args=field_def.args,
                    kwargs=field_def.kwargs,
                    signature=field_def.signature,
                    definition=field_def.definition,
                    line_number=field_def.line_number,
                    source_file=field_def.source_file,
                    defined_in_model=definition.get_target_model() or "",
                    is_inherited=is_inherited_context,
                )

                # Store in registry - later definitions automatically override earlier ones
                # This implements Odoo's inheritance semantics where inheritance models override base
                field_registry[field_def.name] = flattened_field

        # Convert final registry to list (order no longer matters since we have metadata)
        flattened.all_fields = list(field_registry.values())
        logger.debug(
            f"Field flattening complete: {len(flattened.all_fields)} total fields"
        )

    def _flatten_methods(
        self, flattened: FlattenedModel, definitions: List[ModelDefinition]
    ) -> None:
        """
        Flatten all methods from inheritance chain with override detection.

        This algorithm resolves method inheritance and override semantics in Odoo models.
        Unlike fields, methods have more complex override behavior where both the original
        and overriding method can be called using super().

        Algorithm:
        1. Create temporary registry to track methods by name
        2. Establish processing order: base model → inheritance models
        3. For each model definition in order:
           - Process all methods in that model
           - Detect if method overrides a previous definition
           - Mark methods with inheritance and override metadata
           - Later definitions override earlier ones in registry
        4. Convert final registry to list

        Method Override Behavior:
        - If method appears in both base and inheritance: inheritance version wins
        - Override detection allows tracking of super() call patterns
        - Original method source information preserved for analysis
        - Method signatures may change between base and override

        Args:
            flattened: Target FlattenedModel to populate with methods
            definitions: List of ModelDefinition objects for the same model name

        Side Effects:
            - Modifies flattened.all_methods with resolved method list
            - Methods maintain source traceability and override status

        Override Detection:
        The is_overridden flag indicates this method replaces a previous definition.
        This is crucial for rename detection across inheritance boundaries.

        Example:
            Base model 'sale.order' defines: def confirm(self)
            Inheritance model defines: def confirm(self) with super() call
            Result: confirm() from inheritance wins, marked as is_overridden=True
        """
        # Registry to track methods by name (enables override detection)
        method_registry: Dict[str, FlattenedMethod] = {}

        # Establish inheritance processing order (same as fields - critical for correctness)
        base_model = self._find_base_model(definitions)
        inheritance_models = [d for d in definitions if d.is_inheritance()]

        ordered_definitions = []
        if base_model:
            ordered_definitions.append(base_model)
        ordered_definitions.extend(inheritance_models)

        logger.debug(
            f"Flattening methods in order: {[d.class_name for d in ordered_definitions]}"
        )

        # Process each model definition in inheritance order
        for definition in ordered_definitions:
            is_inherited_context = definition != base_model

            for method_def in definition.methods:
                # Check if this method name already exists (override detection)
                existing_method = method_registry.get(method_def.name)
                is_method_override = existing_method is not None

                if is_method_override:
                    logger.debug(
                        f"Method '{method_def.name}' overridden: {existing_method.source_file} → {method_def.source_file}"
                    )

                # Create flattened method with inheritance and override metadata
                flattened_method = FlattenedMethod(
                    name=method_def.name,
                    args=method_def.args,
                    decorators=method_def.decorators,
                    signature=method_def.signature,
                    definition=method_def.definition,
                    line_number=method_def.line_number,
                    source_file=method_def.source_file,
                    defined_in_model=definition.get_target_model() or "",
                    is_inherited=is_inherited_context,
                    is_overridden=is_method_override,  # Critical for rename detection
                )

                # Store in registry - later definitions automatically override earlier ones
                # This mirrors Odoo's method resolution order where inheritance methods override base
                method_registry[method_def.name] = flattened_method

        # Convert final registry to list (order preserved through metadata)
        flattened.all_methods = list(method_registry.values())
        logger.debug(
            f"Method flattening complete: {len(flattened.all_methods)} total methods"
        )

    def _extract_cross_references(
        self, flattened: FlattenedModel, definitions: List[ModelDefinition]
    ) -> None:
        """Extract cross-references (method calls and field references) within the model"""
        cross_refs = []

        for definition in definitions:
            # Extract method calls
            for method_call in definition.method_calls:
                # Check if the called method exists in the flattened model
                target_method = flattened.get_method_by_name(method_call.method_name)
                target_model = ""

                if target_method:
                    target_model = target_method.defined_in_model

                cross_ref = CrossReference(
                    reference_type="method",
                    reference_name=method_call.method_name,
                    source_method=method_call.calling_method,
                    source_model=definition.get_target_model() or "",
                    source_file=method_call.source_file,
                    line_number=method_call.line_number,
                    target_model=target_model,
                )
                cross_refs.append(cross_ref)

            # Extract field references
            for field_ref in definition.field_references:
                # Check if the referenced field exists in the flattened model
                target_field = flattened.get_field_by_name(field_ref.field_name)
                target_model = ""

                if target_field:
                    target_model = target_field.defined_in_model

                cross_ref = CrossReference(
                    reference_type="field",
                    reference_name=field_ref.field_name,
                    source_method=field_ref.referencing_method,
                    source_model=definition.get_target_model() or "",
                    source_file=field_ref.source_file,
                    line_number=field_ref.line_number,
                    target_model=target_model,
                )
                cross_refs.append(cross_ref)

        flattened.cross_references = cross_refs

    def get_models_affected_by_file_change(self, file_path: str) -> List[str]:
        """
        Get all model names that could be affected by changes to a specific file.

        This is useful for determining which models need to be re-analyzed when
        a specific file changes.

        Args:
            file_path: Path to the changed file

        Returns:
            List of model names that have definitions in this file
        """
        affected_models = []

        for model_name in self.registry.get_all_model_names():
            definitions = self.registry.get_models_for_name(model_name)
            for definition in definitions:
                if definition.source_file == file_path:
                    affected_models.append(model_name)
                    break

        return affected_models

    def clear_cache(self) -> None:
        """Clear the flattened model cache"""
        self._flattened_cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "cached_models": len(self._flattened_cache),
            "total_models": len(self.registry.get_all_model_names()),
        }
