"""
XML Processor for Field/Method Renaming
=======================================

Handles renaming of field and method references in XML files using
safe text replacement that preserves original formatting.
"""

import logging
import re
from pathlib import Path

from utils.csv_reader import FieldChange

from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class XMLProcessor(BaseProcessor):
    """Processor for XML files (views, data, demo, templates, reports, security)"""

    def __init__(self, create_backups: bool = True, validate_syntax: bool = True):
        """
        Initialize XML processor.

        Args:
            create_backups: Whether to create backups before modifying files
            validate_syntax: Whether to validate XML syntax after modifications
        """
        super().__init__(create_backups, validate_syntax)

    def get_supported_extensions(self) -> list[str]:
        """Get supported file extensions"""
        return [".xml"]

    def _apply_single_change(
        self, file_path: Path, content: str, change: FieldChange
    ) -> tuple[str, list[str]]:
        """
        Apply a single change considering its context and scope.

        Args:
            file_path: Path to the file being processed
            content: Current file content
            change: Single change to apply

        Returns:
            Tuple of (modified_content, list_of_applied_changes_descriptions)
        """
        # Delegate to _apply_changes with a single-item list
        # In the future, this can be extended with context-aware logic
        return self._apply_changes(file_path, content, [change])

    def _apply_changes(
        self, file_path: Path, content: str, changes: list[FieldChange]
    ) -> tuple[str, list[str]]:
        """
        Apply field and method changes to XML file content using simple text replacement.
        This approach preserves the original formatting, indentation, and structure.

        Args:
            file_path: Path to the XML file
            content: Original file content
            changes: List of changes to apply

        Returns:
            Tuple of (modified_content, list_of_applied_changes)
        """
        logger.debug(f"Applying {len(changes)} changes to XML file: {file_path}")

        # Separate field and method changes
        field_changes = {
            change.old_name: change.new_name for change in changes if change.is_field
        }
        method_changes = {
            change.old_name: change.new_name for change in changes if change.is_method
        }

        logger.debug(f"Field changes: {field_changes}")
        logger.debug(f"Method changes: {method_changes}")

        applied_changes = []
        modified_content = content

        # Apply simple, safe text replacements that preserve formatting
        modified_content, all_applied = self._apply_safe_text_replacements(
            modified_content, field_changes, method_changes
        )
        applied_changes.extend(all_applied)

        return modified_content, applied_changes

    def _apply_safe_text_replacements(
        self,
        content: str,
        field_changes: dict[str, str],
        method_changes: dict[str, str],
    ) -> tuple[str, list[str]]:
        """
        Apply field and method changes using safe, minimal text replacements.
        This method preserves 100% of the original formatting, indentation, and structure.

        Args:
            content: XML content to modify
            field_changes: Dict mapping old field names to new names
            method_changes: Dict mapping old method names to new names

        Returns:
            Tuple of (modified_content, applied_changes)
        """
        applied_changes = []
        modified_content = content

        # Apply field changes with safe patterns
        for old_name, new_name in field_changes.items():
            total_replacements = 0

            # Pattern 1: Field name attributes
            field_name_patterns = [
                (f'name="{old_name}"', f'name="{new_name}"'),
                (f"name='{old_name}'", f"name='{new_name}'"),
            ]

            for old_pattern, new_pattern in field_name_patterns:
                if old_pattern in modified_content:
                    count = modified_content.count(old_pattern)
                    modified_content = modified_content.replace(old_pattern, new_pattern)
                    total_replacements += count
                    if count > 0:
                        logger.debug(f"Applied field name replacement: {old_pattern} → {new_pattern} ({count}x)")

            # Pattern 2: Field references in attribute values (invisible, readonly, context, etc.)
            # Use word boundaries to avoid partial replacements
            # This catches: invisible="product_count > 1", context="{'field': product_count}"

            # Build regex pattern with word boundaries
            # Matches field_name as a complete word (not part of another word)
            field_pattern = re.compile(r'\b' + re.escape(old_name) + r'\b')

            # Count matches and replace
            matches = field_pattern.findall(modified_content)
            if matches:
                count = len(matches)
                modified_content = field_pattern.sub(new_name, modified_content)
                total_replacements += count
                logger.debug(
                    f"Applied field reference replacement in attributes: {old_name} → {new_name} ({count}x)"
                )

            if total_replacements > 0:
                applied_changes.append(
                    f"Field: {old_name} → {new_name} ({total_replacements} occurrences)"
                )

        # Apply method changes with safe patterns
        for old_name, new_name in method_changes.items():
            total_replacements = 0

            # Pattern 1: Method name and action attributes
            method_attribute_patterns = [
                (f'name="{old_name}"', f'name="{new_name}"'),
                (f"name='{old_name}'", f"name='{new_name}'"),
                (f'action="{old_name}"', f'action="{new_name}"'),
                (f"action='{old_name}'", f"action='{new_name}'"),
            ]

            for old_pattern, new_pattern in method_attribute_patterns:
                if old_pattern in modified_content:
                    count = modified_content.count(old_pattern)
                    modified_content = modified_content.replace(old_pattern, new_pattern)
                    total_replacements += count
                    if count > 0:
                        logger.debug(f"Applied method attribute replacement: {old_pattern} → {new_pattern} ({count}x)")

            # Pattern 2: Method references in attribute values (similar to fields)
            # This catches: domain="[('id', 'in', method_name())]", etc.
            method_pattern = re.compile(r'\b' + re.escape(old_name) + r'\b')

            # Count matches and replace
            matches = method_pattern.findall(modified_content)
            if matches:
                count = len(matches)
                modified_content = method_pattern.sub(new_name, modified_content)
                total_replacements += count
                logger.debug(
                    f"Applied method reference replacement in attributes: {old_name} → {new_name} ({count}x)"
                )

            if total_replacements > 0:
                applied_changes.append(
                    f"Method: {old_name} → {new_name} ({total_replacements} occurrences)"
                )

        return modified_content, applied_changes

    def _filter_relevant_changes(
        self, file_path: Path, changes: list[FieldChange]
    ) -> list[FieldChange]:
        """
        Filter changes relevant to this XML file.
        Simplified version that checks if the old name exists in the content.

        Args:
            file_path: Path to the XML file
            changes: All changes to consider

        Returns:
            List of relevant changes
        """
        try:
            content = self._read_file_content(file_path)

            # Simple filtering: check if old name exists in file content
            relevant_changes = []
            for change in changes:
                if change.old_name in content:
                    relevant_changes.append(change)
                    logger.debug(
                        f"Relevant change for {file_path}: {change.old_name} → {change.new_name}"
                    )

            return relevant_changes

        except Exception as e:
            logger.warning(f"Could not filter changes for {file_path}: {e}")
            # If we can't determine, return all changes
            return changes
