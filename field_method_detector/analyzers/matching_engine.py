"""
Matching Engine with Inheritance Support
========================================

Single matching engine that integrates all rename detection capabilities:
- Direct signature matching
- Inheritance-aware detection
- Cross-reference generation
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

from config.naming_rules import naming_engine
from config.settings import SCORING_WEIGHTS, config
from core.models import Model, Field, Method, Reference, RenameCandidate

logger = logging.getLogger(__name__)


class MatchingEngine:
    """
    Matching engine that finds all types of renames including:
    - Direct renames
    - Inheritance impacts
    - Cross-reference impacts
    """

    # Global shared counter for unique change IDs across all instances
    _global_change_id_counter = 1

    def __init__(self, start_id: int = None):
        self.naming_engine = naming_engine
        if start_id is not None:
            MatchingEngine._global_change_id_counter = start_id

    @classmethod
    def get_next_change_id(cls) -> str:
        """Get next unique change ID across all MatchingEngine instances"""
        current_id = cls._global_change_id_counter
        cls._global_change_id_counter += 1
        return str(current_id)

    def find_all_renames(
        self,
        before_models: List[Model],
        after_models: List[Model],
        module_name: str,
        include_inheritance: bool = True,
        include_cross_references: bool = True,
    ) -> List[RenameCandidate]:
        """
        Single method that finds all types of renames:
        - Direct renames (original functionality)
        - Inheritance impacts (inheritance-aware functionality)
        - Cross-references (cross-reference functionality)
        """
        all_candidates = []

        # Phase 1: Direct renames
        direct_candidates = self._find_direct_renames(
            before_models, after_models, module_name
        )

        # Set module name for all candidates
        for candidate in direct_candidates:
            candidate.module = module_name

        all_candidates.extend(direct_candidates)

        # Phase 2: Inheritance impacts (if enabled)
        if include_inheritance:
            inheritance_candidates = self._find_inheritance_impacts(
                direct_candidates, before_models, after_models
            )
            all_candidates.extend(inheritance_candidates)

        # Phase 3: Cross-references (if enabled)
        if include_cross_references:
            cross_ref_candidates = self._find_cross_reference_impacts(
                direct_candidates, before_models, after_models
            )
            all_candidates.extend(cross_ref_candidates)

        return all_candidates

    def _find_direct_renames(
        self, before_models: List[Model], after_models: List[Model], module_name: str
    ) -> List[RenameCandidate]:
        """Find direct renames by comparing fields and methods"""
        candidates = []

        # Build maps for efficient lookup
        before_fields = self._build_field_map(before_models)
        after_fields = self._build_field_map(after_models)
        before_methods = self._build_method_map(before_models)
        after_methods = self._build_method_map(after_models)

        # Find field renames
        field_candidates = self._match_fields(before_fields, after_fields, module_name)
        candidates.extend(field_candidates)

        # Find method renames
        method_candidates = self._match_methods(
            before_methods, after_methods, module_name
        )
        candidates.extend(method_candidates)

        return candidates

    def _build_field_map(self, models: List[Model]) -> Dict[str, List[Field]]:
        """Build a map of model_name -> list of fields"""
        field_map = {}
        for model in models:
            field_map[model.name] = model.fields
        return field_map

    def _build_method_map(self, models: List[Model]) -> Dict[str, List[Method]]:
        """Build a map of model_name -> list of methods"""
        method_map = {}
        for model in models:
            method_map[model.name] = model.methods
        return method_map

    def _match_fields(
        self,
        before_fields: Dict[str, List[Field]],
        after_fields: Dict[str, List[Field]],
        module_name: str,
    ) -> List[RenameCandidate]:
        """Match fields between before and after to find renames"""
        candidates = []

        # For each model, compare fields
        for model_name in before_fields:
            if model_name not in after_fields:
                continue

            before_list = before_fields[model_name]
            after_list = after_fields[model_name]

            # Simple matching: look for missing fields in before and new fields in after
            before_names = {f.name for f in before_list}
            after_names = {f.name for f in after_list}

            missing_names = before_names - after_names
            new_names = after_names - before_names

            # Find optimal assignments to avoid cross-matching
            optimal_matches = self._find_optimal_matches(missing_names, new_names)

            for missing_name, new_name, confidence in optimal_matches:
                if confidence > config.confidence_threshold:  # Use configured threshold
                    # Auto-approve if high confidence
                    from core.models import ValidationStatus

                    validation_status = (
                        ValidationStatus.AUTO_APPROVED.value
                        if confidence >= 0.90
                        else ValidationStatus.PENDING.value
                    )

                    candidate = RenameCandidate.create_primary_declaration(
                        change_id=self.get_next_change_id(),
                        old_name=missing_name,
                        new_name=new_name,
                        item_type="field",
                        module="",  # Will be set by caller
                        model=model_name,
                        confidence=confidence,
                        source_file=before_list[0].source_file if before_list else "",
                        validation_status=validation_status,
                    )
                    candidates.append(candidate)
                    # ID is auto-incremented in get_next_change_id()

        return candidates

    def _match_methods(
        self,
        before_methods: Dict[str, List[Method]],
        after_methods: Dict[str, List[Method]],
        module_name: str,
    ) -> List[RenameCandidate]:
        """Match methods between before and after to find renames"""
        candidates = []

        # For each model, compare methods
        for model_name in before_methods:
            if model_name not in after_methods:
                continue

            before_list = before_methods[model_name]
            after_list = after_methods[model_name]

            # Simple matching: look for missing methods in before and new methods in after
            before_names = {m.name for m in before_list}
            after_names = {m.name for m in after_list}

            missing_names = before_names - after_names
            new_names = after_names - before_names

            # Find optimal assignments to avoid cross-matching
            optimal_matches = self._find_optimal_matches(missing_names, new_names)

            for missing_name, new_name, confidence in optimal_matches:
                if confidence > config.confidence_threshold:  # Use configured threshold
                    # Auto-approve if high confidence
                    from core.models import ValidationStatus

                    validation_status = (
                        ValidationStatus.AUTO_APPROVED.value
                        if confidence >= 0.90
                        else ValidationStatus.PENDING.value
                    )

                    candidate = RenameCandidate.create_primary_declaration(
                        change_id=self.get_next_change_id(),
                        old_name=missing_name,
                        new_name=new_name,
                        item_type="method",
                        module="",  # Will be set by caller
                        model=model_name,
                        confidence=confidence,
                        source_file=before_list[0].source_file if before_list else "",
                        validation_status=validation_status,
                    )
                    candidates.append(candidate)
                    # ID is auto-incremented in get_next_change_id()

        return candidates

    def _find_optimal_matches(
        self, missing_names: set, new_names: set
    ) -> List[Tuple[str, str, float]]:
        """Find optimal matches allowing many-to-one mappings (multiple old names to same new name)"""
        # Convert to lists for indexing
        missing_list = list(missing_names)
        new_list = list(new_names)

        # Log raw comparison count for debugging
        total_comparisons = len(missing_list) * len(new_list)
        if total_comparisons > 0:
            logger.debug(
                f"Evaluating {total_comparisons} raw comparisons ({len(missing_list)} missing × {len(new_list)} new)"
            )

        # Calculate all possible matches with similarities
        all_matches = []
        for missing in missing_list:
            for new in new_list:
                similarity = self._calculate_similarity(missing, new)
                if similarity > 0:  # Only consider non-zero similarities
                    all_matches.append((similarity, missing, new))

        # Sort by similarity descending (highest first)
        all_matches.sort(reverse=True)

        # Two-phase assignment to handle both one-to-one and many-to-one cases
        matches = []
        used_missing = set()

        # Phase 1: Handle high-confidence exact matches first (similarity >= 0.9)
        # These are likely perfect renames and should get priority
        for similarity, missing_name, new_name in all_matches:
            if similarity >= 0.9 and missing_name not in used_missing:
                matches.append((missing_name, new_name, similarity))
                used_missing.add(missing_name)

        # Phase 2: Handle remaining matches, allowing many-to-one
        # But be smart about avoiding obvious conflicts
        for similarity, missing_name, new_name in all_matches:
            if missing_name in used_missing:
                continue

            # Check if this would create a conflict with an existing high-confidence match
            conflict = False
            for existing_missing, existing_new, existing_conf in matches:
                # If we're trying to map to same new_name, only allow if:
                # 1. Current similarity is reasonably high (>= 0.6)
                # 2. OR there's no much better alternative for this missing_name
                if (
                    existing_new == new_name
                    and existing_conf >= 0.9
                    and similarity < 0.8
                ):
                    # Don't allow weak matches to high-confidence targets
                    conflict = True
                    break

            if not conflict:
                matches.append((missing_name, new_name, similarity))
                used_missing.add(missing_name)

        # Log filtering results for debugging
        if total_comparisons > 0:
            logger.debug(
                f"Filtered to {len(matches)} viable matches from {total_comparisons} comparisons"
            )

        return matches

    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names with semantic awareness"""
        if name1 == name2:
            return 1.0

        if len(name1) == 0 or len(name2) == 0:
            return 0.0

        # Check for incompatible semantic patterns in Odoo methods
        if self._are_semantically_incompatible(name1, name2):
            return 0.0

        # Check if one is a transformation of the other using naming rules
        if hasattr(self.naming_engine, "is_transformation"):
            if self.naming_engine.is_transformation(name1, name2):
                return 0.9

        # Use a more sophisticated similarity calculation
        return self._calculate_semantic_similarity(name1, name2)

    def _are_semantically_incompatible(self, name1: str, name2: str) -> bool:
        """Check if two method names represent incompatible semantic patterns"""
        # Define incompatible prefixes/patterns in Odoo
        action_patterns = ["action_", "button_", "open_", "show_"]
        compute_patterns = ["_compute_", "_calculate_", "_get_computed_"]
        api_patterns = ["api_", "json_", "jsonrpc_"]
        internal_patterns = ["_internal_", "_private_", "_helper_"]

        # Check if names have incompatible patterns
        name1_lower = name1.lower()
        name2_lower = name2.lower()

        # Action methods should not become compute methods
        if any(name1_lower.startswith(p) for p in action_patterns) and any(
            name2_lower.startswith(p) for p in compute_patterns
        ):
            return True

        if any(name1_lower.startswith(p) for p in compute_patterns) and any(
            name2_lower.startswith(p) for p in action_patterns
        ):
            return True

        # API methods should not become internal methods
        if any(name1_lower.startswith(p) for p in api_patterns) and any(
            name2_lower.startswith(p) for p in internal_patterns
        ):
            return True

        return False

    def _calculate_semantic_similarity(self, name1: str, name2: str) -> float:
        """Calculate semantic similarity considering word boundaries and structure"""
        # Split names into words (by underscore, camelCase, etc.)
        words1 = self._extract_words(name1)
        words2 = self._extract_words(name2)

        if not words1 or not words2:
            return 0.0

        # Calculate word-level similarity with synonyms and removable words
        exact_common = set(words1) & set(words2)
        synonym_matches = self._find_synonym_matches(words1, words2)
        removal_bonus = self._calculate_removal_bonus(words1, words2)

        total_matches = len(exact_common) + len(synonym_matches)
        total_words = len(set(words1) | set(words2))

        if total_words == 0:
            return 0.0

        word_similarity = (total_matches / total_words) + removal_bonus

        # Boost similarity if structural patterns match
        structure_bonus = self._calculate_structure_bonus(name1, name2)

        # Final similarity with structure consideration
        final_similarity = min(1.0, word_similarity + structure_bonus)

        return final_similarity

    def _find_synonym_matches(self, words1: List[str], words2: List[str]) -> Set[tuple]:
        """Find synonym matches between two word lists for Odoo-specific concepts"""
        # Define synonym groups for common Odoo concepts
        synonym_groups = [
            # Counting/quantity concepts - CORE for our use case
            {"number", "count", "qty", "quantity", "total", "amount", "sum"},
            # Product concepts (be more specific about item/product relationship)
            {"product", "products"},
            {"item", "items"},  # Keep separate - only match in specific contexts
            # Template/model concepts
            {"template", "tmpl", "model", "variant", "tpl"},
            # Related/associated concepts (often removed in renames)
            {"related", "associated", "linked", "connected", "ref"},
            # ID/identifier concepts (singular/plural)
            {"id", "ids", "identifier", "identifiers", "key", "keys"},
            # Compute/calculate concepts
            {"compute", "calculate", "calc", "get", "determine"},
            # Line/item list concepts
            {"line", "lines", "item", "items", "record", "records"},
            # State/status concepts
            {"state", "status", "stage", "phase"},
            # Transfer/movement concepts
            {"received", "delivered", "transferred", "moved", "sent"},
            # Common Odoo field suffixes/prefixes
            {"name", "title", "label", "description", "desc"},
            # Price/cost concepts (singular/plural)
            {"price", "prices", "cost", "costs", "rate", "rates"},
            # Update/modify concepts
            {"update", "updatable", "modify", "change", "edit", "alter"},
            # Action/view concepts (UI actions)
            {"open", "view", "show", "display", "action"},
            # Financial/invoice concepts
            {"invoice", "invoiced", "bill", "billing", "charge"},
            # Tax concepts
            {"tax", "taxed", "untaxed", "exempt"},
            # Amount/value concepts
            {"amount", "amounts", "value", "values", "sum", "total"},
            # Order/ordering concepts
            {"order", "orders", "ordering", "sequence"},
            # Assignment/log concepts
            {"assign", "assignation", "allocation", "log", "logs", "history"},
        ]

        matches = set()

        for word1 in words1:
            for word2 in words2:
                if word1 != word2:  # Skip exact matches (already counted)
                    # Check if words are in the same synonym group
                    for group in synonym_groups:
                        if word1 in group and word2 in group:
                            matches.add((word1, word2))
                            break

                    # Special contextual matching for item/product
                    if self._is_valid_item_product_match(word1, word2, words1, words2):
                        matches.add((word1, word2))

        return matches

    def _is_valid_item_product_match(
        self, word1: str, word2: str, words1: List[str], words2: List[str]
    ) -> bool:
        """Check if item/product synonym match is valid in context"""
        # Only allow item <-> product in appropriate contexts
        if not (
            (word1 == "item" and word2 == "product")
            or (word1 == "product" and word2 == "item")
        ):
            return False

        # Context words where item/product synonymy is invalid
        invalid_contexts = [
            # Financial/pricing contexts where item has different meaning
            "pricelist",
            "price",
            "cost",
            "invoice",
            "bill",
            # Document contexts where item means line items, not products
            "document",
            "report",
            "list",
            "menu",
            "view",
            # Configuration contexts
            "config",
            "setting",
            "option",
            "choice",
        ]

        # Check if any invalid context words are present
        all_words = set(words1) | set(words2)
        for invalid_word in invalid_contexts:
            if invalid_word in all_words:
                return False

        # Valid contexts where item/product synonymy makes sense
        valid_contexts = [
            # Sales/order contexts
            "sale",
            "order",
            "line",
            "qty",
            "quantity",
            # Inventory contexts
            "stock",
            "move",
            "picking",
            "delivery",
            # General product-related contexts
            "template",
            "variant",
            "attribute",
        ]

        # Allow if any valid context is present
        for valid_word in valid_contexts:
            if valid_word in all_words:
                return True

        # Default: be conservative and don't allow
        return False

    def _calculate_removal_bonus(self, words1: List[str], words2: List[str]) -> float:
        """Calculate bonus for words commonly removed in refactoring"""
        removable_words = {
            "related",
            "associated",
            "linked",
            "ref",
            "old",
            "new",
            "temp",
            "tmp",
        }

        words1_set = set(words1)
        words2_set = set(words2)

        # Find removable words that appear in one list but not the other
        removed_words = (words1_set & removable_words) - words2_set
        added_words = (words2_set & removable_words) - words1_set

        # Small bonus for each removed/added removable word (indicates refactoring)
        total_removable = len(removed_words) + len(added_words)
        max_total_words = max(len(words1), len(words2))

        if max_total_words == 0:
            return 0.0

        # Give up to 20% bonus for removable word patterns
        removal_bonus = min(0.2, (total_removable / max_total_words) * 0.3)

        return removal_bonus

    def _extract_words(self, name: str) -> List[str]:
        """Extract meaningful words from a method/field name"""
        import re

        # Remove common prefixes/suffixes that are structural
        name = re.sub(r"^_+|_+$", "", name)

        # Split on underscores and camelCase
        words = re.split(r"_+", name)
        result = []

        for word in words:
            # Split camelCase
            camel_words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)", word)
            if camel_words:
                result.extend([w.lower() for w in camel_words])
            else:
                result.append(word.lower())

        # Filter out very short words and common structural words
        structural_words = {
            "get",
            "set",
            "is",
            "has",
            "do",
            "to",
            "of",
            "for",
            "by",
            "id",
            "ids",
        }
        # Also filter words commonly removed in refactoring
        removable_words = {
            "related",
            "associated",
            "linked",
            "ref",
            "old",
            "new",
            "temp",
            "tmp",
        }
        meaningful_words = [
            w for w in result if len(w) > 2 and w not in structural_words
        ]

        return meaningful_words

    def _calculate_structure_bonus(self, name1: str, name2: str) -> float:
        """Calculate bonus for similar structural patterns"""
        # Check for similar prefixes (action_, compute_, etc.)
        if name1.startswith("_") and name2.startswith("_"):
            return 0.1
        if not name1.startswith("_") and not name2.startswith("_"):
            return 0.1

        # Check for similar suffixes
        if name1.endswith("_id") and name2.endswith("_id"):
            return 0.1
        if name1.endswith("_ids") and name2.endswith("_ids"):
            return 0.1

        return 0.0

    def _find_inheritance_impacts(
        self,
        direct_candidates: List[RenameCandidate],
        before_models: List[Model],
        after_models: List[Model],
    ) -> List[RenameCandidate]:
        """Find inheritance impacts for direct renames (simplified)"""
        # For now, return empty list - inheritance analysis would be more complex
        return []

    def _find_cross_reference_impacts(
        self,
        direct_candidates: List[RenameCandidate],
        before_models: List[Model],
        after_models: List[Model],
    ) -> List[RenameCandidate]:
        """Find cross-reference impacts for direct renames (simplified)"""
        # For now, return empty list - cross-reference analysis would be more complex
        return []

    def _convert_inventory_to_models(
        self, inventory: dict, file_path: str
    ) -> List[Model]:
        """Convert inventory format to Model objects"""
        models = []

        # Group fields and methods by model
        models_by_name = {}

        # Process fields
        for field_info in inventory.get("fields", []):
            model_name = field_info.get("model", "unknown")
            if model_name not in models_by_name:
                models_by_name[model_name] = {
                    "fields": [],
                    "methods": [],
                    "class_name": model_name.replace(".", "").title(),
                }

            field = Field(
                name=field_info["name"],
                field_type=field_info.get("field_type", ""),
                args=field_info.get("args", []),
                kwargs=field_info.get("kwargs", {}),
                signature=field_info.get("signature", ""),
                definition=field_info.get("definition", ""),
                line_number=field_info.get("line", 0),
                source_file=file_path,
            )
            models_by_name[model_name]["fields"].append(field)

        # Process methods
        for method_info in inventory.get("methods", []):
            model_name = method_info.get("model", "unknown")
            if model_name not in models_by_name:
                models_by_name[model_name] = {
                    "fields": [],
                    "methods": [],
                    "class_name": model_name.replace(".", "").title(),
                }

            method = Method(
                name=method_info["name"],
                args=method_info.get("args", []),
                decorators=method_info.get("decorators", []),
                signature=method_info.get("signature", ""),
                definition=method_info.get("definition", ""),
                line_number=method_info.get("line", 0),
                source_file=file_path,
            )
            models_by_name[model_name]["methods"].append(method)

        # Create Model objects
        for model_name, model_data in models_by_name.items():
            model = Model(
                name=model_name,
                class_name=model_data["class_name"],
                file_path=file_path,
                fields=model_data["fields"],
                methods=model_data["methods"],
            )
            models.append(model)

        return models
