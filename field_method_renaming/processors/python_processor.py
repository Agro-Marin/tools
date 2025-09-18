"""
Python Processor for Field/Method Renaming
==========================================

Handles renaming of fields and methods in Python files using AST parsing
for precise and safe modifications.
"""
import ast
import re
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
import logging

from .base_processor import BaseProcessor, ProcessResult
from utils.csv_reader import FieldChange

logger = logging.getLogger(__name__)


class ASTFieldMethodTransformer(ast.NodeTransformer):
    """AST transformer for renaming fields and methods"""
    
    def __init__(self, field_changes: Dict[str, str], method_changes: Dict[str, str]):
        """
        Initialize transformer.
        
        Args:
            field_changes: Dict mapping old field names to new names
            method_changes: Dict mapping old method names to new names
        """
        self.field_changes = field_changes
        self.method_changes = method_changes
        self.changes_applied = []
        
    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        """Visit assignment nodes to rename field definitions"""
        # Check if this is a field assignment
        if (len(node.targets) == 1 and 
            isinstance(node.targets[0], ast.Name) and
            self._is_fields_call(node.value)):
            
            field_name = node.targets[0].id
            if field_name in self.field_changes:
                new_name = self.field_changes[field_name]
                node.targets[0].id = new_name
                self.changes_applied.append(f"Field definition: {field_name} → {new_name}")
                logger.debug(f"Renamed field definition: {field_name} → {new_name}")
        
        return self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Visit function definitions to rename methods"""
        if node.name in self.method_changes:
            new_name = self.method_changes[node.name]
            node.name = new_name
            self.changes_applied.append(f"Method definition: {node.name} → {new_name}")
            logger.debug(f"Renamed method definition: {node.name} → {new_name}")
        
        return self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Visit async function definitions to rename methods"""
        if node.name in self.method_changes:
            new_name = self.method_changes[node.name]
            node.name = new_name
            self.changes_applied.append(f"Async method definition: {node.name} → {new_name}")
            logger.debug(f"Renamed async method definition: {node.name} → {new_name}")
        
        return self.generic_visit(node)
    
    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        """Visit string constants to rename field/method references"""
        if isinstance(node.value, str):
            original_value = node.value
            new_value = self._replace_references_in_string(original_value)
            
            if new_value != original_value:
                node.value = new_value
                self.changes_applied.append(f"String reference: '{original_value}' → '{new_value}'")
                logger.debug(f"Updated string reference: '{original_value}' → '{new_value}'")
        
        return node
    
    def visit_Str(self, node: ast.Str) -> ast.Str:
        """Visit string nodes (for Python < 3.8 compatibility)"""
        original_value = node.s
        new_value = self._replace_references_in_string(original_value)
        
        if new_value != original_value:
            node.s = new_value
            self.changes_applied.append(f"String reference: '{original_value}' → '{new_value}'")
            logger.debug(f"Updated string reference: '{original_value}' → '{new_value}'")
        
        return node
    
    def _is_fields_call(self, node) -> bool:
        """Check if node is a fields.FieldType() call"""
        return (isinstance(node, ast.Call) and 
                isinstance(node.func, ast.Attribute) and
                isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'fields')
    
    def _replace_references_in_string(self, text: str) -> str:
        """Replace field/method references in string content"""
        # Replace field references
        for old_name, new_name in self.field_changes.items():
            # Exact match patterns
            patterns = [
                f"'{old_name}'",  # Single quotes
                f'"{old_name}"',  # Double quotes
                f" {old_name} ",  # Space-separated
                f",{old_name},",  # Comma-separated
                f"({old_name})",  # Parentheses
                f"[{old_name}]",  # Brackets
            ]
            
            for pattern in patterns:
                replacement = pattern.replace(old_name, new_name)
                text = text.replace(pattern, replacement)
        
        # Replace method references
        for old_name, new_name in self.method_changes.items():
            # Method call patterns
            patterns = [
                f"'{old_name}'",  # Single quotes
                f'"{old_name}"',  # Double quotes
                f".{old_name}(",  # Method call
                f" {old_name}(",  # Function call
            ]
            
            for pattern in patterns:
                replacement = pattern.replace(old_name, new_name)
                text = text.replace(pattern, replacement)
        
        return text


