"""
Base Processor for Field/Method Renaming
========================================

Provides common functionality for all file processors including
validation, backup creation, and error handling.
"""

import ast
import logging
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from utils.csv_reader import FieldChange

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """Status of processing operation"""

    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"
    NO_CHANGES = "no_changes"


@dataclass
class ProcessResult:
    """Result of processing a file"""

    file_path: Path
    status: ProcessingStatus
    changes_applied: int
    changes_details: list[str]
    error_message: str | None = None
    backup_path: Path | None = None
    original_content: str | None = None
    modified_content: str | None = None

    @property
    def is_success(self) -> bool:
        """Check if processing was successful"""
        return self.status == ProcessingStatus.SUCCESS

    @property
    def has_changes(self) -> bool:
        """Check if any changes were applied"""
        return self.changes_applied > 0

    def __str__(self):
        if self.status == ProcessingStatus.SUCCESS:
            return f"✅ {self.file_path}: {self.changes_applied} changes applied"
        elif self.status == ProcessingStatus.ERROR:
            return f"❌ {self.file_path}: {self.error_message}"
        elif self.status == ProcessingStatus.SKIPPED:
            return f"⏭️  {self.file_path}: Skipped"
        else:
            return f"ℹ️  {self.file_path}: No changes needed"


class ProcessingError(Exception):
    """Base exception for processing errors"""

    pass


class SyntaxValidationError(ProcessingError):
    """Exception for syntax validation errors"""

    pass


class BackupError(ProcessingError):
    """Exception for backup creation errors"""

    pass


