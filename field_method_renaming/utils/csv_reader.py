"""
CSV Reader for Field/Method Changes
===================================

Handles reading, validation, and parsing of CSV files containing
field and method rename records for application.
"""
import csv
import os
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FieldChange:
    """Represents a field or method change to be applied"""
    old_name: str
    new_name: str
    module: str
    model: str
    change_type: str = 'field'  # 'field' or 'method'
    
    def __post_init__(self):
        """Determine change type based on naming patterns"""
        if self.change_type == 'field':
            # Detect if it's actually a method based on naming patterns
            if (self.old_name.startswith('_') or 
                self.old_name.startswith('action_') or
                self.old_name.startswith('get_') or
                self.old_name.startswith('compute_') or
                self.old_name.startswith('onchange_')):
                self.change_type = 'method'
    
    @property
    def is_field(self) -> bool:
        """Check if this is a field change"""
        return self.change_type == 'field'
    
    @property
    def is_method(self) -> bool:
        """Check if this is a method change"""
        return self.change_type == 'method'
    
    def __str__(self):
        return f"{self.old_name} → {self.new_name} ({self.module}.{self.model}) [{self.change_type}]"


class CSVValidationError(Exception):
    """Exception raised for CSV validation errors"""
    pass


class CSVReader:
    """Reader for CSV files containing field/method changes"""
    
    # Required CSV headers
    REQUIRED_HEADERS = ['old_name', 'new_name', 'module', 'model']
    
    def __init__(self, csv_file_path: str):
        """
        Initialize CSV reader.
        
        Args:
            csv_file_path: Path to the CSV file
        """
        self.csv_file_path = Path(csv_file_path)
        self.encoding = 'utf-8'
        self.changes = []
        
    def load_changes(self) -> List[FieldChange]:
        """
        Load and validate changes from CSV file.
        
        Returns:
            List of FieldChange objects
            
        Raises:
            CSVValidationError: If CSV is invalid or malformed
            FileNotFoundError: If CSV file doesn't exist
        """
        if not self.csv_file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_file_path}")
        
        try:
            with open(self.csv_file_path, 'r', encoding=self.encoding, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Validate headers
                self._validate_csv_headers(reader.fieldnames)
                
                changes = []
                for row_num, row in enumerate(reader, start=2):  # Start at 2 because header is row 1
                    # Clean and validate row
                    cleaned_row = self._clean_csv_row(row)
                    self._validate_csv_row(cleaned_row, row_num)
                    
                    # Create FieldChange object
                    change = FieldChange(
                        old_name=cleaned_row['old_name'],
                        new_name=cleaned_row['new_name'],
                        module=cleaned_row['module'],
                        model=cleaned_row['model']
                    )
                    changes.append(change)
                
                self.changes = changes
                logger.info(f"Loaded {len(changes)} changes from {self.csv_file_path}")
                
                return changes
                
        except Exception as e:
            if isinstance(e, (CSVValidationError, FileNotFoundError)):
                raise
            else:
                raise CSVValidationError(f"Error reading CSV file {self.csv_file_path}: {e}")
    
    def _validate_csv_headers(self, headers: List[str]):
        """Validate CSV headers"""
        if not headers:
            raise CSVValidationError("CSV file is empty or has no headers")
        
        missing_headers = set(self.REQUIRED_HEADERS) - set(headers)
        if missing_headers:
            raise CSVValidationError(f"Missing required headers: {', '.join(missing_headers)}")
        
        logger.debug(f"CSV headers validated: {headers}")
    
    def _clean_csv_row(self, row: Dict[str, str]) -> Dict[str, str]:
        """Clean CSV row data"""
        cleaned = {}
        for header in self.REQUIRED_HEADERS:
            value = row.get(header, '').strip()
            cleaned[header] = value
        return cleaned
    
    def _validate_csv_row(self, row: Dict[str, str], row_num: int):
        """
        Validate CSV row data.
        
        Args:
            row: Cleaned row data
            row_num: Row number for error reporting
            
        Raises:
            CSVValidationError: If row is invalid
        """
        # Check required fields
        for field in self.REQUIRED_HEADERS:
            if not row.get(field):
                raise CSVValidationError(f"Row {row_num}: Missing or empty required field '{field}'")
        
        # Check for identical old and new names
        if row['old_name'] == row['new_name']:
            raise CSVValidationError(f"Row {row_num}: old_name and new_name are identical: {row['old_name']}")
        
        # Validate naming patterns
        self._validate_naming_patterns(row, row_num)
    
    def _validate_naming_patterns(self, row: Dict[str, str], row_num: int):
        """Validate that field/method names follow proper patterns"""
        old_name = row['old_name']
        new_name = row['new_name']
        
        # Check for invalid characters
        invalid_chars = set('!@#$%^&*()+=[]{}|\\:";\'<>?,./')
        
        for name, name_type in [(old_name, 'old_name'), (new_name, 'new_name')]:
            if any(char in invalid_chars for char in name):
                raise CSVValidationError(f"Row {row_num}: {name_type} contains invalid characters: {name}")
            
            if name.startswith(' ') or name.endswith(' '):
                raise CSVValidationError(f"Row {row_num}: {name_type} has leading/trailing spaces: '{name}'")
            
            if '__' in name and not (name.startswith('__') and name.endswith('__')):
                logger.warning(f"Row {row_num}: {name_type} contains double underscores: {name}")
    
    def group_by_module(self, changes: Optional[List[FieldChange]] = None) -> Dict[str, List[FieldChange]]:
        """
        Group changes by module for efficient processing.
        
        Args:
            changes: List of changes to group (uses loaded changes if None)
            
        Returns:
            Dictionary mapping module names to lists of changes
        """
        if changes is None:
            changes = self.changes
        
        grouped = {}
        for change in changes:
            module = change.module
            if module not in grouped:
                grouped[module] = []
            grouped[module].append(change)
        
        # Sort changes within each module
        for module in grouped:
            grouped[module].sort(key=lambda c: (c.model, c.old_name))
        
        logger.debug(f"Grouped {len(changes)} changes into {len(grouped)} modules")
        
        return grouped
    
    def group_by_model(self, changes: Optional[List[FieldChange]] = None) -> Dict[str, List[FieldChange]]:
        """
        Group changes by model for processing.
        
        Args:
            changes: List of changes to group (uses loaded changes if None)
            
        Returns:
            Dictionary mapping model names to lists of changes
        """
        if changes is None:
            changes = self.changes
        
        grouped = {}
        for change in changes:
            model_key = f"{change.module}.{change.model}"
            if model_key not in grouped:
                grouped[model_key] = []
            grouped[model_key].append(change)
        
        # Sort changes within each model
        for model_key in grouped:
            grouped[model_key].sort(key=lambda c: c.old_name)
        
        logger.debug(f"Grouped {len(changes)} changes into {len(grouped)} models")
        
        return grouped
    
    def filter_by_module(self, modules: List[str], changes: Optional[List[FieldChange]] = None) -> List[FieldChange]:
        """
        Filter changes by specific modules.
        
        Args:
            modules: List of module names to include
            changes: List of changes to filter (uses loaded changes if None)
            
        Returns:
            Filtered list of changes
        """
        if changes is None:
            changes = self.changes
        
        module_set = set(modules)
        filtered = [change for change in changes if change.module in module_set]
        
        logger.info(f"Filtered to {len(filtered)} changes for modules: {', '.join(modules)}")
        
        return filtered
    
    def filter_by_change_type(self, change_type: str, changes: Optional[List[FieldChange]] = None) -> List[FieldChange]:
        """
        Filter changes by type (field or method).
        
        Args:
            change_type: 'field' or 'method'
            changes: List of changes to filter (uses loaded changes if None)
            
        Returns:
            Filtered list of changes
        """
        if changes is None:
            changes = self.changes
        
        if change_type not in ['field', 'method']:
            raise ValueError(f"Invalid change_type: {change_type}. Must be 'field' or 'method'")
        
        filtered = [change for change in changes if change.change_type == change_type]
        
        logger.info(f"Filtered to {len(filtered)} {change_type} changes")
        
        return filtered
    
    def get_statistics(self, changes: Optional[List[FieldChange]] = None) -> Dict[str, any]:
        """
        Get statistics about the loaded changes.
        
        Args:
            changes: List of changes to analyze (uses loaded changes if None)
            
        Returns:
            Dictionary with statistics
        """
        if changes is None:
            changes = self.changes
        
        if not changes:
            return {
                'total_changes': 0,
                'field_changes': 0,
                'method_changes': 0,
                'modules': {},
                'models': {}
            }
        
        modules = {}
        models = {}
        field_count = 0
        method_count = 0
        
        for change in changes:
            # Count by type
            if change.is_field:
                field_count += 1
            else:
                method_count += 1
            
            # Count by module
            module = change.module
            modules[module] = modules.get(module, 0) + 1
            
            # Count by model
            model_key = f"{change.module}.{change.model}"
            models[model_key] = models.get(model_key, 0) + 1
        
        return {
            'total_changes': len(changes),
            'field_changes': field_count,
            'method_changes': method_count,
            'unique_modules': len(modules),
            'unique_models': len(models),
            'modules': modules,
            'models': models,
            'csv_file': str(self.csv_file_path)
        }
    
    def validate_csv_integrity(self) -> Dict[str, any]:
        """
        Perform comprehensive validation of the CSV file.
        
        Returns:
            Dictionary with validation results
        """
        if not self.csv_file_path.exists():
            return {
                'valid': False,
                'error': f'File does not exist: {self.csv_file_path}'
            }
        
        try:
            changes = self.load_changes()
            stats = self.get_statistics(changes)
            
            # Additional validations
            issues = []
            
            # Check for duplicate changes
            seen_changes = set()
            duplicates = []
            
            for change in changes:
                change_key = (change.old_name, change.new_name, change.module, change.model)
                if change_key in seen_changes:
                    duplicates.append(str(change))
                else:
                    seen_changes.add(change_key)
            
            if duplicates:
                issues.append(f"Duplicate changes found: {duplicates}")
            
            # Check for circular renames (A→B and B→A)
            rename_pairs = {}
            circular_renames = []
            
            for change in changes:
                key = (change.module, change.model)
                if key not in rename_pairs:
                    rename_pairs[key] = {}
                
                rename_pairs[key][change.old_name] = change.new_name
            
            for key, renames in rename_pairs.items():
                for old_name, new_name in renames.items():
                    if new_name in renames and renames[new_name] == old_name:
                        circular_renames.append(f"{key}: {old_name} ↔ {new_name}")
            
            if circular_renames:
                issues.append(f"Circular renames detected: {circular_renames}")
            
            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'statistics': stats,
                'file_size': self.csv_file_path.stat().st_size
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }