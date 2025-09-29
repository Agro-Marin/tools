"""
Matching Engine for Field and Method Renames
==============================================

Core algorithm for detecting renamed fields and methods using AST signatures
and AgroMarin naming rules.
"""

import logging
from dataclasses import dataclass
from typing import Any

from config.naming_rules import naming_engine
from config.settings import SCORING_WEIGHTS

logger = logging.getLogger(__name__)


@dataclass
class RenameCandidate:
    """Data class for rename candidates"""

    old_name: str
    new_name: str
    item_type: str  # 'field' or 'method'
    module: str
    model: str
    confidence: float
    signature_match: bool
    rule_applied: str | None = None
    scoring_breakdown: dict[str, float] | None = None
    validations: list[dict] | None = None
    api_changes: dict | None = None
    file_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "old_name": self.old_name,
            "new_name": self.new_name,
            "type": self.item_type,
            "module": self.module,
            "model": self.model,
            "confidence": self.confidence,
            "signature_match": self.signature_match,
            "rule_applied": self.rule_applied,
            "scoring_breakdown": self.scoring_breakdown or {},
            "validations": self.validations or [],
            "api_changes": self.api_changes,
            "file_path": self.file_path,
        }


class MatchingEngine:
    """Main engine for detecting field and method renames"""

    def __init__(self):
        self.naming_engine = naming_engine
        self.scoring_weights = SCORING_WEIGHTS

    def find_renames_in_inventories(
        self,
        before_inventory: dict,
        after_inventory: dict,
        module_name: str,
        file_path: str = "",
    ) -> list[RenameCandidate]:
        """
        Find renames between two code inventories.

        Args:
            before_inventory: Code inventory from before commit
            after_inventory: Code inventory from after commit
            module_name: Name of the Odoo module
            file_path: Path to the file being analyzed

        Returns:
            List of rename candidates
        """
        candidates = []

        # Find field renames
        field_candidates = self._find_field_renames(
            before_inventory.get("fields", []),
            after_inventory.get("fields", []),
            module_name,
            file_path,
        )
        candidates.extend(field_candidates)

        # Find method renames
        method_candidates = self._find_method_renames(
            before_inventory.get("methods", []),
            after_inventory.get("methods", []),
            module_name,
            file_path,
        )
        candidates.extend(method_candidates)

        # Debug logging for matching process
        logger.debug(f"\n--- MATCHING ENGINE ANALYSIS for {file_path} ---")
        logger.debug(
            f"Fields processed: {len(before_inventory.get('fields', []))} → {len(after_inventory.get('fields', []))}"
        )
        logger.debug(
            f"Methods processed: {len(before_inventory.get('methods', []))} → {len(after_inventory.get('methods', []))}"
        )
        logger.debug(f"Total candidates found: {len(candidates)}")

        if candidates:
            for candidate in candidates:
                logger.debug(
                    f"  Candidate: {candidate.old_name} → {candidate.new_name}"
                )
                logger.debug(f"    Type: {candidate.item_type}")
                logger.debug(f"    Confidence: {candidate.confidence:.3f}")
                logger.debug(f"    Rule: {candidate.rule_applied}")
                if candidate.scoring_breakdown:
                    logger.debug(f"    Scoring: {candidate.scoring_breakdown}")

        logger.debug(f"--- END MATCHING ANALYSIS ---\n")
        return candidates

    def _find_field_renames(
        self,
        fields_before: list[dict],
        fields_after: list[dict],
        module_name: str,
        file_path: str,
    ) -> list[RenameCandidate]:
        """Find renamed fields using signature matching and naming rules"""
        candidates = []

        logger.debug(f"\n  === FIELD RENAME ANALYSIS ===")
        logger.debug(
            f"  Fields before: {[(f['name'], f.get('signature', 'no-sig')) for f in fields_before]}"
        )
        logger.debug(
            f"  Fields after: {[(f['name'], f.get('signature', 'no-sig')) for f in fields_after]}"
        )

        for field_before in fields_before:
            # Check if the original field still exists (indicating it wasn't renamed)
            field_still_exists = any(
                f["name"] == field_before["name"] for f in fields_after
            )
            if field_still_exists:
                # Field still exists, so it wasn't renamed - skip
                logger.debug(
                    f"  Field '{field_before['name']}' still exists, skipping rename detection"
                )
                continue

            # Find fields with matching signature but different name
            signature_matches = self._find_signature_matches(field_before, fields_after)
            renamed_matches = [
                f for f in signature_matches if f["name"] != field_before["name"]
            ]

            if len(renamed_matches) == 1:
                field_after = renamed_matches[0]

                # Validate rename using naming rules
                validation = self._validate_field_rename(field_before, field_after)

                if validation["confidence"] >= 0.50:  # Minimum threshold
                    candidate = RenameCandidate(
                        old_name=field_before["name"],
                        new_name=field_after["name"],
                        item_type="field",
                        module=module_name,
                        model=field_before.get("model", ""),
                        confidence=validation["confidence"],
                        signature_match=True,
                        rule_applied=validation.get("rule_applied"),
                        scoring_breakdown=validation.get("scoring_breakdown"),
                        validations=validation.get("validations"),
                        api_changes=validation.get("api_changes"),
                        file_path=file_path,
                    )
                    candidates.append(candidate)

            elif len(renamed_matches) > 1:
                # Multiple matches - need disambiguation
                logger.debug(
                    f"Multiple signature matches for field {field_before['name']}: "
                    f"{[f['name'] for f in renamed_matches]}"
                )

                # Try to disambiguate using naming rules
                best_match = self._disambiguate_matches(
                    field_before, renamed_matches, "field"
                )
                if best_match:
                    validation = self._validate_field_rename(field_before, best_match)
                    if (
                        validation["confidence"] >= 0.40
                    ):  # Lower threshold for disambiguated
                        candidate = RenameCandidate(
                            old_name=field_before["name"],
                            new_name=best_match["name"],
                            item_type="field",
                            module=module_name,
                            model=field_before.get("model", ""),
                            confidence=validation["confidence"],
                            signature_match=True,
                            rule_applied=validation.get("rule_applied"),
                            scoring_breakdown=validation.get("scoring_breakdown"),
                            validations=validation.get("validations"),
                            api_changes=validation.get("api_changes"),
                            file_path=file_path,
                        )
                        candidates.append(candidate)

            else:
                # No exact signature matches - try fuzzy matching for field type compatibility
                fuzzy_matches = self._find_fuzzy_field_matches(
                    field_before, fields_after
                )
                if fuzzy_matches:
                    logger.debug(
                        f"Fuzzy matches for field {field_before['name']}: "
                        f"{[f['name'] for f in fuzzy_matches]}"
                    )

                    # Try to find the best fuzzy match using naming rules
                    best_match = self._disambiguate_matches(
                        field_before, fuzzy_matches, "field"
                    )
                    if best_match:
                        validation = self._validate_field_rename(
                            field_before, best_match
                        )
                        if (
                            validation["confidence"] >= 0.65
                        ):  # Slightly higher threshold for fuzzy matches based on data analysis
                            candidate = RenameCandidate(
                                old_name=field_before["name"],
                                new_name=best_match["name"],
                                item_type="field",
                                module=module_name,
                                model=field_before.get("model", ""),
                                confidence=validation["confidence"],
                                signature_match=False,  # Not exact signature match
                                rule_applied=validation.get("rule_applied"),
                                scoring_breakdown=validation.get("scoring_breakdown"),
                                validations=validation.get("validations"),
                                api_changes=validation.get("api_changes"),
                                file_path=file_path,
                            )
                            candidates.append(candidate)

        return candidates

    def _find_method_renames(
        self,
        methods_before: list[dict],
        methods_after: list[dict],
        module_name: str,
        file_path: str,
    ) -> list[RenameCandidate]:
        """Find renamed methods using signature matching and naming rules"""
        candidates = []

        for method_before in methods_before:
            # Check if the original method still exists (indicating it wasn't renamed)
            method_still_exists = any(
                m["name"] == method_before["name"] for m in methods_after
            )
            if method_still_exists:
                # Method still exists, so it wasn't renamed - skip
                logger.debug(
                    f"  Method '{method_before['name']}' still exists, skipping rename detection"
                )
                continue

            # Find methods with matching signature but different name
            signature_matches = self._find_signature_matches(
                method_before, methods_after
            )
            renamed_matches = [
                m for m in signature_matches if m["name"] != method_before["name"]
            ]

            if len(renamed_matches) == 1:
                method_after = renamed_matches[0]

                # Validate rename using naming rules
                validation = self._validate_method_rename(method_before, method_after)

                if (
                    validation["confidence"] >= 0.55
                ):  # Slightly higher threshold based on successful patterns
                    candidate = RenameCandidate(
                        old_name=method_before["name"],
                        new_name=method_after["name"],
                        item_type="method",
                        module=module_name,
                        model=method_before.get("model", ""),
                        confidence=validation["confidence"],
                        signature_match=True,
                        rule_applied=validation.get("rule_applied"),
                        scoring_breakdown=validation.get("scoring_breakdown"),
                        validations=validation.get("validations"),
                        api_changes=validation.get("api_changes"),
                        file_path=file_path,
                    )
                    candidates.append(candidate)

            elif len(renamed_matches) > 1:
                # Multiple matches - try disambiguation
                best_match = self._disambiguate_matches(
                    method_before, renamed_matches, "method"
                )
                if best_match:
                    validation = self._validate_method_rename(method_before, best_match)
                    if validation["confidence"] >= 0.40:
                        candidate = RenameCandidate(
                            old_name=method_before["name"],
                            new_name=best_match["name"],
                            item_type="method",
                            module=module_name,
                            model=method_before.get("model", ""),
                            confidence=validation["confidence"],
                            signature_match=True,
                            rule_applied=validation.get("rule_applied"),
                            scoring_breakdown=validation.get("scoring_breakdown"),
                            validations=validation.get("validations"),
                            api_changes=validation.get("api_changes"),
                            file_path=file_path,
                        )
                        candidates.append(candidate)

        return candidates

    def _find_signature_matches(
        self, target_item: dict, candidate_items: list[dict]
    ) -> list[dict]:
        """Find items with matching signatures"""
        matches = []
        target_signature = target_item.get("signature", "")

        logger.debug(
            f"    Looking for signature matches for '{target_item['name']}' (sig: {target_signature[:50]}...)"
        )

        if not target_signature:
            logger.debug(f"    No signature for '{target_item['name']}', skipping")
            return matches

        for candidate in candidate_items:
            candidate_signature = candidate.get("signature", "")
            if candidate_signature == target_signature:
                matches.append(candidate)
                logger.debug(f"      ✅ Signature match: {candidate['name']}")
            else:
                logger.debug(
                    f"      ❌ No match: {candidate['name']} (sig: {candidate_signature[:50]}...)"
                )

        logger.debug(f"    Total signature matches: {len(matches)}")
        return matches

    def _find_fuzzy_field_matches(
        self, target_field: dict, candidate_fields: list[dict]
    ) -> list[dict]:
        """Find fields with compatible types and contexts for fuzzy matching"""
        matches = []
        target_field_type = target_field.get("field_type", "")
        target_name = target_field["name"]

        logger.debug(
            f"    Looking for fuzzy matches for '{target_name}' (type: {target_field_type})"
        )

        if not target_field_type:
            return matches

        # Only look for candidates with different names that don't already have exact matches
        remaining_candidates = [f for f in candidate_fields if f["name"] != target_name]

        for candidate in remaining_candidates:
            candidate_field_type = candidate.get("field_type", "")
            candidate_name = candidate["name"]

            # Check if field types are compatible
            if self._are_field_types_compatible(
                target_field_type, candidate_field_type
            ):
                # Check if the candidate follows naming rules from target
                validation = self._validate_field_rename(target_field, candidate)
                confidence = validation.get("confidence", 0.0)

                # Only consider if there's some naming rule match
                if confidence > 0.30:  # Basic threshold for fuzzy matching
                    matches.append(candidate)
                    logger.debug(
                        f"      ✅ Fuzzy match: {candidate_name} (type: {candidate_field_type}, confidence: {confidence:.3f})"
                    )
                else:
                    logger.debug(
                        f"      ❌ Low confidence: {candidate_name} (type: {candidate_field_type}, confidence: {confidence:.3f})"
                    )
            else:
                logger.debug(
                    f"      ❌ Incompatible type: {candidate_name} ({candidate_field_type} vs {target_field_type})"
                )

        logger.debug(f"    Total fuzzy matches: {len(matches)}")
        return matches

    def _are_field_types_compatible(self, type1: str, type2: str) -> bool:
        """Check if two field types are compatible for rename detection"""
        if type1 == type2:
            return True

        # Define compatible field type groups
        relational_types = {"Many2one", "One2many", "Many2many"}
        numeric_types = {"Integer", "Float", "Monetary"}
        text_types = {"Char", "Text", "Html"}
        temporal_types = {"Date", "Datetime"}

        # Check if both types are in the same compatibility group
        for type_group in [relational_types, numeric_types, text_types, temporal_types]:
            if type1 in type_group and type2 in type_group:
                return True

        return False

    def _disambiguate_matches(
        self, target_item: dict, matches: list[dict], item_type: str
    ) -> dict | None:
        """Disambiguate multiple signature matches using naming rules"""
        best_match = None
        best_score = 0.0

        for match in matches:
            if item_type == "field":
                validation = self._validate_field_rename(target_item, match)
            else:
                validation = self._validate_method_rename(target_item, match)

            confidence = validation.get("confidence", 0.0)
            if confidence > best_score:
                best_score = confidence
                best_match = match

        return best_match if best_score > 0.30 else None

    def _validate_field_rename(self, field_before: dict, field_after: dict) -> dict:
        """Validate field rename using naming rules and conventions"""
        validation = self.naming_engine.validate_rename(
            old_name=field_before["name"],
            new_name=field_after["name"],
            item_type="field",
            field_type=field_after.get("field_type"),
            old_definition=field_before.get("definition", ""),
            new_definition=field_after.get("definition", ""),
        )

        # Ensure confidence is calculated
        if "confidence" not in validation or validation["confidence"] is None:
            validation["confidence"] = self.calculate_comprehensive_confidence(
                validation
            )

        # Add bonus for type compatibility in fuzzy matching
        field_before_type = field_before.get("field_type", "")
        field_after_type = field_after.get("field_type", "")
        if field_before_type and field_after_type:
            if field_before_type == field_after_type:
                # Exact type match bonus
                validation["confidence"] += 0.15
                validation.setdefault("scoring_breakdown", {})[
                    "exact_type_match"
                ] = 0.15
            elif self._are_field_types_compatible(field_before_type, field_after_type):
                # Compatible type bonus
                validation["confidence"] += 0.10
                validation.setdefault("scoring_breakdown", {})["compatible_type"] = 0.10

        # Cap confidence at 1.0
        validation["confidence"] = min(validation["confidence"], 1.0)

        return validation

    def _validate_method_rename(self, method_before: dict, method_after: dict) -> dict:
        """Validate method rename using naming rules"""
        validation = self.naming_engine.validate_rename(
            old_name=method_before["name"],
            new_name=method_after["name"],
            item_type="method",
            decorators=method_after.get("decorators", []),
            old_definition=method_before.get("definition", ""),
            new_definition=method_after.get("definition", ""),
        )

        # Ensure confidence is calculated
        if "confidence" not in validation or validation["confidence"] is None:
            validation["confidence"] = self.calculate_comprehensive_confidence(
                validation
            )

        return validation

    def calculate_comprehensive_confidence(self, validation_result: dict) -> float:
        """Calculate comprehensive confidence score using weighted components"""
        scoring_breakdown = validation_result.get("scoring_breakdown", {})

        # Apply weights to each component
        weighted_score = 0.0
        for component, weight in self.scoring_weights.items():
            component_score = scoring_breakdown.get(component, 0.0)
            weighted_score += component_score * weight

        # Add signature match base score
        if validation_result.get("signature_match", False):
            weighted_score += self.scoring_weights["signature_match"]

        return min(weighted_score, 1.0)  # Cap at 1.0

    def group_similar_renames(
        self, candidates: list[RenameCandidate]
    ) -> dict[str, list[RenameCandidate]]:
        """Group similar rename patterns for batch processing"""
        groups = {}

        for candidate in candidates:
            # Create pattern key based on rule applied and module
            pattern_key = f"{candidate.rule_applied}_{candidate.module}"

            if pattern_key not in groups:
                groups[pattern_key] = []

            groups[pattern_key].append(candidate)

        # Filter groups with multiple items
        return {k: v for k, v in groups.items() if len(v) > 1}

    def filter_high_confidence_renames(
        self, candidates: list[RenameCandidate], threshold: float = 0.90
    ) -> tuple[list[RenameCandidate], list[RenameCandidate]]:
        """Separate high confidence renames from those needing review"""
        high_confidence = []
        needs_review = []

        for candidate in candidates:
            if candidate.confidence >= threshold:
                high_confidence.append(candidate)
            else:
                needs_review.append(candidate)

        return high_confidence, needs_review

    def generate_confidence_summary(
        self, candidates: list[RenameCandidate]
    ) -> dict[str, Any]:
        """Generate summary statistics about confidence levels"""
        if not candidates:
            return {
                "total_candidates": 0,
                "average_confidence": 0.0,
                "confidence_distribution": {},
                "rule_distribution": {},
                "module_distribution": {},
            }

        total = len(candidates)
        avg_confidence = sum(c.confidence for c in candidates) / total

        # Confidence distribution
        confidence_ranges = {
            "90-100%": sum(1 for c in candidates if c.confidence >= 0.90),
            "75-89%": sum(1 for c in candidates if 0.75 <= c.confidence < 0.90),
            "50-74%": sum(1 for c in candidates if 0.50 <= c.confidence < 0.75),
            "<50%": sum(1 for c in candidates if c.confidence < 0.50),
        }

        # Rule distribution
        rule_dist = {}
        for candidate in candidates:
            rule = candidate.rule_applied or "No rule"
            rule_dist[rule] = rule_dist.get(rule, 0) + 1

        # Module distribution
        module_dist = {}
        for candidate in candidates:
            module = candidate.module
            module_dist[module] = module_dist.get(module, 0) + 1

        return {
            "total_candidates": total,
            "average_confidence": avg_confidence,
            "confidence_distribution": confidence_ranges,
            "rule_distribution": rule_dist,
            "module_distribution": module_dist,
        }
