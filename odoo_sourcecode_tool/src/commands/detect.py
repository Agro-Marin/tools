"""
Command module for field/method change detection
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from core.ordering import Ordering
from core.config import Config
from core.git_manager import GitManager
from core.odoo_module_utils import OdooModuleUtils
from core.base_processor import ProcessingStatus, ProcessResult

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
    file_path: str = ""


class DetectCommand:
    """Command handler for detecting field/method renames"""

    def __init__(self, config: Config):
        """Initialize detect command with configuration"""
        self.config = config
        self.git_manager = GitManager(config.repo_path)
        self.ordering = Ordering(config)

    def execute(
        self,
        from_commit: str | None,
        to_commit: str | None,
        output_file: str,
    ) -> ProcessResult:
        """
        Execute detection operation

        Args:
            from_commit: Starting commit (optional, will auto-detect)
            to_commit: Ending commit (optional, will use HEAD)
            output_file: Output CSV file path

        Returns:
            ProcessResult with status and details
        """
        try:
            # Resolve commits
            if not to_commit:
                to_commit = "HEAD"
            to_sha = self.git_manager.resolve_commit(to_commit)

            if not from_commit:
                # Find a reasonable base commit (e.g., last merge to main)
                from_commit = self.git_manager.get_merge_base("main", to_commit)
                if not from_commit:
                    logger.error("Could not auto-detect base commit")
                    return ProcessResult(
                        file_path=Path(self.config.repo_path),
                        status=ProcessingStatus.ERROR,
                        error_message="Could not auto-detect base commit",
                    )

            from_sha = self.git_manager.resolve_commit(from_commit)

            logger.info(f"Detecting changes from {from_sha[:8]} to {to_sha[:8]}")

            # Get modified files
            modified_files = self.git_manager.get_modified_files(from_sha, to_sha)
            python_files = [f for f in modified_files if f.endswith(".py")]

            # Filter by module if specified
            if self.config.modules:
                python_files = self._filter_by_modules(python_files)

            logger.info(f"Analyzing {len(python_files)} Python files")

            # Analyze each file
            all_candidates = []
            for file_path in python_files:
                candidates = self._analyze_file(file_path, from_sha, to_sha)
                all_candidates.extend(candidates)

            # Filter by confidence threshold
            filtered = [
                c
                for c in all_candidates
                if c.confidence >= self.config.detection.confidence_threshold
            ]

            logger.info(f"Found {len(filtered)} rename candidates above threshold")

            # Interactive validation if enabled
            if self.config.interactive:
                filtered = self._interactive_validation(filtered)

            # Save to CSV
            data = []
            for f in filtered:
                data.append(
                    {
                        "old_name": f.old_name,
                        "new_name": f.new_name,
                        "item_type": f.item_type,
                        "module": f.module,
                        "model": f.model,
                        "confidence": round(f.confidence, 3),
                        "signature_match": f.signature_match,
                        "file_path": f.file_path,
                    }
                )
            df = pd.DataFrame(data)
            df.to_csv(output_file, index=False)
            logger.info(f"Saved {len(filtered)} changes to {output_file}")
            return ProcessResult(
                file_path=Path(output_file),
                status=ProcessingStatus.SUCCESS,
                changes_applied=len(filtered),
            )

        except Exception as e:
            logger.error(f"Error during detection: {e}")
            return ProcessResult(
                file_path=(
                    Path(output_file) if output_file else Path(self.config.repo_path)
                ),
                status=ProcessingStatus.ERROR,
                error_message=str(e),
            )

    def _analyze_file(
        self,
        file_path: str,
        from_sha: str,
        to_sha: str,
    ) -> list[RenameCandidate]:
        """Analyze a single file for renames"""
        candidates = []

        try:
            # Get file content at both commits
            before_content = self.git_manager.get_file_content_at_commit(
                file_path, from_sha
            )
            after_content = self.git_manager.get_file_content_at_commit(
                file_path, to_sha
            )

            if not before_content or not after_content:
                return candidates

            # Get inventories
            before_inventory = self.ordering.get_inventory(before_content, file_path)
            after_inventory = self.ordering.get_inventory(after_content, file_path)

            # Find field renames
            field_candidates = self._find_field_renames(
                before_inventory.get("fields", []),
                after_inventory.get("fields", []),
                file_path,
            )
            candidates.extend(field_candidates)

            # Find method renames
            method_candidates = self._find_method_renames(
                before_inventory.get("methods", []),
                after_inventory.get("methods", []),
                file_path,
            )
            candidates.extend(method_candidates)

        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")

        return candidates

    def _find_field_renames(
        self,
        before_fields: list[dict],
        after_fields: list[dict],
        file_path: str,
    ) -> list[RenameCandidate]:
        """Find renamed fields"""
        candidates = []

        # Create lookup by name
        before_by_name = {f["name"]: f for f in before_fields}
        after_by_name = {f["name"]: f for f in after_fields}

        # Find removed fields
        removed = set(before_by_name.keys()) - set(after_by_name.keys())

        # Find added fields
        added = set(after_by_name.keys()) - set(before_by_name.keys())

        # Match removed with added based on similarity
        for old_name in removed:
            old_field = before_by_name[old_name]

            for new_name in added:
                new_field = after_by_name[new_name]

                # Calculate confidence based on various factors
                confidence = self._calculate_field_confidence(
                    old_field, new_field, old_name, new_name
                )

                if confidence >= 0.5:  # Minimum threshold
                    # Extract module and model from file path
                    module = OdooModuleUtils.get_module_name_from_path(Path(file_path))
                    if not module:
                        module = "unknown"
                    model = old_field.get("class", "unknown")

                    candidates.append(
                        RenameCandidate(
                            old_name=old_name,
                            new_name=new_name,
                            item_type="field",
                            module=module,
                            model=model,
                            confidence=confidence,
                            signature_match=old_field.get("type")
                            == new_field.get("type"),
                            file_path=file_path,
                        )
                    )

        return candidates

    def _find_method_renames(
        self,
        before_methods: list[dict],
        after_methods: list[dict],
        file_path: str,
    ) -> list[RenameCandidate]:
        """Find renamed methods"""
        candidates = []

        # Create lookup by name
        before_by_name = {m["name"]: m for m in before_methods}
        after_by_name = {m["name"]: m for m in after_methods}

        # Find removed methods
        removed = set(before_by_name.keys()) - set(after_by_name.keys())

        # Find added methods
        added = set(after_by_name.keys()) - set(before_by_name.keys())

        # Match removed with added
        for old_name in removed:
            old_method = before_by_name[old_name]

            for new_name in added:
                new_method = after_by_name[new_name]

                # Calculate confidence
                confidence = self._calculate_method_confidence(
                    old_method, new_method, old_name, new_name
                )

                if confidence >= 0.5:
                    module = OdooModuleUtils.get_module_name_from_path(Path(file_path))
                    if not module:
                        module = "unknown"
                    model = old_method.get("class", "unknown")

                    candidates.append(
                        RenameCandidate(
                            old_name=old_name,
                            new_name=new_name,
                            item_type="method",
                            module=module,
                            model=model,
                            confidence=confidence,
                            signature_match=self._methods_have_same_signature(
                                old_method, new_method
                            ),
                            file_path=file_path,
                        )
                    )

        return candidates

    def _calculate_field_confidence(
        self,
        old_field: dict,
        new_field: dict,
        old_name: str,
        new_name: str,
    ) -> float:
        """Calculate confidence score for field rename"""
        score = 0.0

        # Same type = high confidence
        if old_field.get("type") == new_field.get("type"):
            score += 0.4

        # Similar attributes
        old_attrs = set(old_field.get("attributes", {}).keys())
        new_attrs = set(new_field.get("attributes", {}).keys())
        if old_attrs and new_attrs:
            similarity = len(old_attrs & new_attrs) / len(old_attrs | new_attrs)
            score += similarity * 0.3

        # Name similarity (using simple ratio)
        name_similarity = self._string_similarity(old_name, new_name)
        score += name_similarity * 0.3

        return min(score, 1.0)

    def _calculate_method_confidence(
        self,
        old_method: dict,
        new_method: dict,
        old_name: str,
        new_name: str,
    ) -> float:
        """Calculate confidence score for method rename"""
        score = 0.0

        # Same decorators = high confidence
        old_decorators = set(old_method.get("decorators", []))
        new_decorators = set(new_method.get("decorators", []))
        if old_decorators == new_decorators and old_decorators:
            score += 0.5

        # Same method type
        if old_method.get("type") == new_method.get("type"):
            score += 0.2

        # Name similarity
        name_similarity = self._string_similarity(old_name, new_name)
        score += name_similarity * 0.3

        return min(score, 1.0)

    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate simple string similarity"""
        # Remove common prefixes/suffixes
        s1_clean = s1.replace("_", "").lower()
        s2_clean = s2.replace("_", "").lower()

        # Levenshtein distance approximation
        if s1_clean == s2_clean:
            return 1.0

        # Check if one contains the other
        if s1_clean in s2_clean or s2_clean in s1_clean:
            return 0.7

        # Common prefix/suffix
        common_prefix = 0
        for i in range(min(len(s1_clean), len(s2_clean))):
            if s1_clean[i] == s2_clean[i]:
                common_prefix += 1
            else:
                break

        if common_prefix > 3:
            return 0.5 + (common_prefix / max(len(s1_clean), len(s2_clean))) * 0.5

        return 0.0

    def _methods_have_same_signature(
        self,
        old_method: dict,
        new_method: dict,
    ) -> bool:
        """Check if methods have same signature"""
        return old_method.get("decorators") == new_method.get("decorators")

    def _filter_by_modules(
        self,
        files: list[str],
    ) -> list[str]:
        """Filter files by module names"""
        filtered = []
        for file_path in files:
            parts = Path(file_path).parts
            if parts and parts[0] in self.config.modules:
                filtered.append(file_path)
        return filtered

    def _interactive_validation(
        self,
        candidates: list[RenameCandidate],
    ) -> list[RenameCandidate]:
        """Interactive validation of candidates"""
        validated = []

        for candidate in candidates:
            print(f"\n{'='*60}")
            print(f"Type: {candidate.item_type}")
            print(f"Module: {candidate.module}")
            print(f"Model: {candidate.model}")
            print(f"Old name: {candidate.old_name}")
            print(f"New name: {candidate.new_name}")
            print(f"Confidence: {candidate.confidence:.2%}")
            print(f"File: {candidate.file_path}")

            if candidate.confidence >= self.config.detection.auto_approve_threshold:
                print("✓ Auto-approved (high confidence)")
                validated.append(candidate)
            else:
                response = input("Accept this change? (y/n/q): ").lower()
                if response == "y":
                    validated.append(candidate)
                elif response == "q":
                    break

        return validated
