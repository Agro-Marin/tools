"""
Configuration Settings for Field/Method Renaming Tool
=====================================================

Default configuration values and environment-specific settings.
"""
import os
from pathlib import Path
from typing import Dict, List


# Default file paths
DEFAULT_OUTPUT_REPORT = "field_renaming_report.json"
DEFAULT_BACKUP_DIR = ".backups"

# Processing configuration
DEFAULT_CREATE_BACKUPS = True
DEFAULT_VALIDATE_SYNTAX = True
DEFAULT_INTERACTIVE_MODE = False
DEFAULT_DRY_RUN = False

# Backup configuration
DEFAULT_BACKUP_RETENTION_DAYS = 30
DEFAULT_COMPRESS_BACKUPS = False

# File filtering settings
SUPPORTED_PYTHON_EXTENSIONS = ['.py']
SUPPORTED_XML_EXTENSIONS = ['.xml']
ALL_SUPPORTED_EXTENSIONS = SUPPORTED_PYTHON_EXTENSIONS + SUPPORTED_XML_EXTENSIONS

# File type categories
FILE_TYPE_CATEGORIES = {
    'python': SUPPORTED_PYTHON_EXTENSIONS,
    'xml': SUPPORTED_XML_EXTENSIONS,
    'views': SUPPORTED_XML_EXTENSIONS,
    'data': SUPPORTED_XML_EXTENSIONS,
    'demo': SUPPORTED_XML_EXTENSIONS,
    'templates': SUPPORTED_XML_EXTENSIONS,
    'reports': SUPPORTED_XML_EXTENSIONS,
    'security': SUPPORTED_XML_EXTENSIONS,
}

# OCA directory structure
OCA_DIRECTORIES = {
    'python': ['models', 'controllers', 'wizards', 'wizard'],
    'views': ['views'],
    'data': ['data'],
    'demo': ['demo'],
    'templates': ['templates'],
    'reports': ['reports'],
    'security': ['security']
}

# File patterns to exclude from processing
EXCLUDE_PATTERNS = [
    '__pycache__',
    '.git',
    '.pytest_cache',
    'migrations',
    '.pyc',
    'node_modules',
    '.venv',
    'venv',
    '.env'
]

# Logging configuration
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Progress reporting
SHOW_PROGRESS_BAR = True
PROGRESS_UPDATE_INTERVAL = 10  # Every N files