class PythonProcessor(BaseProcessor):
    """Processor for Python files (.py)"""
    
    def __init__(self, create_backups: bool = True, validate_syntax: bool = True):
        """
        Initialize Python processor.
        
        Args:
            create_backups: Whether to create backups before modifying files
            validate_syntax: Whether to validate Python syntax after modifications
        """
        super().__init__(create_backups, validate_syntax)
    
    def get_supported_extensions(self) -> List[str]:
        """Get supported file extensions"""
        return ['.py']
    
    def _apply_changes(self, file_path: Path, content: str, changes: List[FieldChange]) -> Tuple[str, List[str]]:
        """
        Apply field and method changes to Python file content.
        
        Args:
            file_path: Path to the Python file
            content: Original file content
            changes: List of changes to apply
            
        Returns:
            Tuple of (modified_content, list_of_applied_changes)
        """
        logger.debug(f"Applying {len(changes)} changes to Python file: {file_path}")
        
        # Separate field and method changes
        field_changes = {change.old_name: change.new_name 
                        for change in changes if change.is_field}
        method_changes = {change.old_name: change.new_name 
                         for change in changes if change.is_method}
        
        logger.debug(f"Field changes: {field_changes}")
        logger.debug(f"Method changes: {method_changes}")
        
        try:
            # Use regex-based approach to preserve formatting
            modified_content, changes_applied = self._apply_regex_only_transformations(
                content, field_changes, method_changes
            )
            
            return modified_content, changes_applied
            
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing Python file {file_path}: {e}")
            raise
    
    def _apply_regex_transformations(self, content: str, field_changes: Dict[str, str], 
                                   method_changes: Dict[str, str]) -> str:
        """
        Apply additional regex-based transformations for patterns AST might miss.
        
        Args:
            content: Python content to transform
            field_changes: Dict of field name changes
            method_changes: Dict of method name changes
            
        Returns:
            Modified content
        """
        applied_changes = []
        
        # Patterns for @api.depends decorators
        for old_name, new_name in field_changes.items():
            # @api.depends('field_name')
            pattern = rf"@api\.depends\(([^)]*['\"]){re.escape(old_name)}(['\"][^)]*)\)"
            replacement = rf"@api.depends(\g<1>{new_name}\g<2>)"
            
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                applied_changes.append(f"@api.depends decorator: {old_name} → {new_name}")
        
        # Patterns for compute field references
        for old_name, new_name in field_changes.items():
            # compute='_compute_field_name'
            compute_pattern = rf"compute\s*=\s*['\"]_compute_{re.escape(old_name)}['\"]"
            compute_replacement = f"compute='_compute_{new_name}'"
            
            if re.search(compute_pattern, content):
                content = re.sub(compute_pattern, compute_replacement, content)
                applied_changes.append(f"Compute method reference: _compute_{old_name} → _compute_{new_name}")
        
        # Patterns for inverse and search method references
        for old_name, new_name in field_changes.items():
            # inverse='_inverse_field_name'
            inverse_pattern = rf"inverse\s*=\s*['\"]_inverse_{re.escape(old_name)}['\"]"
            inverse_replacement = f"inverse='_inverse_{new_name}'"
            
            if re.search(inverse_pattern, content):
                content = re.sub(inverse_pattern, inverse_replacement, content)
                applied_changes.append(f"Inverse method reference: _inverse_{old_name} → _inverse_{new_name}")
            
            # search='_search_field_name'
            search_pattern = rf"search\s*=\s*['\"]_search_{re.escape(old_name)}['\"]"
            search_replacement = f"search='_search_{new_name}'"
            
            if re.search(search_pattern, content):
                content = re.sub(search_pattern, search_replacement, content)
                applied_changes.append(f"Search method reference: _search_{old_name} → _search_{new_name}")
        
        # Patterns for domain and context field references
        for old_name, new_name in field_changes.items():
            # Domain references: [('field_name', '=', value)]
            domain_pattern = rf"\(\s*['\"]({re.escape(old_name)})['\"]"
            
            def domain_replacement(match):
                return match.group(0).replace(old_name, new_name)
            
            new_content = re.sub(domain_pattern, domain_replacement, content)
            if new_content != content:
                content = new_content
                applied_changes.append(f"Domain reference: {old_name} → {new_name}")
        
        # Log applied regex changes
        for change in applied_changes:
            logger.debug(f"Regex transformation: {change}")
        
        return content
    
    def _apply_regex_only_transformations(self, content: str, field_changes: Dict[str, str], 
                                        method_changes: Dict[str, str]) -> Tuple[str, List[str]]:
        """
        Apply all transformations using only regex to preserve formatting.
        
        Args:
            content: Python content to transform
            field_changes: Dict of field name changes
            method_changes: Dict of method name changes
            
        Returns:
            Tuple of (modified_content, list_of_applied_changes)
        """
        modified_content = content
        applied_changes = []
        
        # 1. Field assignments: field_name = fields.Type(...)
        for old_name, new_name in field_changes.items():
            # Match field definitions with proper word boundaries
            pattern = rf'\b{re.escape(old_name)}\s*=\s*fields\.'
            if re.search(pattern, modified_content):
                modified_content = re.sub(
                    rf'\b{re.escape(old_name)}\b(?=\s*=\s*fields\.)',
                    new_name,
                    modified_content
                )
                applied_changes.append(f"Field definition: {old_name} → {new_name}")
        
        # 2. Method definitions: def method_name(self, ...):
        for old_name, new_name in method_changes.items():
            pattern = rf'\bdef\s+{re.escape(old_name)}\s*\('
            if re.search(pattern, modified_content):
                modified_content = re.sub(
                    rf'\bdef\s+{re.escape(old_name)}\b(?=\s*\()',
                    f'def {new_name}',
                    modified_content
                )
                applied_changes.append(f"Method definition: {old_name} → {new_name}")
        
        # 3. Method calls: self.method_name(...) or obj.method_name(...)
        for old_name, new_name in method_changes.items():
            pattern = rf'\.{re.escape(old_name)}\s*\('
            if re.search(pattern, modified_content):
                modified_content = re.sub(
                    rf'\.{re.escape(old_name)}\b(?=\s*\()',
                    f'.{new_name}',
                    modified_content
                )
                applied_changes.append(f"Method call: {old_name} → {new_name}")
        
        # 4. String references in quotes
        for old_name, new_name in field_changes.items():
            # Single quotes
            pattern = rf"'{re.escape(old_name)}'"
            if re.search(pattern, modified_content):
                modified_content = re.sub(pattern, f"'{new_name}'", modified_content)
                applied_changes.append(f"String reference (single quotes): '{old_name}' → '{new_name}'")
            
            # Double quotes  
            pattern = rf'"{re.escape(old_name)}"'
            if re.search(pattern, modified_content):
                modified_content = re.sub(pattern, f'"{new_name}"', modified_content)
                applied_changes.append(f"String reference (double quotes): \"{old_name}\" → \"{new_name}\"")
        
        for old_name, new_name in method_changes.items():
            # Single quotes for method names
            pattern = rf"'{re.escape(old_name)}'"
            if re.search(pattern, modified_content):
                modified_content = re.sub(pattern, f"'{new_name}'", modified_content)
                applied_changes.append(f"String reference (single quotes): '{old_name}' → '{new_name}'")
            
            # Double quotes for method names
            pattern = rf'"{re.escape(old_name)}"'
            if re.search(pattern, modified_content):
                modified_content = re.sub(pattern, f'"{new_name}"', modified_content)
                applied_changes.append(f"String reference (double quotes): \"{old_name}\" → \"{new_name}\"")
        
        # Apply the existing regex transformations for decorators and other patterns
        modified_content = self._apply_regex_transformations(
            modified_content, field_changes, method_changes
        )
        
        return modified_content, applied_changes
    
    def _filter_relevant_changes(self, file_path: Path, changes: List[FieldChange]) -> List[FieldChange]:
        """
        Filter changes relevant to this Python file.
        
        Args:
            file_path: Path to the Python file
            changes: All changes to consider
            
        Returns:
            List of relevant changes
        """
        # For Python files, we need to read the content to determine which models are defined
        try:
            content = self._read_file_content(file_path)
            models_in_file = self._extract_models_from_python_file(content)
            
            # Filter changes for models that are defined or inherited in this file
            relevant_changes = []
            for change in changes:
                model_key = f"{change.module}.{change.model}"
                if model_key in models_in_file or change.model in models_in_file:
                    relevant_changes.append(change)
                    logger.debug(f"Relevant change for {file_path}: {change}")
            
            return relevant_changes
            
        except Exception as e:
            logger.warning(f"Could not filter changes for {file_path}: {e}")
            # If we can't determine, return all changes and let AST handle it
            return changes
    
    def _extract_models_from_python_file(self, content: str) -> Set[str]:
        """
        Extract model names defined or inherited in a Python file.
        
        Args:
            content: Python file content
            
        Returns:
            Set of model names found in the file
        """
        models = set()
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Look for _name and _inherit attributes
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            targets = [t.id for t in item.targets if isinstance(t, ast.Name)]
                            
                            if '_name' in targets and isinstance(item.value, ast.Constant):
                                models.add(item.value.value)
                            elif '_inherit' in targets:
                                if isinstance(item.value, ast.Constant):
                                    models.add(item.value.value)
                                elif isinstance(item.value, ast.List):
                                    for elt in item.value.elts:
                                        if isinstance(elt, ast.Constant):
                                            models.add(elt.value)
            
        except Exception as e:
            logger.debug(f"Error extracting models from Python content: {e}")
        
        return models
    
    def _validate_python_transformations(self, original_content: str, 
                                       modified_content: str, 
                                       changes: List[FieldChange]) -> bool:
        """
        Validate that Python transformations were applied correctly.
        
        Args:
            original_content: Original file content
            modified_content: Modified file content
            changes: Changes that were supposed to be applied
            
        Returns:
            True if transformations appear correct
        """
        # Check that we haven't accidentally broken imports or basic structure
        try:
            original_tree = ast.parse(original_content)
            modified_tree = ast.parse(modified_content)
            
            # Count nodes to ensure structure is preserved
            original_nodes = len(list(ast.walk(original_tree)))
            modified_nodes = len(list(ast.walk(modified_tree)))
            
            # Allow for small differences due to AST normalization
            if abs(original_nodes - modified_nodes) > len(changes):
                logger.warning("Significant structural changes detected in AST")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating Python transformations: {e}")
            return False
    
    def get_file_analysis(self, file_path: Path) -> Dict[str, any]:
        """
        Analyze a Python file to extract information about fields and methods.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Dictionary with analysis results
        """
        try:
            content = self._read_file_content(file_path)
            tree = ast.parse(content)
            
            fields = []
            methods = []
            models = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Extract model information
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            targets = [t.id for t in item.targets if isinstance(t, ast.Name)]
                            
                            # Model names
                            if '_name' in targets and isinstance(item.value, ast.Constant):
                                models.append(item.value.value)
                            
                            # Field definitions
                            if (len(item.targets) == 1 and 
                                isinstance(item.targets[0], ast.Name) and
                                self._is_fields_call_analysis(item.value)):
                                fields.append(item.targets[0].id)
                        
                        # Method definitions
                        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            methods.append(item.name)
            
            return {
                'models': models,
                'fields': fields,
                'methods': methods,
                'total_lines': len(content.splitlines()),
                'file_size': len(content)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing Python file {file_path}: {e}")
            return {
                'models': [],
                'fields': [],
                'methods': [],
                'error': str(e)
            }
    
    def _is_fields_call_analysis(self, node) -> bool:
        """Check if node is a fields.FieldType() call for analysis"""
        return (isinstance(node, ast.Call) and 
                isinstance(node.func, ast.Attribute) and
                isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'fields')