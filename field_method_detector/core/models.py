"""
Model Structures for field_method_detector
==========================================

Single source of truth for all model-related data structures.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum


class InheritanceType(Enum):
    """Type of Odoo model inheritance"""

    NAME = "_name"  # Base model
    INHERIT = "_inherit"  # Extension model
    INHERITS = "_inherits"  # Delegation model


class CallType(Enum):
    """Type of method/field reference"""

    SELF = "self"  # self.method() or self.field
    SUPER = "super"  # super().method()
    CROSS_MODEL = "cross"  # record.method() or other_model.field
    DECORATOR = "decorator"  # @api.depends('field')


class ValidationStatus(Enum):
    """Status of validation for a rename candidate"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


class ChangeScope(Enum):
    """Scope of the change being made"""

    DECLARATION = "declaration"
    REFERENCE = "reference"
    CALL = "call"
    SUPER_CALL = "super_call"


class ImpactType(Enum):
    """Type of impact this change has"""

    PRIMARY = "primary"
    SELF_REFERENCE = "self_reference"
    SELF_CALL = "self_call"
    CROSS_MODEL = "cross_model"
    CROSS_MODEL_CALL = "cross_model_call"
    INHERITANCE = "inheritance"
    DECORATOR = "decorator"


@dataclass
class Field:
    """
    Field representation combining all metadata:
    - Definition information from AST parsing
    - Inheritance information when available
    - Source location and context
    """

    name: str
    field_type: str
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, str] = field(default_factory=dict)
    signature: str = ""
    definition: str = ""
    line_number: int = 0
    source_file: str = ""

    # Inheritance metadata (when needed)
    defined_in_model: str = ""
    is_inherited: bool = False
    is_overridden: bool = False


@dataclass
class Method:
    """
    Method representation combining all metadata:
    - Definition information from AST parsing
    - Inheritance information when available
    - Source location and context
    """

    name: str
    args: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    signature: str = ""
    definition: str = ""
    line_number: int = 0
    source_file: str = ""

    # Inheritance metadata (when needed)
    defined_in_model: str = ""
    is_inherited: bool = False
    is_overridden: bool = False


@dataclass
class Reference:
    """
    Reference representation for method calls and field accesses:
    - Captures context and location information
    - Supports inheritance analysis
    - Used for cross-reference detection
    """

    reference_type: str  # 'field' or 'method'
    reference_name: str
    call_type: CallType
    source_model: str
    source_method: str
    source_file: str
    line_number: int = 0
    target_model: str = ""  # Will be resolved by inheritance analysis


@dataclass
class Model:
    """
    Model representation combining all metadata:
    - Basic model information
    - Inheritance relationships
    - Fields, methods, and references
    """

    # Basic identification
    name: str  # e.g., 'sale.order'
    class_name: str  # e.g., 'SaleOrder'
    file_path: str
    line_number: int = 0

    # Inheritance information
    inheritance_type: InheritanceType = InheritanceType.NAME
    inherits_from: List[str] = field(default_factory=list)
    inherited_by: List[str] = field(default_factory=list)

    # Model contents
    fields: List[Field] = field(default_factory=list)
    methods: List[Method] = field(default_factory=list)
    references: List[Reference] = field(default_factory=list)

    # Utility methods
    def get_field_by_name(self, name: str) -> Optional[Field]:
        """Get field by name"""
        for field_obj in self.fields:
            if field_obj.name == name:
                return field_obj
        return None

    def get_method_by_name(self, name: str) -> Optional[Method]:
        """Get method by name"""
        for method in self.methods:
            if method.name == name:
                return method
        return None

    def is_base_model(self) -> bool:
        """Check if this is a base model (_name)"""
        return self.inheritance_type == InheritanceType.NAME

    def is_inheritance_model(self) -> bool:
        """Check if this is an inheritance model (_inherit)"""
        return self.inheritance_type == InheritanceType.INHERIT

    def is_delegation_model(self) -> bool:
        """Check if this is a delegation model (_inherits)"""
        return self.inheritance_type == InheritanceType.INHERITS

    def get_all_fields(self) -> List[Field]:
        """Get all fields including inherited ones"""
        return self.fields

    def get_all_methods(self) -> List[Method]:
        """Get all methods including inherited ones"""
        return self.methods

    def get_direct_fields(self) -> List[Field]:
        """Get only fields defined directly in this model"""
        return [f for f in self.fields if not f.is_inherited]

    def get_direct_methods(self) -> List[Method]:
        """Get only methods defined directly in this model"""
        return [m for m in self.methods if not m.is_inherited]

    def get_inherited_fields(self) -> List[Field]:
        """Get only inherited fields"""
        return [f for f in self.fields if f.is_inherited]

    def get_inherited_methods(self) -> List[Method]:
        """Get only inherited methods"""
        return [m for m in self.methods if m.is_inherited]

    def get_overridden_fields(self) -> List[Field]:
        """Get only overridden fields"""
        return [f for f in self.fields if f.is_overridden]

    def get_overridden_methods(self) -> List[Method]:
        """Get only overridden methods"""
        return [m for m in self.methods if m.is_overridden]


