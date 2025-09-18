"""
CSV Manager for Field/Method Changes
====================================

Handles reading, writing, and deduplication of CSV files containing
field and method rename records.
"""
import csv
import os
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
import logging

from analyzers.matching_engine import RenameCandidate
from config.settings import CSV_HEADERS, CSV_ENCODING

logger = logging.getLogger(__name__)


class CSVManager:
    """Manager for CSV operations with deduplication and validation"""
    
    def __init__(self, csv_file_path: str):
        """
        Initialize CSV manager.
        
        Args:
            csv_file_path: Path to the CSV file
        """
        self.csv_file_path = Path(csv_file_path)
        self.headers = CSV_HEADERS
        self.encoding = CSV_ENCODING
        self.existing_records = []
        self.existing_record_keys = set()
    
    def load_existing_csv(self) -> List[Dict[str, str]]:
        """
        Load existing CSV records for deduplication.
        
        Returns:
            List of existing records as dictionaries
        """
        if not self.csv_file_path.exists():
            logger.info(f"CSV file {self.csv_file_path} does not exist, will create new one")
            return []
        
        try:
            with open(self.csv_file_path, 'r', encoding=self.encoding, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Validate headers
                if reader.fieldnames != self.headers:
                    logger.warning(f"CSV headers mismatch. Expected: {self.headers}, Found: {reader.fieldnames}")
                
                records = []
                for row_num, row in enumerate(reader, start=2):  # Start at 2 because header is row 1
                    # Clean and validate row
                    cleaned_row = self._clean_csv_row(row)
                    if self._validate_csv_row(cleaned_row, row_num):
                        records.append(cleaned_row)
                        # Create unique key for deduplication
                        record_key = self._create_record_key(cleaned_row)
                        self.existing_record_keys.add(record_key)
                
                self.existing_records = records
                logger.info(f"Loaded {len(records)} existing records from {self.csv_file_path}")
                
                return records
                
        except Exception as e:
            logger.error(f"Error loading CSV file {self.csv_file_path}: {e}")
            return []
    
    def _clean_csv_row(self, row: Dict[str, str]) -> Dict[str, str]:
        """Clean CSV row data"""
        cleaned = {}
        for header in self.headers:
            value = row.get(header, '').strip()
            cleaned[header] = value
        return cleaned
    
    def _validate_csv_row(self, row: Dict[str, str], row_num: int) -> bool:
        """Validate CSV row data"""
        # Check required fields
        required_fields = ['old_name', 'new_name']
        for field in required_fields:
            if not row.get(field):
                logger.warning(f"Row {row_num}: Missing required field '{field}'")
                return False
        
        # Check for obvious duplicates within the row
        if row['old_name'] == row['new_name']:
            logger.warning(f"Row {row_num}: old_name and new_name are identical: {row['old_name']}")
            return False
        
        return True
    
    def _create_record_key(self, record: Dict[str, str]) -> str:
        """Create unique key for record deduplication"""
        return f"{record['old_name']}→{record['new_name']}:{record.get('item_type', '')}:{record.get('module', '')}:{record.get('model', '')}"
    
    def filter_new_candidates(self, candidates: List[RenameCandidate]) -> Tuple[List[RenameCandidate], List[RenameCandidate]]:
        """
        Filter candidates to separate new ones from existing ones.
        
        Args:
            candidates: List of rename candidates
            
        Returns:
            Tuple of (new_candidates, duplicate_candidates)
        """
        new_candidates = []
        duplicate_candidates = []
        
        for candidate in candidates:
            record_key = self._create_record_key_from_candidate(candidate)
            
            if record_key in self.existing_record_keys:
                duplicate_candidates.append(candidate)
                logger.debug(f"Duplicate candidate found: {candidate.old_name} → {candidate.new_name}")
            else:
                new_candidates.append(candidate)
        
        logger.info(f"Filtered {len(new_candidates)} new candidates, skipped {len(duplicate_candidates)} duplicates")
        
        return new_candidates, duplicate_candidates
    
    def _create_record_key_from_candidate(self, candidate: RenameCandidate) -> str:
        """Create record key from rename candidate"""
        return f"{candidate.old_name}→{candidate.new_name}:{candidate.item_type}:{candidate.module}:{candidate.model}"
    
    def add_candidates_to_csv(self, candidates: List[RenameCandidate], 
                             backup_existing: bool = True) -> int:
        """
        Add new candidates to CSV file.
        
        Args:
            candidates: List of rename candidates to add
            backup_existing: Whether to backup existing file
            
        Returns:
            Number of records added
        """
        if not candidates:
            logger.info("No candidates to add to CSV")
            return 0
        
        # Create backup if requested and file exists
        if backup_existing and self.csv_file_path.exists():
            self._create_backup()
        
        # Ensure directory exists
        self.csv_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert candidates to CSV records
        new_records = [self._candidate_to_csv_record(candidate) for candidate in candidates]
        
        # Combine with existing records
        all_records = self.existing_records + new_records
        
        try:
            # Write all records to CSV
            with open(self.csv_file_path, 'w', encoding=self.encoding, newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.headers)
                writer.writeheader()
                writer.writerows(all_records)
            
            logger.info(f"Added {len(new_records)} new records to {self.csv_file_path}")
            logger.info(f"Total records in CSV: {len(all_records)}")
            
            return len(new_records)
            
        except Exception as e:
            logger.error(f"Error writing to CSV file {self.csv_file_path}: {e}")
            raise
    
    def _candidate_to_csv_record(self, candidate: RenameCandidate) -> Dict[str, str]:
        """Convert rename candidate to CSV record"""
        return {
            'old_name': candidate.old_name,
            'new_name': candidate.new_name,
            'item_type': candidate.item_type,
            'module': candidate.module,
            'model': candidate.model
        }
    
    def _create_backup(self) -> Optional[Path]:
        """Create backup of existing CSV file"""
        if not self.csv_file_path.exists():
            return None
        
        # Create backup filename with timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.csv_file_path.with_suffix(f'.backup_{timestamp}.csv')
        
        try:
            import shutil
            shutil.copy2(self.csv_file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.warning(f"Could not create backup: {e}")
            return None
    
    def validate_csv_integrity(self) -> Dict[str, any]:
        """
        Validate CSV file integrity and return statistics.
        
        Returns:
            Dictionary with validation results and statistics
        """
        if not self.csv_file_path.exists():
            return {
                'exists': False,
                'valid': False,
                'error': 'File does not exist'
            }
        
        try:
            with open(self.csv_file_path, 'r', encoding=self.encoding, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Check headers
                headers_valid = reader.fieldnames == self.headers
                
                # Count records and check for issues
                total_records = 0
                valid_records = 0
                duplicate_keys = set()
                duplicates_found = 0
                issues = []
                
                for row_num, row in enumerate(reader, start=2):
                    total_records += 1
                    
                    # Clean row
                    cleaned_row = self._clean_csv_row(row)
                    
                    # Validate row
                    if self._validate_csv_row(cleaned_row, row_num):
                        valid_records += 1
                        
                        # Check for duplicates
                        record_key = self._create_record_key(cleaned_row)
                        if record_key in duplicate_keys:
                            duplicates_found += 1
                            issues.append(f"Row {row_num}: Duplicate record - {record_key}")
                        else:
                            duplicate_keys.add(record_key)
                    else:
                        issues.append(f"Row {row_num}: Invalid record")
                
                return {
                    'exists': True,
                    'valid': headers_valid and valid_records == total_records,
                    'headers_valid': headers_valid,
                    'total_records': total_records,
                    'valid_records': valid_records,
                    'duplicate_records': duplicates_found,
                    'issues': issues,
                    'file_size': self.csv_file_path.stat().st_size
                }
                
        except Exception as e:
            return {
                'exists': True,
                'valid': False,
                'error': str(e)
            }
    
    def export_candidates_report(self, candidates: List[RenameCandidate], 
                                report_file: str) -> bool:
        """
        Export detailed candidates report to CSV.
        
        Args:
            candidates: List of rename candidates
            report_file: Path to report file
            
        Returns:
            True if successful
        """
        if not candidates:
            logger.warning("No candidates to export")
            return False
        
        # Extended headers for detailed report
        extended_headers = [
            'old_name', 'new_name', 'module', 'model', 'type',
            'confidence', 'signature_match', 'rule_applied',
            'file_path'
        ]
        
        try:
            report_path = Path(report_file)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_path, 'w', encoding=self.encoding, newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=extended_headers)
                writer.writeheader()
                
                for candidate in candidates:
                    row = {
                        'old_name': candidate.old_name,
                        'new_name': candidate.new_name,
                        'module': candidate.module,
                        'model': candidate.model,
                        'type': candidate.item_type,
                        'confidence': f"{candidate.confidence:.3f}",
                        'signature_match': candidate.signature_match,
                        'rule_applied': candidate.rule_applied or '',
                        'file_path': candidate.file_path
                    }
                    writer.writerow(row)
            
            logger.info(f"Exported detailed report with {len(candidates)} candidates to {report_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting candidates report: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, any]:
        """Get statistics about current CSV data"""
        if not self.existing_records:
            return {
                'total_records': 0,
                'modules': {},
                'models': {},
                'field_changes': 0,
                'method_changes': 0
            }
        
        modules = {}
        models = {}
        
        for record in self.existing_records:
            module = record.get('module', 'unknown')
            model = record.get('model', 'unknown')
            
            modules[module] = modules.get(module, 0) + 1
            models[model] = models.get(model, 0) + 1
        
        return {
            'total_records': len(self.existing_records),
            'unique_modules': len(modules),
            'unique_models': len(models),
            'modules': modules,
            'models': models,
            'file_path': str(self.csv_file_path),
            'file_exists': self.csv_file_path.exists()
        }