"""
Inheritance Graph for Odoo Models
==================================

Tracks which modules define or extend models to properly classify
primary changes vs inherited changes.
"""

import logging
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
from core.models import Model, InheritanceType

logger = logging.getLogger(__name__)


class InheritanceGraph:
    """
    Tracks model inheritance across modules to identify:
    - Base module (where _name is defined)
    - Extension modules (where _inherit is used)
    """

    def __init__(self):
        # model_name -> {module: inheritance_type}
        self.model_definitions: Dict[str, Dict[str, str]] = defaultdict(dict)

        # model_name -> base_module (where _name is defined)
        self.base_modules: Dict[str, str] = {}

        # model_name -> [extension_modules] (where _inherit is used)
        self.extension_modules: Dict[str, List[str]] = defaultdict(list)

    def register_model(self, model: Model, module: str) -> None:
        """Register a model and its inheritance type"""
        model_name = model.name

        # Track this module's relationship to the model
        self.model_definitions[model_name][module] = model.inheritance_type.value

        logger.debug(
            f"Registering '{model_name}' from '{module}' "
            f"with inheritance_type='{model.inheritance_type.value}'"
        )

        # Determine if this is the base module or an extension
        if model.inheritance_type == InheritanceType.NAME:
            # This module defines the model with _name
            if model_name not in self.base_modules:
                self.base_modules[model_name] = module
                logger.debug(f"✓ BASE module '{module}' for model '{model_name}'")
            else:
                # Multiple modules define _name for same model - keep first one
                # (or we could use a heuristic to pick the "real" base)
                logger.warning(
                    f"Model '{model_name}' has _name in multiple modules: "
                    f"'{self.base_modules[model_name]}' and '{module}' (keeping first)"
                )
        else:
            # This module extends the model with _inherit
            if module not in self.extension_modules[model_name]:
                self.extension_modules[model_name].append(module)
                logger.debug(f"→ EXTENSION module '{module}' for model '{model_name}'")

    def is_base_module(self, model_name: str, module: str) -> bool:
        """Check if a module is the base module for a model"""
        return self.base_modules.get(model_name) == module

    def is_extension_module(self, model_name: str, module: str) -> bool:
        """Check if a module extends a model"""
        return module in self.extension_modules.get(model_name, [])

    def get_base_module(self, model_name: str) -> Optional[str]:
        """Get the base module for a model"""
        return self.base_modules.get(model_name)

    def get_extension_modules(self, model_name: str) -> List[str]:
        """Get all modules that extend a model"""
        return self.extension_modules.get(model_name, [])

    def get_all_modules_for_model(self, model_name: str) -> List[str]:
        """Get all modules (base + extensions) that touch a model"""
        modules = []
        base = self.get_base_module(model_name)
        if base:
            modules.append(base)
        modules.extend(self.get_extension_modules(model_name))
        return modules

    def classify_change(
        self, model_name: str, module: str, method_name: str
    ) -> Tuple[str, str]:
        """
        Classify a change as primary or inheritance-based.

        Returns:
            (change_scope, impact_type)
        """
        if self.is_base_module(model_name, module):
            # Change in the base module = primary declaration
            return "declaration", "primary"
        elif self.is_extension_module(model_name, module):
            # Change in extension module = inheritance override
            return "super_call", "inheritance"
        else:
            # Unknown relationship - be conservative and mark as primary
            logger.warning(
                f"Model '{model_name}' in module '{module}' has no clear inheritance relationship"
            )
            return "declaration", "primary"

    def find_related_changes(
        self,
        model_name: str,
        old_name: str,
        new_name: str,
        item_type: str,
        all_candidates: List
    ) -> List:
        """
        Find all changes related to a primary change in other modules.

        This helps identify when multiple modules have the same rename
        (e.g., _action_cancel -> action_cancel in sale, sale_loyalty, etc.)
        """
        related = []
        base_module = self.get_base_module(model_name)

        for candidate in all_candidates:
            if (
                candidate.model == model_name
                and candidate.old_name == old_name
                and candidate.new_name == new_name
                and candidate.item_type == item_type
                and candidate.module != base_module
            ):
                related.append(candidate)

        return related

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the inheritance graph"""
        return {
            "total_models": len(self.model_definitions),
            "base_models": len(self.base_modules),
            "extended_models": len(self.extension_modules),
            "total_extensions": sum(
                len(exts) for exts in self.extension_modules.values()
            ),
        }

    def print_summary(self) -> None:
        """Print a summary of the inheritance graph"""
        stats = self.get_stats()
        logger.info("=" * 60)
        logger.info("Inheritance Graph Summary")
        logger.info("=" * 60)
        logger.info(f"Total models tracked: {stats['total_models']}")
        logger.info(f"Base models (with _name): {stats['base_models']}")
        logger.info(f"Extended models: {stats['extended_models']}")
        logger.info(f"Total extensions: {stats['total_extensions']}")
        logger.info("")

        # Show examples of heavily extended models
        extended_counts = [
            (model, len(exts))
            for model, exts in self.extension_modules.items()
        ]
        extended_counts.sort(key=lambda x: x[1], reverse=True)

        logger.info("Most extended models:")
        for model, count in extended_counts[:10]:
            base = self.get_base_module(model)
            logger.info(f"  {model}: {count} extensions (base: {base})")
        logger.info("=" * 60)


def build_inheritance_graph(all_models: Dict[str, List[Model]]) -> InheritanceGraph:
    """
    Build inheritance graph from all models across modules.

    Args:
        all_models: Dictionary mapping module_name -> list of models

    Returns:
        InheritanceGraph with all models registered
    """
    graph = InheritanceGraph()

    for module_name, models in all_models.items():
        for model in models:
            graph.register_model(model, module_name)

    return graph