@dataclass
class RenameCandidate:
    """
    Rename candidate representation with cross-reference support.

    This structure supports the CSV format that captures:
    1. Primary declarations (the original field/method definition)
    2. All impact locations (references, calls, decorators, etc.)
    3. Cross-model references and inheritance impacts
    """

    # Core identification fields
    change_id: str
    old_name: str
    new_name: str
    item_type: str  # 'field', 'method'
    module: str
    model: str  # The model where this change applies

    # New cross-reference fields from the improvement plan
    change_scope: str  # 'declaration', 'reference', 'call', 'super_call'
    impact_type: str  # 'primary', 'self_reference', 'self_call', 'cross_model',
    # 'cross_model_call', 'inheritance', 'decorator'
    context: str  # Specific context (method name, decorator type, etc.)
    confidence: float
    parent_change_id: str = ""  # Links impacts to their primary declaration
    validation_status: str = (
        "pending"  # 'pending', 'approved', 'rejected', 'auto_approved'
    )

    # Legacy compatibility fields
    old_signature: str = ""
    new_signature: str = ""
    affected_models: List[str] = field(default_factory=list)
    source_file: str = ""
    line_number: int = 0

    # Additional fields for compatibility with existing code
    signature_match: bool = False
    rule_applied: str = ""
    scoring_breakdown: Dict[str, float] = field(default_factory=dict)
    validations: List[Dict] = field(default_factory=list)
    api_changes: Dict = field(default_factory=dict)
    file_path: str = ""

    def is_primary_change(self) -> bool:
        """True if this is the primary declaration of the rename"""
        return self.impact_type == "primary"

    def needs_context(self) -> bool:
        """True if this change needs specific context for application"""
        return self.change_scope in ["reference", "call", "super_call"]

    def get_full_context(self) -> str:
        """Returns full context string for debugging"""
        if not self.context:
            return f"{self.change_scope}:{self.impact_type}"
        return f"{self.change_scope}:{self.impact_type}:{self.context}"

    def is_cross_model_impact(self) -> bool:
        """True if this impacts a different model than the declaration"""
        return self.impact_type in ["cross_model", "cross_model_call"]

    def is_self_impact(self) -> bool:
        """True if this impacts the same model as the declaration"""
        return self.impact_type in ["self_reference", "self_call"]

    def is_inheritance_impact(self) -> bool:
        """True if this is an inheritance-related impact"""
        return self.impact_type == "inheritance"

    def is_decorator_impact(self) -> bool:
        """True if this is a decorator-related impact"""
        return self.impact_type == "decorator"

    def get_impact_summary(self) -> str:
        """Get a human-readable summary of this impact"""
        if self.is_primary_change():
            return f"Declaration in {self.model}"
        elif self.is_self_impact():
            return f"Self-reference in {self.context or 'unknown method'}"
        elif self.is_cross_model_impact():
            return f"Cross-model reference from {self.module}.{self.model}"
        elif self.is_inheritance_impact():
            return f"Inheritance impact in {self.model}"
        elif self.is_decorator_impact():
            return f"Decorator reference: {self.context}"
        else:
            return f"Unknown impact type: {self.impact_type}"

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for legacy serialization"""
        return {
            "old_name": self.old_name,
            "new_name": self.new_name,
            "type": self.item_type,
            "module": self.module,
            "model": self.model,
            "confidence": self.confidence,
            "signature_match": self.signature_match,
            "rule_applied": self.rule_applied,
            "scoring_breakdown": self.scoring_breakdown,
            "validations": self.validations,
            "api_changes": self.api_changes,
            "file_path": self.file_path,
        }

    def to_cross_ref_dict(self) -> Dict[str, any]:
        """Convert to dictionary with full cross-reference fields"""
        return {
            "change_id": self.change_id,
            "old_name": self.old_name,
            "new_name": self.new_name,
            "item_type": self.item_type,
            "module": self.module,
            "model": self.model,
            "change_scope": self.change_scope,
            "impact_type": self.impact_type,
            "context": self.context,
            "confidence": self.confidence,
            "parent_change_id": self.parent_change_id,
            "validation_status": self.validation_status,
        }

    @classmethod
    def create_primary_declaration(
        cls,
        change_id: str,
        old_name: str,
        new_name: str,
        item_type: str,
        module: str,
        model: str,
        confidence: float,
        **kwargs,
    ) -> "RenameCandidate":
        """Factory method to create a primary declaration candidate"""
        return cls(
            change_id=change_id,
            old_name=old_name,
            new_name=new_name,
            item_type=item_type,
            module=module,
            model=model,
            change_scope="declaration",
            impact_type="primary",
            context="",
            confidence=confidence,
            parent_change_id="",
            **kwargs,
        )

    @classmethod
    def create_impact_candidate(
        cls,
        parent_change_id: str,
        old_name: str,
        new_name: str,
        item_type: str,
        module: str,
        model: str,
        change_scope: str,
        impact_type: str,
        context: str,
        confidence: float,
        **kwargs,
    ) -> "RenameCandidate":
        """Factory method to create an impact candidate"""
        # Generate unique change_id for impact
        import uuid

        change_id = str(uuid.uuid4())[:8]  # Short UUID for readability

        return cls(
            change_id=change_id,
            old_name=old_name,
            new_name=new_name,
            item_type=item_type,
            module=module,
            model=model,
            change_scope=change_scope,
            impact_type=impact_type,
            context=context,
            confidence=confidence,
            parent_change_id=parent_change_id,
            **kwargs,
        )

    def __str__(self) -> str:
        return f"{self.item_type}_rename: {self.old_name} -> {self.new_name} (confidence: {self.confidence:.2f})"
