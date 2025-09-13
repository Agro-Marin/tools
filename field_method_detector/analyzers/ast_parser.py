"""
AST Parser for Odoo Python and XML Files
=========================================

Parses Python files using AST to extract field and method information.
Also handles basic XML parsing for view files.
"""
import ast
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Set, Any
import logging
import re

logger = logging.getLogger(__name__)


class OdooASTVisitor(ast.NodeVisitor):
    """AST visitor specifically for Odoo model files"""
    
    def __init__(self):
        self.fields = []
        self.methods = []
        self.classes = []
        self.current_model = None
        self.current_class_node = None
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definitions to identify Odoo models"""
        if self._is_odoo_model(node):
            # Store previous context
            old_model = self.current_model
            old_class_node = self.current_class_node
            
            # Set current context
            self.current_model = self._extract_model_name(node)
            self.current_class_node = node
            
            # Store class info
            class_info = {
                'name': node.name,
                'model_name': self.current_model,
                'inheritance': self._extract_inheritance(node),
                'line': node.lineno,
                'decorators': self._extract_decorators(node)
            }
            self.classes.append(class_info)
            
            # Visit children
            self.generic_visit(node)
            
            # Restore previous context
            self.current_model = old_model
            self.current_class_node = old_class_node
        else:
            # Not an Odoo model, visit normally
            self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Visit assignments to detect Odoo field definitions"""
        if self.current_model and self._is_odoo_field_assignment(node):
            field_info = self._extract_field_info(node)
            if field_info:
                field_info['model'] = self.current_model
                field_info['line'] = node.lineno
                self.fields.append(field_info)
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions to detect methods"""
        if self.current_model:
            method_info = self._extract_method_info(node)
            if method_info:
                method_info['model'] = self.current_model
                method_info['line'] = node.lineno
                self.methods.append(method_info)
        
        self.generic_visit(node)
    
    def _is_odoo_model(self, node: ast.ClassDef) -> bool:
        """Check if class is an Odoo model"""
        for base in node.bases:
            if isinstance(base, ast.Attribute):
                # models.Model, models.TransientModel, etc.
                if (isinstance(base.value, ast.Name) and 
                    base.value.id == 'models' and 
                    base.attr in ['Model', 'TransientModel', 'AbstractModel']):
                    return True
            elif isinstance(base, ast.Name):
                # Inherited from another model class
                if base.id.endswith('Model'):
                    return True
        
        return False
    
    def _extract_model_name(self, node: ast.ClassDef) -> Optional[str]:
        """Extract _name attribute from model class"""
        for item in node.body:
            if (isinstance(item, ast.Assign) and 
                len(item.targets) == 1 and
                isinstance(item.targets[0], ast.Name) and
                item.targets[0].id == '_name' and
                isinstance(item.value, ast.Constant)):
                return item.value.value
        
        # If no _name found, try to infer from class name
        return self._infer_model_name_from_class(node.name)
    
    def _infer_model_name_from_class(self, class_name: str) -> str:
        """Infer model name from class name"""
        # Convert CamelCase to dot.notation
        # e.g., SaleOrder -> sale.order
        result = []
        for i, char in enumerate(class_name):
            if char.isupper() and i > 0:
                result.append('.')
            result.append(char.lower())
        return ''.join(result)
    
    def _extract_inheritance(self, node: ast.ClassDef) -> List[str]:
        """Extract inheritance information"""
        inheritance = []
        for base in node.bases:
            if isinstance(base, ast.Attribute):
                inheritance.append(f"{base.value.id}.{base.attr}")
            elif isinstance(base, ast.Name):
                inheritance.append(base.id)
        return inheritance
    
    def _extract_decorators(self, node) -> List[str]:
        """Extract decorators from node"""
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(f"{decorator.value.id}.{decorator.attr}")
            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                decorators.append(f"{decorator.func.value.id}.{decorator.func.attr}")
        return decorators
    
    def _is_odoo_field_assignment(self, node: ast.Assign) -> bool:
        """Check if assignment is an Odoo field definition"""
        if len(node.targets) != 1:
            return False
        
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            return False
        
        # Check if value is fields.FieldType(...)
        return self._is_fields_call(node.value)
    
    def _is_fields_call(self, node) -> bool:
        """Check if node is a fields.FieldType() call"""
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and 
                node.func.value.id == 'fields'):
                return True
        return False
    
    def _extract_field_info(self, node: ast.Assign) -> Optional[Dict]:
        """Extract field information from assignment"""
        target = node.targets[0]
        field_name = target.id
        
        if not self._is_fields_call(node.value):
            return None
        
        field_type = node.value.func.attr
        
        # Extract field arguments
        args = []
        kwargs = {}
        
        for arg in node.value.args:
            if isinstance(arg, ast.Constant):
                args.append(arg.value)
            else:
                # Use AST node type for non-constant args
                args.append(f"<{type(arg).__name__}>")
        
        for keyword in node.value.keywords:
            if isinstance(keyword.value, ast.Constant):
                kwargs[keyword.arg] = keyword.value.value
            else:
                # Use AST node type for non-constant values
                kwargs[keyword.arg] = f"<{type(keyword.value).__name__}>"
        
        # Generate signature for matching
        signature = self._generate_field_signature(field_type, args, kwargs)
        
        return {
            'name': field_name,
            'type': 'field',
            'field_type': field_type,
            'args': args,
            'kwargs': kwargs,
            'signature': signature,
            'definition': ast.unparse(node.value)
        }
    
    def _extract_method_info(self, node: ast.FunctionDef) -> Optional[Dict]:
        """Extract method information from function definition"""
        # Skip private methods that are not Odoo patterns
        if (node.name.startswith('__') and node.name.endswith('__') and 
            node.name not in ['__init__']):
            return None
        
        # Extract arguments
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        
        # Extract decorators
        decorators = self._extract_decorators(node)
        
        # Generate signature for matching
        signature = self._generate_method_signature(node.name, args, decorators)
        
        return {
            'name': node.name,
            'type': 'method',
            'args': args,
            'decorators': decorators,
            'signature': signature,
            'definition': f"def {node.name}({', '.join(args)}):"
        }
    
    def _generate_field_signature(self, field_type: str, args: List, kwargs: Dict) -> str:
        """Generate unique signature for field matching"""
        # Normalize arguments for consistent comparison, avoiding AST object references
        normalized_args = []
        for arg in args:
            if isinstance(arg, str):
                normalized_args.append(f"'{arg}'")
            elif isinstance(arg, (int, float, bool)):
                normalized_args.append(str(arg))
            else:
                # For AST objects or other complex types, use a placeholder
                normalized_args.append("*")
        
        normalized_kwargs = []
        for key, value in sorted(kwargs.items()):
            if isinstance(value, str):
                if value.startswith('<') and value.endswith('>'):
                    # AST node type placeholder
                    normalized_kwargs.append(f"{key}=*")
                else:
                    normalized_kwargs.append(f"{key}='{value}'")
            elif isinstance(value, (int, float, bool)):
                normalized_kwargs.append(f"{key}={value}")
            else:
                # For other types, use key only
                normalized_kwargs.append(f"{key}=*")
        
        all_args = normalized_args + normalized_kwargs
        return f"{field_type}({', '.join(all_args)})"
    
    def _generate_method_signature(self, name: str, args: List[str], decorators: List[str]) -> str:
        """Generate unique signature for method matching (excludes method name for rename detection)"""
        # Sort decorators for consistent comparison
        sorted_decorators = sorted(decorators) if decorators else []
        decorator_part = '|'.join(sorted_decorators)
        
        # Include argument names (excluding 'self')
        method_args = [arg for arg in args if arg != 'self']
        args_part = ','.join(method_args)
        
        # Don't include method name in signature for rename detection
        return f"{decorator_part}::({args_part})"


class XMLParser:
    """Parser for Odoo XML view files"""
    
    def extract_xml_elements(self, content: str, file_path: str = "") -> Dict[str, List]:
        """
        Extract relevant elements from XML content.
        
        Args:
            content: XML file content
            file_path: File path for context
            
        Returns:
            Dictionary with extracted elements
        """
        elements = {
            'fields': [],
            'methods': [],
            'views': []
        }
        
        try:
            # Parse XML
            root = ET.fromstring(content)
            
            # Extract field references
            for field_elem in root.findall('.//field'):
                name_attr = field_elem.get('name')
                if name_attr:
                    elements['fields'].append({
                        'name': name_attr,
                        'type': 'xml_field_reference',
                        'context': field_elem.tag,
                        'file': file_path
                    })
            
            # Extract method calls (buttons, etc.)
            for button_elem in root.findall('.//button'):
                name_attr = button_elem.get('name')
                if name_attr:
                    elements['methods'].append({
                        'name': name_attr,
                        'type': 'xml_method_reference',
                        'context': 'button',
                        'file': file_path
                    })
            
            # Extract view type changes (tree/list)
            for tree_elem in root.findall('.//tree'):
                elements['views'].append({
                    'type': 'tree_view',
                    'context': 'view_definition',
                    'file': file_path
                })
            
            for list_elem in root.findall('.//list'):
                elements['views'].append({
                    'type': 'list_view', 
                    'context': 'view_definition',
                    'file': file_path
                })
                
        except ET.ParseError as e:
            logger.warning(f"Cannot parse XML file {file_path}: {e}")
        
        return elements


class CodeInventoryExtractor:
    """Main extractor for creating code inventories"""
    
    def __init__(self):
        self.xml_parser = XMLParser()
    
    def extract_python_inventory(self, content: str, file_path: str = "") -> Dict[str, List]:
        """
        Extract complete inventory from Python file content.
        
        Args:
            content: Python file content
            file_path: File path for context
            
        Returns:
            Dictionary with fields, methods, and classes
        """
        inventory = {
            'fields': [],
            'methods': [],
            'classes': [],
            'file_path': file_path
        }
        
        try:
            # Parse Python AST
            tree = ast.parse(content)
            
            # Visit nodes to extract information
            visitor = OdooASTVisitor()
            visitor.visit(tree)
            
            inventory['fields'] = visitor.fields
            inventory['methods'] = visitor.methods
            inventory['classes'] = visitor.classes
            
        except SyntaxError as e:
            logger.warning(f"Cannot parse Python file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing {file_path}: {e}")
        
        return inventory
    
    def extract_xml_inventory(self, content: str, file_path: str = "") -> Dict[str, List]:
        """
        Extract inventory from XML file content.
        
        Args:
            content: XML file content
            file_path: File path for context
            
        Returns:
            Dictionary with XML elements
        """
        inventory = self.xml_parser.extract_xml_elements(content, file_path)
        inventory['file_path'] = file_path
        return inventory
    
    def extract_inventory(self, content: str, file_path: str = "") -> Dict[str, List]:
        """
        Extract inventory based on file type.
        
        Args:
            content: File content
            file_path: File path to determine type
            
        Returns:
            Extracted inventory
        """
        if file_path.endswith('.py'):
            return self.extract_python_inventory(content, file_path)
        elif file_path.endswith('.xml'):
            return self.extract_xml_inventory(content, file_path)
        else:
            logger.warning(f"Unsupported file type: {file_path}")
            return {'fields': [], 'methods': [], 'classes': [], 'file_path': file_path}