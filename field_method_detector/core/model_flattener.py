"""
Model Flattener for Odoo Inheritance Resolution
==============================================

This module provides functionality to "flatten" Odoo models by resolving
inheritance relationships and creating complete views of models with all
inherited fields, methods, and references.
"""

import logging
from typing import Dict, List, Optional
from core.model_registry import ModelRegistry
from core.models import Model, Field, Method, Reference, InheritanceType

logger = logging.getLogger(__name__)


class ModelFlattener:
    """Flattens Odoo models by resolving inheritance relationships"""

    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self._flattened_cache: Dict[str, Model] = {}

    def get_flattened_model(
        self, model_name: str, use_cache: bool = True
    ) -> Optional[Model]:
        """
        Get a complete flattened view of a model with all inheritance resolved.

        Args:
            model_name: Name of the model to flatten (e.g., 'sale.order')
            use_cache: Whether to use cached results

        Returns:
            Model with all fields/methods from inheritance chain, or None if model not found
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

        # Create flattened model by merging all definitions
        flattened = self._create_flattened_model(model_name, model_definitions)

        # Cache result
        if use_cache:
            self._flattened_cache[model_name] = flattened

        logger.debug(
            f"Flattened {model_name}: {len(flattened.fields)} fields, {len(flattened.methods)} methods"
        )

        return flattened

    def _create_flattened_model(
        self, model_name: str, definitions: List[Model]
    ) -> Model:
        """
        Create a flattened model by merging all definitions with inheritance resolution.

        Args:
            model_name: Name of the model to flatten
            definitions: List of Model objects for the same model name

        Returns:
            Model with all fields/methods from inheritance chain resolved
        """
        # Find base model and inheritance models
        base_model = self._find_base_model(definitions)
        inheritance_models = [
            d for d in definitions if d.inheritance_type == InheritanceType.INHERIT
        ]

        # Start with base model if it exists
        if base_model:
            flattened = Model(
                name=model_name,
                class_name=base_model.class_name,
                file_path=base_model.file_path,
                line_number=base_model.line_number,
                inheritance_type=base_model.inheritance_type,
                inherits_from=base_model.inherits_from.copy(),
                inherited_by=base_model.inherited_by.copy(),
                fields=[],
                methods=[],
                references=[],
            )
        else:
            # No base model, use first inheritance model as base
            first_model = definitions[0] if definitions else None
            if not first_model:
                logger.warning(f"No definitions found for model {model_name}")
                return Model(name=model_name, class_name="", file_path="")

            flattened = Model(
                name=model_name,
                class_name=first_model.class_name,
                file_path=first_model.file_path,
                line_number=first_model.line_number,
                inheritance_type=first_model.inheritance_type,
                inherits_from=first_model.inherits_from.copy(),
                inherited_by=first_model.inherited_by.copy(),
                fields=[],
                methods=[],
                references=[],
            )

        # Flatten fields and methods
        self._flatten_fields(flattened, definitions)
        self._flatten_methods(flattened, definitions)
        self._flatten_references(flattened, definitions)

        return flattened

    def _find_base_model(self, definitions: List[Model]) -> Optional[Model]:
        """Find the base model definition (the one with _name)"""
        for definition in definitions:
            if definition.inheritance_type == InheritanceType.NAME:
                return definition
        return None

    def _flatten_fields(self, flattened: Model, definitions: List[Model]) -> None:
        """Flatten all fields from inheritance chain with proper override handling"""
        field_registry: Dict[str, Field] = {}

        # Process base model first, then inheritance models
        base_model = self._find_base_model(definitions)
        inheritance_models = [
            d for d in definitions if d.inheritance_type == InheritanceType.INHERIT
        ]

        ordered_definitions = []
        if base_model:
            ordered_definitions.append(base_model)
        ordered_definitions.extend(inheritance_models)

        # Process each model in inheritance order
        for definition in ordered_definitions:
            is_inherited_context = (
                definition.inheritance_type == InheritanceType.INHERIT
            )

            for field in definition.fields:
                # Create unified field with inheritance metadata
                unified_field = Field(
                    name=field.name,
                    field_type=field.field_type,
                    args=field.args.copy(),
                    kwargs=field.kwargs.copy(),
                    signature=field.signature,
                    definition=field.definition,
                    line_number=field.line_number,
                    source_file=field.source_file,
                    defined_in_model=definition.name,
                    is_inherited=is_inherited_context,
                    is_overridden=field.name in field_registry,
                )

                # Later definitions override earlier ones
                field_registry[field.name] = unified_field

        flattened.fields = list(field_registry.values())

    def _flatten_methods(self, flattened: Model, definitions: List[Model]) -> None:
        """Flatten all methods from inheritance chain with proper override handling"""
        method_registry: Dict[str, Method] = {}

        # Process base model first, then inheritance models
        base_model = self._find_base_model(definitions)
        inheritance_models = [
            d for d in definitions if d.inheritance_type == InheritanceType.INHERIT
        ]

        ordered_definitions = []
        if base_model:
            ordered_definitions.append(base_model)
        ordered_definitions.extend(inheritance_models)

        # Process each model in inheritance order
        for definition in ordered_definitions:
            is_inherited_context = (
                definition.inheritance_type == InheritanceType.INHERIT
            )

            for method in definition.methods:
                # Create unified method with inheritance metadata
                unified_method = Method(
                    name=method.name,
                    args=method.args.copy(),
                    decorators=method.decorators.copy(),
                    signature=method.signature,
                    definition=method.definition,
                    line_number=method.line_number,
                    source_file=method.source_file,
                    defined_in_model=definition.name,
                    is_inherited=is_inherited_context,
                    is_overridden=method.name in method_registry,
                )

                # Later definitions override earlier ones
                method_registry[method.name] = unified_method

        flattened.methods = list(method_registry.values())

    def _flatten_references(self, flattened: Model, definitions: List[Model]) -> None:
        """Flatten all references from all model definitions"""
        all_references = []

        for definition in definitions:
            all_references.extend(definition.references)

        flattened.references = all_references

    def get_models_affected_by_file_change(self, file_path: str) -> List[str]:
        """
        Get all model names that could be affected by changes to a specific file.

        Args:
            file_path: Path to the changed file

        Returns:
            List of model names that have definitions in this file
        """
        affected_models = []

        for model_name in self.registry.get_all_model_names():
            definitions = self.registry.get_models_for_name(model_name)
            for definition in definitions:
                if definition.file_path == file_path:
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
