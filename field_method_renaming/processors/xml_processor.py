"""
XML Processor for Field/Method Renaming
=======================================

Handles renaming of field and method references in XML files using
safe text replacement that preserves original formatting.
"""

import logging
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
        self, content: str, field_changes: dict[str, str], method_changes: dict[str, str]
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
            # Only apply the most common and safe patterns
            safe_field_patterns = [
                # <field name="old_name" ... (double quotes)
                (f'name="{old_name}"', f'name="{new_name}"'),
                # <field name='old_name' ... (single quotes)
                (f"name='{old_name}'", f"name='{new_name}'"),
            ]
            
            for old_pattern, new_pattern in safe_field_patterns:
                if old_pattern in modified_content:
                    count = modified_content.count(old_pattern)
                    modified_content = modified_content.replace(old_pattern, new_pattern)
                    if count > 0:
                        applied_changes.append(
                            f"Field: {old_name} → {new_name} ({count} occurrences)"
                        )
                        logger.debug(f"Applied safe field replacement: {old_pattern} → {new_pattern}")

        # Apply method changes with safe patterns  
        for old_name, new_name in method_changes.items():
            # Only apply the most common and safe patterns
            safe_method_patterns = [
                # <button name="old_method" ... (double quotes)
                (f'name="{old_name}"', f'name="{new_name}"'),
                # <button name='old_method' ... (single quotes)
                (f"name='{old_name}'", f"name='{new_name}'"),
                # action="old_method" ... (double quotes)
                (f'action="{old_name}"', f'action="{new_name}"'),
                # action='old_method' ... (single quotes)
                (f"action='{old_name}'", f"action='{new_name}'"),
            ]
            
            for old_pattern, new_pattern in safe_method_patterns:
                if old_pattern in modified_content:
                    count = modified_content.count(old_pattern)
                    modified_content = modified_content.replace(old_pattern, new_pattern)
                    if count > 0:
                        applied_changes.append(
                            f"Method: {old_name} → {new_name} ({count} occurrences)"
                        )
                        logger.debug(f"Applied safe method replacement: {old_pattern} → {new_pattern}")

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
                    logger.debug(f"Relevant change for {file_path}: {change.old_name} → {change.new_name}")

            return relevant_changes

        except Exception as e:
            logger.warning(f"Could not filter changes for {file_path}: {e}")
            # If we can't determine, return all changes
            return changes

