"""
XML Processor for Field/Method Renaming
=======================================

Handles renaming of field and method references in XML files using
ElementTree parsing and regex patterns for comprehensive coverage.
"""

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from utils.csv_reader import FieldChange

from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class XMLPatterns:
    """Container for XML search and replace patterns"""

    def __init__(self):
        self.field_patterns = self._build_field_patterns()
        self.method_patterns = self._build_method_patterns()

    def _build_field_patterns(self) -> list[tuple[str, str]]:
        """
        Build regex patterns for field references.

        Returns:
            List of tuples (pattern_template, replacement_template)
        """
        return [
            # Basic field references - double quotes
            (r'<field\s+name="({old_name})"', r'<field name="{new_name}"'),
            # Basic field references - single quotes
            (r"<field\s+name='({old_name})'", r"<field name='{new_name}'"),
            # QWeb template field references - using [\s\S] to match across lines
            (r't-field="([\s\S]*?\.){old_name}"', r't-field="\g<1>{new_name}"'),
            (r"t-field='([\s\S]*?\.){old_name}'", r"t-field='\g<1>{new_name}'"),
            (r't-esc="([\s\S]*?\.){old_name}"', r't-esc="\g<1>{new_name}"'),
            (r"t-esc='([\s\S]*?\.){old_name}'", r"t-esc='\g<1>{new_name}'"),
            (r't-raw="([\s\S]*?\.){old_name}"', r't-raw="\g<1>{new_name}"'),
            (r"t-raw='([\s\S]*?\.){old_name}'", r"t-raw='\g<1>{new_name}'"),
            # Field references in expressions - using [\s\S] to match across lines
            (r't-if="([\s\S]*?){old_name}([\s\S]*?)"', r't-if="\g<1>{new_name}\g<2>"'),
            (r"t-if='([\s\S]*?){old_name}([\s\S]*?)'", r"t-if='\g<1>{new_name}\g<2>'"),
            (
                r't-elif="([\s\S]*?){old_name}([\s\S]*?)"',
                r't-elif="\g<1>{new_name}\g<2>"',
            ),
            (
                r"t-elif='([\s\S]*?){old_name}([\s\S]*?)'",
                r"t-elif='\g<1>{new_name}\g<2>'",
            ),
            (
                r't-unless="([\s\S]*?){old_name}([\s\S]*?)"',
                r't-unless="\g<1>{new_name}\g<2>"',
            ),
            (
                r"t-unless='([\s\S]*?){old_name}([\s\S]*?)'",
                r"t-unless='\g<1>{new_name}\g<2>'",
            ),
            # Attribute conditions - using [\s\S] to match across lines
            (
                r'invisible="([\s\S]*?){old_name}([\s\S]*?)"',
                r'invisible="\g<1>{new_name}\g<2>"',
            ),
            (
                r"invisible='([\s\S]*?){old_name}([\s\S]*?)'",
                r"invisible='\g<1>{new_name}\g<2>'",
            ),
            (
                r'readonly="([\s\S]*?){old_name}([\s\S]*?)"',
                r'readonly="\g<1>{new_name}\g<2>"',
            ),
            (
                r"readonly='([\s\S]*?){old_name}([\s\S]*?)'",
                r"readonly='\g<1>{new_name}\g<2>'",
            ),
            (
                r'required="([\s\S]*?){old_name}([\s\S]*?)"',
                r'required="\g<1>{new_name}\g<2>"',
            ),
            (
                r"required='([\s\S]*?){old_name}([\s\S]*?)'",
                r"required='\g<1>{new_name}\g<2>'",
            ),
            # Domain expressions - using [\s\S] to match across lines (like filter_domain)
            (
                r'domain="([\s\S]*?){old_name}([\s\S]*?)"',
                r'domain="\g<1>{new_name}\g<2>"',
            ),
            (
                r"domain='([\s\S]*?){old_name}([\s\S]*?)'",
                r"domain='\g<1>{new_name}\g<2>'",
            ),
            (
                r'filter_domain="([\s\S]*?){old_name}([\s\S]*?)"',
                r'filter_domain="\g<1>{new_name}\g<2>"',
            ),
            (
                r"filter_domain='([\s\S]*?){old_name}([\s\S]*?)'",
                r"filter_domain='\g<1>{new_name}\g<2>'",
            ),
            (
                r'context="([\s\S]*?){old_name}([\s\S]*?)"',
                r'context="\g<1>{new_name}\g<2>"',
            ),
            (
                r"context='([\s\S]*?){old_name}([\s\S]*?)'",
                r"context='\g<1>{new_name}\g<2>'",
            ),
            # Data field references
            (
                r'<field\s+name="field_id"[^>]*ref="field_([^_]*)_{old_name}"',
                r'<field name="field_id" ref="field_\g<1>_{new_name}"',
            ),
            # Security references
            (
                r"field_id.*field_([^_]*)_{old_name}",
                r"field_id.*field_\g<1>_{new_name}",
            ),
        ]

    def _build_method_patterns(self) -> list[tuple[str, str]]:
        """
        Build regex patterns for method references.

        Returns:
            List of tuples (pattern_template, replacement_template)
        """
        return [
            # Button method references - double quotes
            (r'<button\s+name="({old_name})"', r'<button name="{new_name}"'),
            # Button method references - single quotes
            (r"<button\s+name='({old_name})'", r"<button name='{new_name}'"),
            # Action references - double quotes
            (r'action="({old_name})"', r'action="{new_name}"'),
            # Action references - single quotes
            (r"action='({old_name})'", r"action='{new_name}'"),
            # QWeb method calls - double quotes
            (r't-call="({old_name})"', r't-call="{new_name}"'),
            (r't-call-assets="({old_name})"', r't-call-assets="{new_name}"'),
            # QWeb method calls - single quotes
            (r"t-call='({old_name})'", r"t-call='{new_name}'"),
            (r"t-call-assets='({old_name})'", r"t-call-assets='{new_name}'"),
            # JavaScript method references
            (
                r'onclick="([^"]*){old_name}(\([^"]*)"',
                r'onclick="\g<1>{new_name}\g<2>"',
            ),
            (
                r"onclick='([^']*){old_name}(\([^']*)'",
                r"onclick='\g<1>{new_name}\g<2>'",
            ),
            (
                r'onchange="([^"]*){old_name}(\([^"]*)"',
                r'onchange="\g<1>{new_name}\g<2>"',
            ),
            (
                r"onchange='([^']*){old_name}(\([^']*)'",
                r"onchange='\g<1>{new_name}\g<2>'",
            ),
            # Compute method references in data files - double quotes
            (r'compute="({old_name})"', r'compute="{new_name}"'),
            (r'inverse="({old_name})"', r'inverse="{new_name}"'),
            (r'search="({old_name})"', r'search="{new_name}"'),
            # Compute method references in data files - single quotes
            (r"compute='({old_name})'", r"compute='{new_name}'"),
            (r"inverse='({old_name})'", r"inverse='{new_name}'"),
            (r"search='({old_name})'", r"search='{new_name}'"),
            # Server action references
            (
                r'<field\s+name="code"[^>]*>([^<]*){old_name}([^<]*)</field>',
                r'<field name="code">\g<1>{new_name}\g<2></field>',
            ),
            (
                r"<field\s+name='code'[^>]*>([^<]*){old_name}([^<]*)</field>",
                r"<field name='code'>\g<1>{new_name}\g<2></field>",
            ),
        ]


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
        self.patterns = XMLPatterns()

    def get_supported_extensions(self) -> list[str]:
        """Get supported file extensions"""
        return [".xml"]

    def _apply_changes(
        self, file_path: Path, content: str, changes: list[FieldChange]
    ) -> tuple[str, list[str]]:
        """
        Apply field and method changes to XML file content.

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

        # Apply field changes
        modified_content, field_applied = self._apply_field_changes(
            modified_content, field_changes
        )
        applied_changes.extend(field_applied)

        # Apply method changes
        modified_content, method_applied = self._apply_method_changes(
            modified_content, method_changes
        )
        applied_changes.extend(method_applied)

        # Apply ElementTree-based changes for more complex patterns
        try:
            modified_content, et_applied = self._apply_elementtree_changes(
                modified_content, field_changes, method_changes
            )
            applied_changes.extend(et_applied)
        except ET.ParseError as e:
            logger.warning(f"Could not parse XML with ElementTree for {file_path}: {e}")
            # Continue with regex-only changes

        return modified_content, applied_changes

    def _apply_field_changes(
        self, content: str, field_changes: dict[str, str]
    ) -> tuple[str, list[str]]:
        """
        Apply field changes using regex patterns.

        Args:
            content: XML content to modify
            field_changes: Dict mapping old field names to new names

        Returns:
            Tuple of (modified_content, applied_changes)
        """
        applied_changes = []
        modified_content = content

        for old_name, new_name in field_changes.items():
            for pattern_template, replacement_template in self.patterns.field_patterns:
                # Build specific pattern for this field
                pattern = pattern_template.format(old_name=re.escape(old_name))
                replacement = replacement_template.format(new_name=new_name)

                # Apply replacement with DOTALL flag to handle multiline attributes
                new_content, count = re.subn(
                    pattern,
                    replacement,
                    modified_content,
                    flags=re.IGNORECASE | re.DOTALL,
                )

                if count > 0:
                    modified_content = new_content
                    applied_changes.append(
                        f"Field reference: {old_name} → {new_name} ({count} occurrences)"
                    )
                    logger.debug(
                        f"Applied field pattern {pattern}: {count} replacements"
                    )

        return modified_content, applied_changes

    def _apply_method_changes(
        self, content: str, method_changes: dict[str, str]
    ) -> tuple[str, list[str]]:
        """
        Apply method changes using regex patterns.

        Args:
            content: XML content to modify
            method_changes: Dict mapping old method names to new names

        Returns:
            Tuple of (modified_content, applied_changes)
        """
        applied_changes = []
        modified_content = content

        for old_name, new_name in method_changes.items():
            for pattern_template, replacement_template in self.patterns.method_patterns:
                # Build specific pattern for this method
                pattern = pattern_template.format(old_name=re.escape(old_name))
                replacement = replacement_template.format(new_name=new_name)

                # Apply replacement with DOTALL flag to handle multiline attributes
                new_content, count = re.subn(
                    pattern,
                    replacement,
                    modified_content,
                    flags=re.IGNORECASE | re.DOTALL,
                )

                if count > 0:
                    modified_content = new_content
                    applied_changes.append(
                        f"Method reference: {old_name} → {new_name} ({count} occurrences)"
                    )
                    logger.debug(
                        f"Applied method pattern {pattern}: {count} replacements"
                    )

        return modified_content, applied_changes

    def _apply_elementtree_changes(
        self,
        content: str,
        field_changes: dict[str, str],
        method_changes: dict[str, str],
    ) -> tuple[str, list[str]]:
        """
        Apply changes using ElementTree for more precise XML manipulation.

        Args:
            content: XML content to modify
            field_changes: Dict mapping old field names to new names
            method_changes: Dict mapping old method names to new names

        Returns:
            Tuple of (modified_content, applied_changes)
        """
        applied_changes = []

        try:
            # Parse XML
            root = ET.fromstring(content)
            changes_made = False

            # Process field elements
            for field_elem in root.findall(".//field"):
                name_attr = field_elem.get("name")
                if name_attr and name_attr in field_changes:
                    field_elem.set("name", field_changes[name_attr])
                    applied_changes.append(
                        f"ElementTree field: {name_attr} → {field_changes[name_attr]}"
                    )
                    changes_made = True

            # Process button elements
            for button_elem in root.findall(".//button"):
                name_attr = button_elem.get("name")
                if name_attr and name_attr in method_changes:
                    button_elem.set("name", method_changes[name_attr])
                    applied_changes.append(
                        f"ElementTree button: {name_attr} → {method_changes[name_attr]}"
                    )
                    changes_made = True

                # Check action attribute
                action_attr = button_elem.get("action")
                if action_attr and action_attr in method_changes:
                    button_elem.set("action", method_changes[action_attr])
                    applied_changes.append(
                        f"ElementTree action: {action_attr} → {method_changes[action_attr]}"
                    )
                    changes_made = True

            # Process record elements (for data files)
            for record_elem in root.findall(".//record"):
                for field_elem in record_elem.findall(".//field"):
                    name_attr = field_elem.get("name")

                    # Check field references in data
                    if name_attr in ["field_id", "field"]:
                        ref_attr = field_elem.get("ref")
                        if ref_attr:
                            # Handle field references like field_model_fieldname
                            for old_name, new_name in field_changes.items():
                                if ref_attr.endswith(f"_{old_name}"):
                                    new_ref = ref_attr.replace(
                                        f"_{old_name}", f"_{new_name}"
                                    )
                                    field_elem.set("ref", new_ref)
                                    applied_changes.append(
                                        f"ElementTree ref: {ref_attr} → {new_ref}"
                                    )
                                    changes_made = True

                        # Check field content
                        if field_elem.text:
                            for old_name, new_name in field_changes.items():
                                if old_name in field_elem.text:
                                    field_elem.text = field_elem.text.replace(
                                        old_name, new_name
                                    )
                                    applied_changes.append(
                                        f"ElementTree field content: {old_name} → {new_name}"
                                    )
                                    changes_made = True

            if changes_made:
                # Convert back to string
                modified_content = ET.tostring(root, encoding="unicode")
                # Clean up the XML formatting
                modified_content = self._format_xml_output(modified_content)
                return modified_content, applied_changes
            else:
                return content, applied_changes

        except Exception as e:
            logger.debug(f"ElementTree processing failed: {e}")
            return content, applied_changes

    def _format_xml_output(self, xml_content: str) -> str:
        """
        Format XML output to maintain readability while preserving compact elements.

        Args:
            xml_content: Raw XML content from ElementTree

        Returns:
            Formatted XML content
        """
        # Add XML declaration if missing
        if not xml_content.startswith("<?xml"):
            xml_content = '<?xml version="1.0" encoding="utf-8"?>\n' + xml_content

        # More selective formatting - only break lines for major elements
        # Avoid breaking inline elements like <field><attribute></field>
        # Only break for elements that typically should be on separate lines
        major_elements = [
            "record",
            "data",
            "odoo",
            "template",
            "xpath",
            "form",
            "tree",
            "kanban",
            "graph",
            "pivot",
        ]

        for element in major_elements:
            # Break lines only around major container elements
            pattern = f"><{element}"
            replacement = f">\n<{element}"
            xml_content = re.sub(pattern, replacement, xml_content)

            pattern = f"</{element}><"
            replacement = f"</{element}>\n<"
            xml_content = re.sub(pattern, replacement, xml_content)

        return xml_content

    def _filter_relevant_changes(
        self, file_path: Path, changes: list[FieldChange]
    ) -> list[FieldChange]:
        """
        Filter changes relevant to this XML file.

        Args:
            file_path: Path to the XML file
            changes: All changes to consider

        Returns:
            List of relevant changes
        """
        try:
            content = self._read_file_content(file_path)
            models_in_file = self._extract_models_from_xml_file(content)

            # Filter changes for models referenced in this file
            relevant_changes = []
            for change in changes:
                model_key = f"{change.module}.{change.model}"
                if (
                    model_key in models_in_file
                    or change.model in models_in_file
                    or self._content_contains_reference(content, change.old_name)
                ):
                    relevant_changes.append(change)
                    logger.debug(f"Relevant change for {file_path}: {change}")

            return relevant_changes

        except Exception as e:
            logger.warning(f"Could not filter changes for {file_path}: {e}")
            # If we can't determine, return all changes
            return changes

    def _extract_models_from_xml_file(self, content: str) -> set[str]:
        """
        Extract model names referenced in an XML file.

        Args:
            content: XML file content

        Returns:
            set of model names found in the file
        """
        models = set()

        try:
            # Use regex to find model references
            model_patterns = [
                r'model=["\']([^"\']+)["\']',  # model="model.name"
                r'res_model=["\']([^"\']+)["\']',  # res_model="model.name"
                r'<field\s+name=["\']model["\'][^>]*>([^<]+)</field>',  # <field name="model">model.name</field>
            ]

            for pattern in model_patterns:
                matches = re.findall(pattern, content)
                models.update(matches)

            # Try ElementTree parsing for more precise extraction
            try:
                root = ET.fromstring(content)

                # Look for model attributes
                for elem in root.iter():
                    model_attr = elem.get("model")
                    if model_attr:
                        models.add(model_attr)

                    res_model_attr = elem.get("res_model")
                    if res_model_attr:
                        models.add(res_model_attr)

                # Look for field elements with model content
                for field_elem in root.findall('.//field[@name="model"]'):
                    if field_elem.text:
                        models.add(field_elem.text.strip())

            except ET.ParseError:
                logger.debug(
                    "Could not parse XML with ElementTree for model extraction"
                )

        except Exception as e:
            logger.debug(f"Error extracting models from XML content: {e}")

        return models

    def _content_contains_reference(self, content: str, reference_name: str) -> bool:
        """
        Check if content contains a reference to the given name.

        Args:
            content: File content to search
            reference_name: Name to search for

        Returns:
            True if reference is found
        """
        # Simple check for reference existence
        return reference_name in content

    def get_file_analysis(self, file_path: Path) -> dict[str, any]:
        """
        Analyze an XML file to extract information about field and method references.

        Args:
            file_path: Path to the XML file

        Returns:
            Dictionary with analysis results
        """
        try:
            content = self._read_file_content(file_path)

            # Extract models
            models = list(self._extract_models_from_xml_file(content))

            # Extract field references
            field_refs = set()
            field_patterns = [
                r'<field\s+name=["\']([^"\']+)["\']',
                r't-field=["\'][^"\']*\.([^"\'\.]+)["\']',
                r't-esc=["\'][^"\']*\.([^"\'\.]+)["\']',
            ]

            for pattern in field_patterns:
                matches = re.findall(pattern, content)
                field_refs.update(matches)

            # Extract method references
            method_refs = set()
            method_patterns = [
                r'<button\s+name=["\']([^"\']+)["\']',
                r'action=["\']([^"\']+)["\']',
                r't-call=["\']([^"\']+)["\']',
            ]

            for pattern in method_patterns:
                matches = re.findall(pattern, content)
                method_refs.update(matches)

            # Determine file type based on directory/name
            file_type = self._determine_xml_file_type(file_path)

            return {
                "file_type": file_type,
                "models": models,
                "field_references": list(field_refs),
                "method_references": list(method_refs),
                "total_lines": len(content.splitlines()),
                "file_size": len(content),
            }

        except Exception as e:
            logger.error(f"Error analyzing XML file {file_path}: {e}")
            return {
                "file_type": "unknown",
                "models": [],
                "field_references": [],
                "method_references": [],
                "error": str(e),
            }

    def _determine_xml_file_type(self, file_path: Path) -> str:
        """
        Determine the type of XML file based on its path and name.

        Args:
            file_path: Path to the XML file

        Returns:
            Type of XML file (views, data, demo, templates, reports, security)
        """
        file_name = file_path.name.lower()
        parent_dir = file_path.parent.name.lower()

        # Determine by directory
        if parent_dir == "views":
            return "views"
        elif parent_dir == "data":
            return "data"
        elif parent_dir == "demo":
            return "demo"
        elif parent_dir == "templates":
            return "templates"
        elif parent_dir == "reports":
            return "reports"
        elif parent_dir == "security":
            return "security"

        # Determine by file name
        if "view" in file_name:
            return "views"
        elif "data" in file_name:
            return "data"
        elif "demo" in file_name:
            return "demo"
        elif "template" in file_name:
            return "templates"
        elif "report" in file_name:
            return "reports"
        elif "security" in file_name:
            return "security"

        return "unknown"

    def validate_xml_changes(
        self, original_content: str, modified_content: str
    ) -> bool:
        """
        Validate that XML changes were applied correctly.

        Args:
            original_content: Original XML content
            modified_content: Modified XML content

        Returns:
            True if changes appear correct
        """
        try:
            # Both should be valid XML
            ET.fromstring(original_content)
            ET.fromstring(modified_content)

            # Basic structure should be preserved
            original_lines = len(original_content.splitlines())
            modified_lines = len(modified_content.splitlines())

            # Allow for reasonable variation in line count
            if abs(original_lines - modified_lines) > original_lines * 0.1:
                logger.warning("Significant line count change in XML file")
                return False

            return True

        except ET.ParseError as e:
            logger.error(f"XML validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating XML changes: {e}")
            return False
