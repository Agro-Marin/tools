"""
Base processor interface for file processing operations
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """Status of processing operation"""

    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"
    NO_CHANGES = "no_changes"


@dataclass
class ProcessResult:
    """Result of a processing operation"""

    file_path: Path
    status: ProcessingStatus
    changes_applied: int = 0
    changes_details: list[dict[str, Any]] = None
    error_message: str | None = None
    backup_path: Path | None = None

    @property
    def is_success(self) -> bool:
        """Check if processing was successful"""
        return self.status in [ProcessingStatus.SUCCESS, ProcessingStatus.NO_CHANGES]

    def __str__(self) -> str:
        """String representation"""
        if self.status == ProcessingStatus.SUCCESS:
            return f"✓ {self.file_path.name}: {self.changes_applied} changes applied"
        elif self.status == ProcessingStatus.NO_CHANGES:
            return f"= {self.file_path.name}: No changes needed"
        elif self.status == ProcessingStatus.SKIPPED:
            return f"⊝ {self.file_path.name}: Skipped"
        else:
            return f"✗ {self.file_path.name}: {self.error_message}"


class BaseProcessor(ABC):
    """Abstract base class for all file processors"""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
    ):
        """
        Initialize processor

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def can_process(self, file_path: Path) -> bool:
        """
        Check if this processor can handle the given file

        Args:
            file_path: Path to file

        Returns:
            True if processor can handle this file type
        """
        pass

    @abstractmethod
    def process_file(
        self,
        file_path: Path,
        **kwargs,
    ) -> ProcessResult:
        """
        Process a single file

        Args:
            file_path: Path to file to process
            **kwargs: Additional processing parameters

        Returns:
            ProcessResult with operation details
        """
        pass

    @abstractmethod
    def validate_file(
        self,
        file_path: Path,
    ) -> bool:
        """
        Validate file syntax/structure after processing

        Args:
            file_path: Path to file to validate

        Returns:
            True if file is valid
        """
        pass

    def read_file(
        self,
        file_path: Path,
    ) -> str:
        """
        Read file content

        Args:
            file_path: Path to file

        Returns:
            File content as string
        """
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {e}")
            raise

    def write_file(
        self,
        file_path: Path,
        content: str,
    ) -> bool:
        """
        Write content to file

        Args:
            file_path: Path to file
            content: Content to write

        Returns:
            True if successful
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            self.logger.error(f"Error writing {file_path}: {e}")
            return False

    def process_batch(
        self,
        file_paths: list[Path],
        **kwargs,
    ) -> list[ProcessResult]:
        """
        Process multiple files

        Args:
            file_paths: List of file paths
            **kwargs: Additional processing parameters

        Returns:
            List of ProcessResult objects
        """
        results = []
        for file_path in file_paths:
            if self.can_process(file_path):
                result = self.process_file(file_path, **kwargs)
                results.append(result)
            else:
                results.append(
                    ProcessResult(
                        file_path=file_path,
                        status=ProcessingStatus.SKIPPED,
                        error_message="File type not supported by this processor",
                    )
                )
        return results
