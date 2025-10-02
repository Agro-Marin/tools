"""
AST Visitor for Odoo Models
===========================

AST visitor that produces Model objects directly from Odoo code.
"""

import ast
import logging
from typing import List, Optional, Dict, Any
from core.models import Model, Field, Method, Reference, CallType, InheritanceType

logger = logging.getLogger(__name__)


class OdooASTVisitor(ast.NodeVisitor):
    """
    AST visitor that extracts Odoo model information:
    - Model definitions and inheritance
    - Field and method definitions
    - References and cross-model calls
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.models: List[Model] = []
        self.current_model: Optional[Model] = None
        self.current_method: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Unified class definition visitor that extracts complete model information
        """
        if self._is_odoo_model(node):
            logger.debug(f"Found Odoo model class: {node.name}")

            # Extract complete model information in one pass
            model = self._extract_complete_model(node)
            if model:
                self.models.append(model)

                # Set context and visit children
                old_model = self.current_model
                self.current_model = model
                self.generic_visit(node)
                self.current_model = old_model
        else:
            self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit method definitions within Odoo models"""
        if self.current_model:
            # Extract method information
            method = self._extract_method_info(node)
            self.current_model.methods.append(method)

            # Set method context for finding references
            old_method = self.current_method
            self.current_method = node.name

            # Visit method body to find references
            self.generic_visit(node)

            # Restore method context
            self.current_method = old_method
        else:
            self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignments to find field definitions"""
        if self.current_model and self._is_odoo_field_assignment(node):
            # Extract field information
            field = self._extract_field_info(node)
            if field:
                self.current_model.fields.append(field)

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Visit attribute access to find field and method references"""
        if self.current_model and self.current_method:
            # Detect different types of references
            reference = self._detect_reference_type(node)
            if reference:
                self.current_model.references.append(reference)

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls to detect super() calls and cross-model references"""
        if self.current_model and self.current_method:
            # Detect super() calls
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Call):
                    # Check for super().method() pattern
                    if (
                        isinstance(node.func.value.func, ast.Name)
                        and node.func.value.func.id == "super"
                    ):
                        reference = Reference(
                            reference_type="method",
                            reference_name=node.func.attr,
                            call_type=CallType.SUPER,
                            source_model=self.current_model.name,
                            source_method=self.current_method,
                            source_file=self.file_path,
                            line_number=node.lineno,
                        )
                        self.current_model.references.append(reference)

            # Detect cross-model calls like self.env['model.name'].method()
            cross_ref = self._detect_cross_model_call(node)
            if cross_ref:
                self.current_model.references.append(cross_ref)

        self.generic_visit(node)

    def _extract_complete_model(self, node: ast.ClassDef) -> Optional[Model]:
        """
        Extract complete model information combining both visitor approaches
        """
        # Extract inheritance information
        inheritance_info = self._extract_inheritance_info(node)
        if not inheritance_info:
            return None

        return Model(
            name=inheritance_info["model_name"],
            class_name=node.name,
            file_path=self.file_path,
            line_number=node.lineno,
            inheritance_type=inheritance_info["inheritance_type"],
            inherits_from=inheritance_info["inherits_from"],
            fields=[],  # Will be filled by visit_Assign
            methods=[],  # Will be filled by visit_FunctionDef
            references=[],  # Will be filled by visit_Attribute
        )

    def _extract_inheritance_info(self, node: ast.ClassDef) -> Optional[Dict[str, Any]]:
        """Extract inheritance information from class definition"""
        model_name = None
        primary_model = None  # The _name value (primary model)
        inherit_models = []
        inheritance_type = InheritanceType.NAME

        # Look for _name, _inherit, _inherits assignments in class body
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "_name" and isinstance(
                            child.value, ast.Constant
                        ):
                            primary_model = child.value.value
                            inheritance_type = InheritanceType.NAME
                        elif target.id == "_inherit":
                            if isinstance(child.value, ast.Constant):
                                inherit_models = [child.value.value]
                            elif isinstance(child.value, ast.List):
                                inherit_models = [
                                    elt.value
                                    for elt in child.value.elts
                                    if isinstance(elt, ast.Constant)
                                ]
                            # Only set inheritance_type if no _name exists
                            if not primary_model:
                                inheritance_type = InheritanceType.INHERIT

        # CRITICAL: Determine if this is truly a base module or an extension
        # If a model has BOTH _name AND _inherit with the same model, it's an EXTENSION
        # Example: _name='sale.order' + _inherit=['sale.order', ...] = EXTENSION of sale.order
        if primary_model:
            model_name = primary_model

            # Check if inheriting from itself (extension pattern)
            if primary_model in inherit_models:
                # This is an extension: _name='X' + _inherit=['X', ...]
                inheritance_type = InheritanceType.INHERIT
        elif inherit_models:
            # Fallback: single inheritance without _name
            model_name = inherit_models[0]
            inheritance_type = InheritanceType.INHERIT
        else:
            return None

        return {
            "model_name": model_name,
            "inheritance_type": inheritance_type,
            "inherits_from": inherit_models,
            "primary_model": primary_model,  # Track the actual primary model
        }

    def _is_odoo_model(self, node: ast.ClassDef) -> bool:
        """Check if class is an Odoo model"""
        for base in node.bases:
            if isinstance(base, ast.Attribute):
                # models.Model, models.TransientModel, etc.
                if (
                    isinstance(base.value, ast.Name)
                    and base.value.id == "models"
                    and base.attr in ["Model", "TransientModel", "AbstractModel"]
                ):
                    return True
            elif isinstance(base, ast.Name):
                # Direct inheritance from Model, etc.
                if base.id in ["Model", "TransientModel", "AbstractModel"]:
                    return True

        # Also check if class has _name, _inherit, or _inherits
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id in [
                        "_name",
                        "_inherit",
                        "_inherits",
                    ]:
                        return True

        return False

    def _is_odoo_field_assignment(self, node: ast.Assign) -> bool:
        """Check if assignment is an Odoo field definition"""
        if not isinstance(node.value, ast.Call):
            return False

        # Check for fields.* calls
        if isinstance(node.value.func, ast.Attribute):
            if (
                isinstance(node.value.func.value, ast.Name)
                and node.value.func.value.id == "fields"
            ):
                return True

        return False

    def _extract_field_info(self, node: ast.Assign) -> Optional[Field]:
        """Extract field information from assignment"""
        if not node.targets or not isinstance(node.targets[0], ast.Name):
            return None

        field_name = node.targets[0].id

        if not isinstance(node.value, ast.Call):
            return None

        # Extract field type
        field_type = ""
        if isinstance(node.value.func, ast.Attribute):
            field_type = node.value.func.attr

        # Extract args and kwargs
        args = []
        kwargs = {}

        for arg in node.value.args:
            if isinstance(arg, ast.Constant):
                args.append(str(arg.value))

        for keyword in node.value.keywords:
            if isinstance(keyword.value, ast.Constant):
                kwargs[keyword.arg] = str(keyword.value.value)

        return Field(
            name=field_name,
            field_type=field_type,
            args=args,
            kwargs=kwargs,
            signature=self._get_field_signature(node),
            definition=self._get_source_segment(node),
            line_number=node.lineno,
            source_file=self.file_path,
        )

    def _extract_method_info(self, node: ast.FunctionDef) -> Method:
        """Extract method information from function definition"""
        args = [arg.arg for arg in node.args.args]
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]

        return Method(
            name=node.name,
            args=args,
            decorators=decorators,
            signature=self._get_method_signature(node),
            definition=self._get_source_segment(node),
            line_number=node.lineno,
            source_file=self.file_path,
        )

    def _extract_decorators(self, node: ast.ClassDef) -> List[str]:
        """Extract decorators from class definition"""
        return [self._get_decorator_name(dec) for dec in node.decorator_list]

    def _get_decorator_name(self, decorator) -> str:
        """Get decorator name as string"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return (
                f"{decorator.value.id}.{decorator.attr}"
                if isinstance(decorator.value, ast.Name)
                else decorator.attr
            )
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return str(decorator)

    def _get_method_signature(self, node: ast.FunctionDef) -> str:
        """Get method signature as string"""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        return f"def {node.name}({', '.join(args)})"

    def _get_field_signature(self, node: ast.Assign) -> str:
        """Get field signature as string"""
        try:
            return ast.unparse(node) if hasattr(ast, "unparse") else str(node.lineno)
        except:
            return f"line {node.lineno}"

    def _get_source_segment(self, node) -> str:
        """Get source code segment for node"""
        try:
            with open(self.file_path, "r") as f:
                content = f.read()
            if hasattr(ast, "get_source_segment"):
                return ast.get_source_segment(content, node) or ""
            return f"# Source at line {node.lineno}"
        except:
            return f"# Source at line {node.lineno}"

    def _detect_reference_type(self, node: ast.Attribute) -> Optional[Reference]:
        """Reference detection with different call types"""
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            # Self-reference: self.field or self.method
            parent = getattr(node, "parent", None)
            ref_type = (
                "method"
                if isinstance(parent, ast.Call) and parent.func == node
                else "field"
            )

            return Reference(
                reference_type=ref_type,
                reference_name=node.attr,
                call_type=CallType.SELF,
                source_model=self.current_model.name,
                source_method=self.current_method,
                source_file=self.file_path,
                line_number=node.lineno,
            )

        elif self._is_cross_model_reference(node):
            # Cross-model reference: record.field or record.method()
            parent = getattr(node, "parent", None)
            ref_type = (
                "method"
                if isinstance(parent, ast.Call) and parent.func == node
                else "field"
            )
            target_model = self._extract_target_model(node)

            return Reference(
                reference_type=ref_type,
                reference_name=node.attr,
                call_type=CallType.CROSS_MODEL,
                source_model=self.current_model.name,
                source_method=self.current_method,
                source_file=self.file_path,
                line_number=node.lineno,
                target_model=target_model,
            )

        return None

    def _is_cross_model_reference(self, node: ast.Attribute) -> bool:
        """Check if this is a cross-model reference"""
        # Patterns like:
        # - record.field
        # - self.partner_id.name
        # - order_line.product_id.name
        if isinstance(node.value, ast.Name):
            # Simple variable reference
            return node.value.id not in ["self", "cls"]
        elif isinstance(node.value, ast.Attribute):
            # Chained attribute access
            return True
        return False

    def _extract_target_model(self, node: ast.Attribute) -> str:
        """Extract target model from cross-model reference"""
        # This is a simplified approach - in practice, we'd need type analysis
        # For now, return empty string as we'll resolve it later via inheritance graph
        return ""

    def _detect_cross_model_call(self, node: ast.Call) -> Optional[Reference]:
        """Detect cross-model method calls"""
        # Pattern: self.env['model.name'].method()
        if isinstance(node.func, ast.Attribute) and isinstance(
            node.func.value, ast.Subscript
        ):

            # Check for self.env['model.name'] pattern
            if (
                isinstance(node.func.value.value, ast.Attribute)
                and isinstance(node.func.value.value.value, ast.Name)
                and node.func.value.value.value.id == "self"
                and node.func.value.value.attr == "env"
            ):

                # Extract model name from subscript
                if isinstance(node.func.value.slice, ast.Constant):
                    target_model = node.func.value.slice.value

                    return Reference(
                        reference_type="method",
                        reference_name=node.func.attr,
                        call_type=CallType.CROSS_MODEL,
                        source_model=self.current_model.name,
                        source_method=self.current_method,
                        source_file=self.file_path,
                        line_number=node.lineno,
                        target_model=target_model,
                    )

        return None

    def detect_decorator_references(self, content: str) -> List[Reference]:
        """Detect field/method references in decorators like @api.depends()"""
        references = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        decorator_refs = self._extract_decorator_references(
                            decorator, node
                        )
                        references.extend(decorator_refs)

        except Exception as e:
            logger.error(f"Error detecting decorator references: {e}")

        return references

    def _extract_decorator_references(
        self, decorator, method_node: ast.FunctionDef
    ) -> List[Reference]:
        """Extract field references from decorators"""
        references = []

        # Handle @api.depends('field1', 'field2') pattern
        if isinstance(decorator, ast.Call):
            decorator_name = self._get_decorator_name(decorator)

            if "depends" in decorator_name or "constrains" in decorator_name:
                for arg in decorator.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        # Each string argument is a field reference
                        field_name = arg.value

                        reference = Reference(
                            reference_type="field",
                            reference_name=field_name,
                            call_type=CallType.DECORATOR,
                            source_model=(
                                self.current_model.name if self.current_model else ""
                            ),
                            source_method=method_node.name,
                            source_file=self.file_path,
                            line_number=decorator.lineno,
                        )
                        references.append(reference)

        return references


def extract_models(content: str, file_path: str) -> List[Model]:
    """
    Extract Model objects from Python source code with cross-reference detection.

    Args:
        content: Python source code
        file_path: Path to the source file

    Returns:
        List of Model objects found in the file
    """
    try:
        tree = ast.parse(content)
        visitor = OdooASTVisitor(file_path)

        # Add parent references for better context
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node

        visitor.visit(tree)

        # Post-process to add decorator references
        for model in visitor.models:
            decorator_refs = visitor.detect_decorator_references(content)

            # Filter decorator references by model
            model_decorator_refs = [
                ref for ref in decorator_refs if ref.source_model == model.name
            ]
            model.references.extend(model_decorator_refs)

        return visitor.models
    except SyntaxError as e:
        logger.error(f"Syntax error parsing {file_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
        return []


# Alias for backward compatibility
extract_unified_models = extract_models
