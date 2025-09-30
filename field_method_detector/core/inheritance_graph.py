"""
Inheritance Graph for Odoo Model Analysis
=========================================

This module provides a comprehensive graph structure for analyzing Odoo model
inheritance relationships across multiple files. It builds a complete view of
how models inherit from each other and tracks method/field definitions and
references throughout the inheritance hierarchy.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
from core.models import Model, Field, Method, Reference, CallType

logger = logging.getLogger(__name__)


class InheritanceGraph:
    """
    Global graph of Odoo model inheritance relationships.

    This class provides a complete view of all models in a module and their
    inheritance relationships, enabling advanced analysis like finding all
    references to a method across inheritance hierarchies.
    """

    def __init__(self):
        # Core model storage
        self.models: Dict[str, Model] = {}

        # Inheritance relationship maps
        self.inheritance_edges: Dict[str, List[str]] = defaultdict(
            list
        )  # parent -> [children]
        self.reverse_inheritance: Dict[str, List[str]] = defaultdict(
            list
        )  # child -> [parents]

        # Method and field ownership resolution
        self._method_owners: Dict[Tuple[str, str], str] = (
            {}
        )  # (model, method) -> defining_model
        self._field_owners: Dict[Tuple[str, str], str] = (
            {}
        )  # (model, field) -> defining_model

        # Global reference maps
        self._all_references: List[Reference] = []

        # Cache for expensive operations
        self._inheritance_chains_cache: Dict[str, List[str]] = {}
        self._resolved_methods_cache: Dict[Tuple[str, str], Optional[str]] = {}

    def add_model(self, model: Model) -> None:
        """
        Add a model to the inheritance graph.

        Args:
            model: Model instance to add
        """
        logger.debug(f"Adding model {model.name} from {model.file_path}")

        # Store the model
        self.models[model.name] = model

        # Build inheritance relationships
        for parent_model in model.inherits_from:
            self.inheritance_edges[parent_model].append(model.name)
            self.reverse_inheritance[model.name].append(parent_model)

        # Add references to global collections
        self._all_references.extend(model.references)

        # Clear caches since graph structure changed
        self._clear_caches()

    def get_model(self, model_name: str) -> Optional[Model]:
        """Get a model by name"""
        return self.models.get(model_name)

    def get_all_model_names(self) -> List[str]:
        """Get all model names in the graph"""
        return list(self.models.keys())

    def get_inheritance_chain(self, model_name: str) -> List[str]:
        """
        Get the complete inheritance chain for a model.

        Returns a list of model names from most specific (child) to most general (root parent).
        Uses BFS to handle multiple inheritance correctly.

        Args:
            model_name: Name of the model to get inheritance chain for

        Returns:
            List of model names in inheritance order
        """
        if model_name in self._inheritance_chains_cache:
            return self._inheritance_chains_cache[model_name]

        if model_name not in self.models:
            return []

        # BFS to build inheritance chain
        chain = []
        visited = set()
        queue = deque([model_name])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue

            visited.add(current)
            chain.append(current)

            # Add parents to queue
            parents = self.reverse_inheritance.get(current, [])
            queue.extend(parents)

        # Cache result
        self._inheritance_chains_cache[model_name] = chain

        logger.debug(f"Inheritance chain for {model_name}: {chain}")
        return chain

    def find_method_definition(
        self, model_name: str, method_name: str
    ) -> Optional[str]:
        """
        Find which model actually defines a method in the inheritance hierarchy.

        This searches up the inheritance chain to find where a method is originally defined.

        Args:
            model_name: Name of the model that needs the method
            method_name: Name of the method to find

        Returns:
            Name of the model where the method is defined, or None if not found
        """
        cache_key = (model_name, method_name)
        if cache_key in self._resolved_methods_cache:
            return self._resolved_methods_cache[cache_key]

        # Search inheritance chain
        inheritance_chain = self.get_inheritance_chain(model_name)

        for model in inheritance_chain:
            model_obj = self.models.get(model)
            if not model_obj:
                continue

            # Check if this model defines the method
            for method in model_obj.methods:
                if method.name == method_name:
                    self._resolved_methods_cache[cache_key] = model
                    logger.debug(
                        f"Method {method_name} for {model_name} defined in {model}"
                    )
                    return model

        # Method not found in inheritance chain
        self._resolved_methods_cache[cache_key] = None
        logger.debug(
            f"Method {method_name} not found in inheritance chain for {model_name}"
        )
        return None

    def find_field_definition(self, model_name: str, field_name: str) -> Optional[str]:
        """
        Find which model actually defines a field in the inheritance hierarchy.

        Args:
            model_name: Name of the model that needs the field
            field_name: Name of the field to find

        Returns:
            Name of the model where the field is defined, or None if not found
        """
        # Search inheritance chain
        inheritance_chain = self.get_inheritance_chain(model_name)

        for model in inheritance_chain:
            model_obj = self.models.get(model)
            if not model_obj:
                continue

            # Check if this model defines the field
            for field_info in model_obj.fields:
                if field_info.name == field_name:
                    logger.debug(
                        f"Field {field_name} for {model_name} defined in {model}"
                    )
                    return model

        logger.debug(
            f"Field {field_name} not found in inheritance chain for {model_name}"
        )
        return None

    def find_all_references(
        self,
        reference_name: str,
        reference_type: Optional[str] = None,
        target_model: Optional[str] = None,
    ) -> List[Reference]:
        """
        Find all references to a specific method or field across the entire codebase.

        Args:
            reference_name: Name of the method or field to find references for
            reference_type: Optional type filter ('method' or 'field')
            target_model: Optional model name to filter references to specific model

        Returns:
            List of Reference objects representing all references
        """
        references = []

        for ref in self._all_references:
            if ref.reference_name == reference_name:
                if reference_type is None or ref.reference_type == reference_type:
                    if target_model is None or ref.target_model == target_model:
                        references.append(ref)

        logger.debug(
            f"Found {len(references)} references to {reference_type or 'method/field'} {reference_name}"
        )
        return references

    def find_method_references(
        self, method_name: str, target_model: Optional[str] = None
    ) -> List[Reference]:
        """Find all references to a specific method"""
        return self.find_all_references(method_name, "method", target_model)

    def find_field_references(
        self, field_name: str, target_model: Optional[str] = None
    ) -> List[Reference]:
        """Find all references to a specific field"""
        return self.find_all_references(field_name, "field", target_model)

    def get_children_models(self, model_name: str) -> List[str]:
        """
        Get all models that inherit from the given model.

        Args:
            model_name: Name of the parent model

        Returns:
            List of child model names
        """
        return self.inheritance_edges.get(model_name, [])

    def get_parent_models(self, model_name: str) -> List[str]:
        """
        Get all models that the given model inherits from.

        Args:
            model_name: Name of the child model

        Returns:
            List of parent model names
        """
        return self.reverse_inheritance.get(model_name, [])

    def resolve_cross_references(self) -> None:
        """
        Resolve target_model for all references.

        This should be called after all models have been added to ensure
        cross-references can be properly resolved through inheritance.
        """
        logger.info("Resolving cross-references in inheritance graph")

        # Resolve all references
        for ref in self._all_references:
            if not ref.target_model:  # Only resolve if not already set
                if ref.reference_type == "method":
                    target = self.find_method_definition(
                        ref.source_model, ref.reference_name
                    )
                elif ref.reference_type == "field":
                    target = self.find_field_definition(
                        ref.source_model, ref.reference_name
                    )
                else:
                    target = None

                if target:
                    ref.target_model = target

        logger.info("Cross-reference resolution complete")

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the inheritance graph"""
        total_methods = sum(len(model.methods) for model in self.models.values())
        total_fields = sum(len(model.fields) for model in self.models.values())

        # Count inheritance relationships
        inheritance_relationships = sum(
            len(children) for children in self.inheritance_edges.values()
        )

        # Count references by type
        method_references = len(
            [r for r in self._all_references if r.reference_type == "method"]
        )
        field_references = len(
            [r for r in self._all_references if r.reference_type == "field"]
        )

        return {
            "total_models": len(self.models),
            "total_methods": total_methods,
            "total_fields": total_fields,
            "inheritance_relationships": inheritance_relationships,
            "total_references": len(self._all_references),
            "method_references": method_references,
            "field_references": field_references,
            "cached_inheritance_chains": len(self._inheritance_chains_cache),
        }

    def _clear_caches(self) -> None:
        """Clear all internal caches"""
        self._inheritance_chains_cache.clear()
        self._resolved_methods_cache.clear()

    def validate_graph_integrity(self) -> List[str]:
        """
        Validate the integrity of the inheritance graph.

        Returns:
            List of validation errors (empty if graph is valid)
        """
        errors = []

        # Check for orphaned inheritance references
        for model_name, parents in self.reverse_inheritance.items():
            for parent in parents:
                if parent not in self.models:
                    errors.append(
                        f"Model {model_name} inherits from unknown model {parent}"
                    )

        # Check for circular inheritance
        for model_name in self.models:
            chain = self.get_inheritance_chain(model_name)
            if len(chain) != len(set(chain)):
                errors.append(f"Circular inheritance detected for model {model_name}")

        # Check for consistency in bidirectional inheritance maps
        for parent, children in self.inheritance_edges.items():
            for child in children:
                if parent not in self.reverse_inheritance.get(child, []):
                    errors.append(
                        f"Inconsistent inheritance: {child} -> {parent} not bidirectional"
                    )

        return errors
