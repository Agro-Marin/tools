"""
Change Grouper - Hierarchical Change Organization
==================================================

Organizes changes hierarchically based on parent-child relationships,
with support for extension modules and rollback tracking.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Tuple

from utils.csv_reader import FieldChange

logger = logging.getLogger(__name__)


@dataclass
class ChangeGroup:
    """Groups related changes with tracking for rollback"""

    primary: FieldChange
    references: List[FieldChange] = field(default_factory=list)
    extension_declarations: List[FieldChange] = field(default_factory=list)

    # Tracking for rollback
    applied_changes: List[Tuple[Path, FieldChange]] = field(default_factory=list)

    def get_changes_for_file(self, file_path: Path) -> List[FieldChange]:
        """
        Get only relevant changes for a specific file.

        Args:
            file_path: Path to the file being processed

        Returns:
            List of changes applicable to this file
        """
        relevant = []

        is_python = file_path.suffix == '.py'
        is_xml = file_path.suffix == '.xml'

        # Include primary change if it should apply to this file
        if is_python and self._is_model_file(file_path, self.primary):
            relevant.append(self.primary)
        elif is_xml and self._should_apply_to_file(self.primary, file_path, is_python, is_xml):
            # For XML files, check if primary declaration should apply
            relevant.append(self.primary)

        # Include extension declarations for the same model
        for ext_decl in self.extension_declarations:
            if is_python and self._is_model_file(file_path, ext_decl):
                relevant.append(ext_decl)
            elif is_xml and self._should_apply_to_file(ext_decl, file_path, is_python, is_xml):
                relevant.append(ext_decl)

        # Include references based on context
        for ref in self.references:
            if self._should_apply_to_file(ref, file_path, is_python, is_xml):
                relevant.append(ref)

        return relevant

    def _is_model_file(self, file_path: Path, change: FieldChange) -> bool:
        """Check if file is a model file for the given change"""
        # Convert model name to file name (e.g., sale.order -> sale_order)
        model_file_name = change.model.replace('.', '_')

        # Check if this file matches the model
        return (
            model_file_name in file_path.stem and
            change.module in str(file_path)
        )

    def _should_apply_to_file(
        self, change: FieldChange, file_path: Path, is_python: bool, is_xml: bool
    ) -> bool:
        """Determine if a change should apply to a file based on context"""
        # For Python files: apply references and calls
        if is_python:
            if change.change_scope in ['reference', 'call', 'super_call']:
                # Check if the module matches or is cross-module
                if change.impact_type == 'cross_module':
                    return True
                return change.module in str(file_path)

        # For XML files: apply view references and primary declarations
        if is_xml:
            # Always apply explicit references
            if change.change_scope == 'reference':
                return change.module in str(file_path)

            # Also apply primary field/method declarations to XML files
            # This allows field/method renames to propagate to views without explicit references
            if (change.change_scope == 'declaration' and
                change.impact_type == 'primary' and
                change.change_type in ['field', 'method']):
                # Verify the XML file is related to the model
                if self._is_xml_related_to_model(file_path, change):
                    return change.module in str(file_path)

        return False

    def _is_xml_related_to_model(self, file_path: Path, change: FieldChange) -> bool:
        """
        Check if XML file is related to the model being changed.

        This helps avoid applying changes to unrelated XML files in the same module.

        Args:
            file_path: Path to the XML file
            change: The change being evaluated

        Returns:
            True if the XML file is likely related to the model
        """
        file_name = file_path.stem.lower()
        module = change.module.lower()

        # Convert model name to potential file patterns
        # e.g., 'product.template' -> 'product_template', 'product'
        model_parts = change.model.lower().split('.')
        model_file_pattern = '_'.join(model_parts)  # e.g., 'product_template'
        model_prefix = model_parts[0]  # e.g., 'product'

        # Check if file name matches model patterns
        # 1. Exact model match: product_template_views.xml matches product.template
        if model_file_pattern in file_name:
            return True

        # 2. Generic module views: product_views.xml matches product.* models
        #    This is common in Odoo where one XML file contains views for multiple models
        if file_name.startswith(model_prefix) and 'views' in file_name:
            return True

        # 3. Model suffix match: partner_view.xml matches res.partner
        #    Common pattern in Odoo where prefix is omitted (res.partner -> partner_view.xml)
        if len(model_parts) > 1:
            model_suffix = model_parts[-1]  # e.g., 'partner' from 'res.partner'
            if file_name.startswith(model_suffix):
                return True

        # 4. Generic module data files: product_data.xml, product_demo.xml
        if file_name.startswith(module) and any(suffix in file_name for suffix in ['data', 'demo']):
            return True

        return False

    def track_applied(self, file_path: Path, change: FieldChange):
        """Register a successfully applied change"""
        self.applied_changes.append((file_path, change))
        change.applied = True

    def get_rollback_files(self) -> List[Path]:
        """Get unique list of files that need rollback"""
        return list(set(path for path, _ in self.applied_changes))


def group_changes_hierarchically(changes: List[FieldChange]) -> Dict[str, ChangeGroup]:
    """
    Group changes by parent-child relationships, considering extension modules.

    Args:
        changes: List of all changes to group

    Returns:
        Dictionary mapping change_id to ChangeGroup
    """
    groups = {}

    # Separate changes by type
    primaries = [c for c in changes if c.is_primary()]
    extension_decls = [c for c in changes if c.is_extension_declaration()]
    other_references = [
        c for c in changes
        if not c.is_primary() and not c.is_extension_declaration()
    ]

    # Create groups for each primary change
    for primary in primaries:
        # Find extension declarations for this primary
        primary_extensions = [
            ext for ext in extension_decls
            if ext.parent_change_id == primary.change_id
        ]

        # Find all references for this primary
        primary_refs = [
            ref for ref in other_references
            if ref.parent_change_id == primary.change_id
        ]

        groups[primary.change_id] = ChangeGroup(
            primary=primary,
            references=primary_refs,
            extension_declarations=primary_extensions
        )

    # Handle orphan references (changes without a primary parent)
    orphan_refs = [
        ref for ref in other_references
        if ref.parent_change_id not in groups
    ]

    for orphan in orphan_refs:
        groups[orphan.change_id] = ChangeGroup(
            primary=orphan,
            references=[],
            extension_declarations=[]
        )

    logger.info(
        f"Created {len(groups)} change groups from {len(changes)} changes "
        f"({len(primaries)} primary, {len(extension_decls)} extensions, "
        f"{len(other_references)} references)"
    )

    return groups