class RenamingConfig:
    """Configuration manager with environment variable support"""
    
    def __init__(self):
        # Core settings
        self.create_backups = self._get_bool_env('CREATE_BACKUPS', DEFAULT_CREATE_BACKUPS)
        self.validate_syntax = self._get_bool_env('VALIDATE_SYNTAX', DEFAULT_VALIDATE_SYNTAX)
        self.interactive_mode = self._get_bool_env('INTERACTIVE_MODE', DEFAULT_INTERACTIVE_MODE)
        self.dry_run = self._get_bool_env('DRY_RUN', DEFAULT_DRY_RUN)
        
        # File and directory settings
        self.repo_path = os.getenv('REPO_PATH')
        self.csv_file = os.getenv('CSV_FILE')
        self.backup_dir = os.getenv('BACKUP_DIR', DEFAULT_BACKUP_DIR)
        self.output_report = os.getenv('OUTPUT_REPORT', DEFAULT_OUTPUT_REPORT)
        
        # Backup settings
        self.backup_retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', DEFAULT_BACKUP_RETENTION_DAYS))
        self.compress_backups = self._get_bool_env('COMPRESS_BACKUPS', DEFAULT_COMPRESS_BACKUPS)
        
        # Processing settings
        self.file_types = self._get_list_env('FILE_TYPES', list(FILE_TYPE_CATEGORIES.keys()))
        self.modules = self._get_list_env('MODULES', [])
        self.exclude_patterns = self._get_list_env('EXCLUDE_PATTERNS', EXCLUDE_PATTERNS)
        
        # Performance settings
        self.parallel_processing = self._get_bool_env('PARALLEL_PROCESSING', False)
        self.max_workers = int(os.getenv('MAX_WORKERS', '4'))
        
        # Logging settings
        self.log_level = os.getenv('LOG_LEVEL', LOG_LEVEL)
        self.verbose = self._get_bool_env('VERBOSE', False)
        self.show_progress = self._get_bool_env('SHOW_PROGRESS', SHOW_PROGRESS_BAR)
    
    def _get_bool_env(self, env_var: str, default: bool) -> bool:
        """Get boolean value from environment variable"""
        value = os.getenv(env_var, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def _get_list_env(self, env_var: str, default: List[str]) -> List[str]:
        """Get list value from environment variable (comma-separated)"""
        value = os.getenv(env_var)
        if value:
            return [item.strip() for item in value.split(',') if item.strip()]
        return default
    
    def validate(self):
        """Validate configuration values"""
        errors = []
        
        # Validate required paths
        if self.repo_path and not Path(self.repo_path).exists():
            errors.append(f"Repository path does not exist: {self.repo_path}")
        
        if self.csv_file and not Path(self.csv_file).exists():
            errors.append(f"CSV file does not exist: {self.csv_file}")
        
        # Validate numeric values
        if self.backup_retention_days < 0:
            errors.append("Backup retention days must be non-negative")
        
        if self.max_workers < 1:
            errors.append("Max workers must be at least 1")
        
        # Validate file types
        invalid_types = set(self.file_types) - set(FILE_TYPE_CATEGORIES.keys())
        if invalid_types:
            errors.append(f"Invalid file types: {invalid_types}")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions based on selected file types"""
        extensions = set()
        for file_type in self.file_types:
            if file_type in FILE_TYPE_CATEGORIES:
                extensions.update(FILE_TYPE_CATEGORIES[file_type])
        return list(extensions)
    
    def should_process_file_type(self, file_type: str) -> bool:
        """Check if a file type should be processed"""
        # Direct match
        if file_type in self.file_types:
            return True
        
        # Check if 'xml' is specified and this is an XML file type
        if 'xml' in self.file_types and file_type in ['views', 'data', 'demo', 'templates', 'reports', 'security']:
            return True
        
        return False
    
    def should_process_extension(self, extension: str) -> bool:
        """Check if a file extension should be processed"""
        return extension.lower() in self.get_supported_extensions()
    
    def get_oca_directories_for_type(self, file_type: str) -> List[str]:
        """Get OCA directories for a specific file type"""
        return OCA_DIRECTORIES.get(file_type, [])
    
    def get_processor_config(self) -> Dict:
        """Get configuration for processors"""
        return {
            'create_backups': self.create_backups,
            'validate_syntax': self.validate_syntax,
            'parallel_processing': self.parallel_processing,
            'max_workers': self.max_workers
        }
    
    def get_backup_config(self) -> Dict:
        """Get configuration for backup manager"""
        return {
            'backup_base_dir': self.backup_dir,
            'retention_days': self.backup_retention_days,
            'compress_backups': self.compress_backups
        }
    
    def get_file_finder_config(self) -> Dict:
        """Get configuration for file finder"""
        return {
            'oca_directories': OCA_DIRECTORIES,
            'exclude_patterns': self.exclude_patterns,
            'supported_extensions': self.get_supported_extensions()
        }
    
    def __str__(self):
        return f"""Renaming Configuration:
  Repository Path: {self.repo_path or 'Not set'}
  CSV File: {self.csv_file or 'Not set'}
  Backup Directory: {self.backup_dir}
  
  Processing:
    Create Backups: {self.create_backups}
    Validate Syntax: {self.validate_syntax}
    Interactive Mode: {self.interactive_mode}
    Dry Run: {self.dry_run}
    File Types: {', '.join(self.file_types)}
    
  Performance:
    Parallel Processing: {self.parallel_processing}
    Max Workers: {self.max_workers}
    
  Logging:
    Log Level: {self.log_level}
    Verbose: {self.verbose}
    Show Progress: {self.show_progress}
"""


# Global configuration instance
config = RenamingConfig()