"""
Configuration settings for the Field/Method Change Detector
===========================================================

Default configuration values and environment-specific settings.
"""

import os
from pathlib import Path

# Default confidence thresholds
DEFAULT_CONFIDENCE_THRESHOLD = 0.75
AUTO_APPROVE_THRESHOLD = 0.90
MINIMUM_REVIEW_THRESHOLD = 0.50

# Scoring weights for confidence calculation
SCORING_WEIGHTS = {
    "signature_match": 0.40,  # Exact signature match
    "naming_rule": 0.30,  # Follows naming rule
    "convention_compliance": 0.20,  # Follows conventions
    "api_consistency": 0.10,  # API style consistency
}

# Default file paths
DEFAULT_OUTPUT_CSV = "odoo_field_changes_detected.csv"
DEFAULT_REPORT_FILE = "confidence_report.json"

# Git configuration
DEFAULT_REPO_PATH = None  # Auto-detect from JSON location
GIT_DIFF_CONTEXT_LINES = 3

# Interactive mode settings
INTERACTIVE_BAR_LENGTH = 30
INTERACTIVE_COLORS = {
    "pass": "\033[92m",  # Green
    "fail": "\033[93m",  # Yellow
    "error": "\033[91m",  # Red
    "reset": "\033[0m",  # Reset
    "bold": "\033[1m",  # Bold
}

# CSV output settings
CSV_HEADERS = ["old_name", "new_name", "item_type", "module", "model"]
CSV_ENCODING = "utf-8"

# Valid item types for validation
VALID_ITEM_TYPES = {"field", "method"}

# File filtering settings
PYTHON_FILE_EXTENSIONS = [".py"]
XML_FILE_EXTENSIONS = [".xml"]
SUPPORTED_FILE_TYPES = PYTHON_FILE_EXTENSIONS + XML_FILE_EXTENSIONS

# Model file categories to analyze
ANALYZE_CATEGORIES = ["models", "wizards"]  # From modified_modules.json

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Progress reporting
SHOW_PROGRESS_BAR = True
PROGRESS_UPDATE_INTERVAL = 10  # Every N files


class Config:
    """Configuration manager with environment variable support"""

    def __init__(self):
        self.confidence_threshold = float(
            os.getenv("CONFIDENCE_THRESHOLD", DEFAULT_CONFIDENCE_THRESHOLD)
        )
        self.auto_approve_threshold = float(
            os.getenv("AUTO_APPROVE_THRESHOLD", AUTO_APPROVE_THRESHOLD)
        )
        self.minimum_review_threshold = float(
            os.getenv("MINIMUM_REVIEW_THRESHOLD", MINIMUM_REVIEW_THRESHOLD)
        )

        self.interactive_mode = os.getenv("INTERACTIVE_MODE", "false").lower() == "true"
        self.batch_mode = os.getenv("BATCH_MODE", "false").lower() == "true"
        self.verbose = os.getenv("VERBOSE", "false").lower() == "true"

        self.repo_path = os.getenv("REPO_PATH", DEFAULT_REPO_PATH)
        self.output_csv = os.getenv("OUTPUT_CSV", DEFAULT_OUTPUT_CSV)
        self.report_file = os.getenv("REPORT_FILE", DEFAULT_REPORT_FILE)

        self.log_level = os.getenv("LOG_LEVEL", LOG_LEVEL)
        self.show_progress = (
            os.getenv("SHOW_PROGRESS", str(SHOW_PROGRESS_BAR)).lower() == "true"
        )

    def validate(self):
        """Validate configuration values"""
        if not 0 <= self.confidence_threshold <= 1:
            raise ValueError("Confidence threshold must be between 0 and 1")

        if not 0 <= self.auto_approve_threshold <= 1:
            raise ValueError("Auto-approve threshold must be between 0 and 1")

        if not 0 <= self.minimum_review_threshold <= 1:
            raise ValueError("Minimum review threshold must be between 0 and 1")

        if self.auto_approve_threshold <= self.confidence_threshold:
            raise ValueError(
                "Auto-approve threshold must be higher than confidence threshold"
            )

    def get_repo_path_from_json(self, json_file_path: str) -> str:
        """Auto-detect repository path from JSON file location"""
        if self.repo_path:
            return self.repo_path

        # Assume repo is parent directory of tools/
        json_path = Path(json_file_path)
        tools_dir = json_path.parent

        # Look for .git directory going up the tree
        current = tools_dir
        while current != current.parent:
            if (current / ".git").exists():
                return str(current)
            current = current.parent

        # Default to tools parent directory
        return str(tools_dir.parent)

    def __str__(self):
        return f"""Configuration:
  Confidence Threshold: {self.confidence_threshold:.1%}
  Auto-approve Threshold: {self.auto_approve_threshold:.1%}
  Minimum Review Threshold: {self.minimum_review_threshold:.1%}
  Interactive Mode: {self.interactive_mode}
  Batch Mode: {self.batch_mode}
  Verbose: {self.verbose}
  Repository Path: {self.repo_path or 'Auto-detect'}
  Output CSV: {self.output_csv}
  Report File: {self.report_file}
"""


# Global configuration instance
config = Config()
