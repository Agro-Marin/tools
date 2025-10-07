"""
CSV Reader for Field/Method Changes
===================================

Handles reading, validation, and parsing of CSV files containing
field and method rename records for application.
"""

import csv
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FieldChange:
    """Represents a field or method change with full context from CSV enhanced structure"""

    # Core fields
    old_name: str
    new_name: str
    module: str
    model: str
    change_type: str  # 'field' or 'method'

    # Enhanced CSV fields
    change_id: str = ""
    change_scope: str = "declaration"
    impact_type: str = "primary"
    context: str = ""
    confidence: float = 0.0
    parent_change_id: str = ""
    validation_status: str = "pending"

    # Internal tracking fields
    applied: bool = False
    error_message: str = ""

    def can_be_applied(self) -> bool:
        """Check if this change can be applied based on validation status"""
        return (
            self.validation_status in ["approved", "auto_approved"]
            and not self.applied
        )

    def is_primary(self) -> bool:
        """Check if this is a primary change (declaration in base module)"""
        return self.impact_type == "primary"

    def is_extension_declaration(self) -> bool:
        """Check if this is a declaration in an extension module"""
        return (
            self.impact_type == "inheritance"
            and self.change_scope == "declaration"
        )

    @property
    def is_field(self) -> bool:
        """Check if this is a field change"""
        return self.change_type == "field"

    @property
    def is_method(self) -> bool:
        """Check if this is a method change"""
        return self.change_type == "method"

    def __str__(self):
        base = f"{self.old_name} → {self.new_name} ({self.module}.{self.model})"
        if self.context:
            base += f" in {self.context}"
        return f"[{self.change_id}] {base}" if self.change_id else base


class CSVValidationError(Exception):
    """Exception raised for CSV validation errors"""

    pass


class CSVReader:
    """Reader for CSV files with enhanced structure"""

    # Required CSV headers for enhanced format
    REQUIRED_HEADERS = [
        "change_id", "old_name", "new_name", "item_type", "module", "model",
        "change_scope", "impact_type", "context", "confidence",
        "parent_change_id", "validation_status"
    ]

    # Fields that cannot be empty (others can be empty strings)
    MANDATORY_FIELDS = [
        "change_id", "old_name", "new_name", "item_type", "module", "model",
        "change_scope", "impact_type", "validation_status"
    ]

    def __init__(self, csv_file_path: str):
        """
        Initialize CSV reader.

        Args:
            csv_file_path: Path to the CSV file
        """
        self.csv_file_path = Path(csv_file_path)
        self.encoding = "utf-8"
        self.changes = []

    def load_changes(self) -> list[FieldChange]:
        """
        Load only approved changes from CSV enhanced file.

        Returns:
            List of approved FieldChange objects

        Raises:
            CSVValidationError: If CSV is invalid or malformed
            FileNotFoundError: If CSV file doesn't exist
        """
        if not self.csv_file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_file_path}")

        try:
            with open(
                self.csv_file_path, "r", encoding=self.encoding, newline=""
            ) as csvfile:
                reader = csv.DictReader(csvfile)

                # Validate headers
                self._validate_csv_headers(reader.fieldnames)

                changes = []
                for row_num, row in enumerate(
                    reader, start=2
                ):  # Start at 2 because header is row 1
                    # Clean and validate row
                    cleaned_row = self._clean_csv_row(row)
                    self._validate_csv_row(cleaned_row, row_num)

                    # Create FieldChange object with enhanced fields
                    change = FieldChange(
                        # Core fields
                        old_name=cleaned_row["old_name"],
                        new_name=cleaned_row["new_name"],
                        module=cleaned_row["module"],
                        model=cleaned_row["model"],
                        change_type=cleaned_row["item_type"],

                        # Enhanced fields
                        change_id=cleaned_row["change_id"],
                        change_scope=cleaned_row["change_scope"],
                        impact_type=cleaned_row["impact_type"],
                        context=cleaned_row.get("context", ""),
                        confidence=float(cleaned_row["confidence"]) if cleaned_row.get("confidence") else 0.0,
                        parent_change_id=cleaned_row.get("parent_change_id", ""),
                        validation_status=cleaned_row["validation_status"]
                    )

                    # Only add if can be applied
                    if change.can_be_applied():
                        changes.append(change)

                self.changes = changes
                logger.info(f"Loaded {len(changes)} approved changes from {self.csv_file_path}")

                return changes

        except Exception as e:
            if isinstance(e, (CSVValidationError, FileNotFoundError)):
                raise
            else:
                raise CSVValidationError(
                    f"Error reading CSV file {self.csv_file_path}: {e}"
                )

    def _validate_csv_headers(self, headers: list[str]):
        """Validate CSV headers"""
        if not headers:
            raise CSVValidationError("CSV file is empty or has no headers")

        missing_headers = set(self.REQUIRED_HEADERS) - set(headers)
        if missing_headers:
            raise CSVValidationError(
                f"Missing required headers: {', '.join(missing_headers)}"
            )

        logger.debug(f"CSV headers validated: {headers}")

    def _clean_csv_row(self, row: dict[str, str]) -> dict[str, str]:
        """Clean CSV row data"""
        cleaned = {}
        for header in self.REQUIRED_HEADERS:
            value = row.get(header, "").strip()
            cleaned[header] = value
        return cleaned

    def _validate_csv_row(self, row: dict[str, str], row_num: int):
        """
        Validate CSV row data.

        Args:
            row: Cleaned row data
            row_num: Row number for error reporting

        Raises:
            CSVValidationError: If row is invalid
        """
        # Check mandatory fields (others can be empty)
        for field in self.MANDATORY_FIELDS:
            if not row.get(field):
                raise CSVValidationError(
                    f"Row {row_num}: Missing or empty mandatory field '{field}'"
                )

        # Check for identical old and new names
        if row["old_name"] == row["new_name"]:
            raise CSVValidationError(
                f"Row {row_num}: old_name and new_name are identical: {row['old_name']}"
            )

        # Validate naming patterns
        self._validate_naming_patterns(row, row_num)

    def _validate_naming_patterns(self, row: dict[str, str], row_num: int):
        """Validate that field/method names follow proper patterns"""
        old_name = row["old_name"]
        new_name = row["new_name"]

        # Check for invalid characters
        invalid_chars = set("!@#$%^&*()+=[]{}|\\:\";'<>?,./")

        for name, name_type in [(old_name, "old_name"), (new_name, "new_name")]:
            if any(char in invalid_chars for char in name):
                raise CSVValidationError(
                    f"Row {row_num}: {name_type} contains invalid characters: {name}"
                )

            if name.startswith(" ") or name.endswith(" "):
                raise CSVValidationError(
                    f"Row {row_num}: {name_type} has leading/trailing spaces: '{name}'"
                )

            if "__" in name and not (name.startswith("__") and name.endswith("__")):
                logger.warning(
                    f"Row {row_num}: {name_type} contains double underscores: {name}"
                )