class BaseProcessor(ABC):
    """Base class for all file processors"""

    def __init__(self, create_backups: bool = True, validate_syntax: bool = True):
        """
        Initialize base processor.

        Args:
            create_backups: Whether to create backups before modifying files
            validate_syntax: Whether to validate syntax after modifications
        """
        self.create_backups = create_backups
        self.validate_syntax = validate_syntax
        self.backup_manager = None  # Will be injected by main application

    def process_file(
        self, file_path: Path, changes: list[FieldChange]
    ) -> ProcessResult:
        """
        Process a file with the given changes.

        This is the main template method that coordinates the processing workflow.

        Args:
            file_path: Path to the file to process
            changes: List of changes to apply

        Returns:
            ProcessResult with details of the operation
        """
        logger.debug(f"Processing file: {file_path}")

        # Filter changes relevant to this file
        relevant_changes = self._filter_relevant_changes(file_path, changes)

        if not relevant_changes:
            logger.debug(f"No relevant changes for file: {file_path}")
            return ProcessResult(
                file_path=file_path,
                status=ProcessingStatus.NO_CHANGES,
                changes_applied=0,
                changes_details=[],
            )

        try:
            # Read original content
            original_content = self._read_file_content(file_path)

            # Validate original syntax if required
            if self.validate_syntax and not self._validate_original_syntax(
                file_path, original_content
            ):
                return ProcessResult(
                    file_path=file_path,
                    status=ProcessingStatus.SKIPPED,
                    changes_applied=0,
                    changes_details=[],
                    error_message="Original file has syntax errors",
                )

            # Create backup if required
            backup_path = None
            if self.create_backups:
                backup_path = self._create_backup(file_path, original_content)

            # Apply changes (implemented by subclasses)
            modified_content, applied_changes = self._apply_changes(
                file_path, original_content, relevant_changes
            )

            # Check if any changes were actually made
            if modified_content == original_content:
                logger.debug(f"No actual changes made to file: {file_path}")
                return ProcessResult(
                    file_path=file_path,
                    status=ProcessingStatus.NO_CHANGES,
                    changes_applied=0,
                    changes_details=[],
                    backup_path=backup_path,
                )

            # Validate modified syntax if required
            if self.validate_syntax and not self._validate_modified_syntax(
                file_path, modified_content
            ):
                error_msg = "Modified file has syntax errors, changes not applied"
                logger.error(f"{file_path}: {error_msg}")
                return ProcessResult(
                    file_path=file_path,
                    status=ProcessingStatus.ERROR,
                    changes_applied=0,
                    changes_details=[],
                    error_message=error_msg,
                    backup_path=backup_path,
                )

            # Write modified content
            self._write_file_content(file_path, modified_content)

            logger.info(
                f"Successfully processed {file_path}: {len(applied_changes)} changes applied"
            )

            return ProcessResult(
                file_path=file_path,
                status=ProcessingStatus.SUCCESS,
                changes_applied=len(applied_changes),
                changes_details=applied_changes,
                backup_path=backup_path,
                original_content=original_content,
                modified_content=modified_content,
            )

        except Exception as e:
            error_msg = f"Error processing file: {str(e)}"
            logger.error(f"{file_path}: {error_msg}")

            return ProcessResult(
                file_path=file_path,
                status=ProcessingStatus.ERROR,
                changes_applied=0,
                changes_details=[],
                error_message=error_msg,
            )

    @abstractmethod
    def _apply_changes(
        self, file_path: Path, content: str, changes: list[FieldChange]
    ) -> tuple[str, list[str]]:
        """
        Apply changes to file content.

        This method must be implemented by subclasses.

        Args:
            file_path: Path to the file being processed
            content: Original file content
            changes: List of changes to apply

        Returns:
            Tuple of (modified_content, list_of_applied_changes)
        """
        pass

    def _filter_relevant_changes(
        self, file_path: Path, changes: list[FieldChange]
    ) -> list[FieldChange]:
        """
        Filter changes that are relevant to the specific file.

        Base implementation returns all changes. Subclasses can override
        to implement more sophisticated filtering.

        Args:
            file_path: Path to the file being processed
            changes: All changes to consider

        Returns:
            List of relevant changes
        """
        return changes

    def _read_file_content(self, file_path: Path) -> str:
        """
        Read file content with proper encoding handling.

        Args:
            file_path: Path to the file to read

        Returns:
            File content as string

        Raises:
            ProcessingError: If file cannot be read
        """
        try:
            # Try UTF-8 first
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1
                logger.warning(f"UTF-8 decode failed for {file_path}, trying latin-1")
                return file_path.read_text(encoding="latin-1")
            except Exception as e:
                raise ProcessingError(f"Cannot read file {file_path}: {e}")
        except Exception as e:
            raise ProcessingError(f"Cannot read file {file_path}: {e}")

    def _write_file_content(self, file_path: Path, content: str):
        """
        Write content to file with proper encoding.

        Args:
            file_path: Path to the file to write
            content: Content to write

        Raises:
            ProcessingError: If file cannot be written
        """
        try:
            file_path.write_text(content, encoding="utf-8")
        except Exception as e:
            raise ProcessingError(f"Cannot write file {file_path}: {e}")

    def _create_backup(self, file_path: Path, content: str) -> Path | None:
        """
        Create backup of the original file.

        Args:
            file_path: Path to the original file
            content: Original content to backup

        Returns:
            Path to the backup file, or None if backup creation fails
        """
        if not self.backup_manager:
            logger.warning("No backup manager available, skipping backup creation")
            return None

        try:
            return self.backup_manager.create_backup(file_path, content)
        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")
            return None

    def _validate_original_syntax(self, file_path: Path, content: str) -> bool:
        """
        Validate syntax of original file content.

        Args:
            file_path: Path to the file
            content: File content to validate

        Returns:
            True if syntax is valid
        """
        if file_path.suffix == ".py":
            return self._validate_python_syntax(content)
        elif file_path.suffix == ".xml":
            return self._validate_xml_syntax(content)
        else:
            # For other file types, assume valid
            return True

    def _validate_modified_syntax(self, file_path: Path, content: str) -> bool:
        """
        Validate syntax of modified file content.

        Args:
            file_path: Path to the file
            content: Modified content to validate

        Returns:
            True if syntax is valid
        """
        return self._validate_original_syntax(file_path, content)

    def _validate_python_syntax(self, content: str) -> bool:
        """
        Validate Python syntax using AST parsing.

        Args:
            content: Python code to validate

        Returns:
            True if syntax is valid
        """
        try:
            ast.parse(content)
            return True
        except SyntaxError as e:
            logger.debug(f"Python syntax error: {e}")
            return False
        except Exception as e:
            logger.debug(f"Error validating Python syntax: {e}")
            return False

    def _validate_xml_syntax(self, content: str) -> bool:
        """
        Validate XML syntax using ElementTree parsing.

        Args:
            content: XML content to validate

        Returns:
            True if syntax is valid
        """
        try:
            ET.fromstring(content)
            return True
        except ET.ParseError as e:
            logger.debug(f"XML syntax error: {e}")
            return False
        except Exception as e:
            logger.debug(f"Error validating XML syntax: {e}")
            return False

    def get_supported_extensions(self) -> list[str]:
        """
        Get list of file extensions supported by this processor.

        Returns:
            List of supported extensions (e.g., ['.py', '.xml'])
        """
        return []

    def can_process_file(self, file_path: Path) -> bool:
        """
        Check if this processor can handle the given file.

        Args:
            file_path: Path to the file to check

        Returns:
            True if this processor can handle the file
        """
        supported_extensions = self.get_supported_extensions()
        if not supported_extensions:
            return True  # Processor handles all files

        return file_path.suffix.lower() in [ext.lower() for ext in supported_extensions]

    def set_backup_manager(self, backup_manager):
        """
        Set the backup manager instance.

        Args:
            backup_manager: BackupManager instance
        """
        self.backup_manager = backup_manager

    def get_processing_stats(self, results: list[ProcessResult]) -> dict[str, any]:
        """
        Generate statistics from processing results.

        Args:
            results: List of ProcessResult objects

        Returns:
            Dictionary with processing statistics
        """
        total_files = len(results)
        successful = len([r for r in results if r.is_success])
        failed = len([r for r in results if r.status == ProcessingStatus.ERROR])
        skipped = len([r for r in results if r.status == ProcessingStatus.SKIPPED])
        no_changes = len(
            [r for r in results if r.status == ProcessingStatus.NO_CHANGES]
        )

        total_changes = sum(r.changes_applied for r in results)

        return {
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "no_changes": no_changes,
            "total_changes_applied": total_changes,
            "success_rate": (successful / total_files * 100) if total_files > 0 else 0,
        }
