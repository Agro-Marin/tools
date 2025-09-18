"""
Backup Manager for Field/Method Renaming
========================================

Handles creation, management, and restoration of file backups
during the renaming process.
"""

import hashlib
import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class BackupInfo:
    """Information about a backup"""

    original_path: Path
    backup_path: Path
    timestamp: datetime
    file_size: int
    checksum: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "original_path": str(self.original_path),
            "backup_path": str(self.backup_path),
            "timestamp": self.timestamp.isoformat(),
            "file_size": self.file_size,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackupInfo":
        """Create from dictionary"""
        return cls(
            original_path=Path(data["original_path"]),
            backup_path=Path(data["backup_path"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            file_size=data["file_size"],
            checksum=data["checksum"],
        )


class BackupError(Exception):
    """Exception raised for backup-related errors"""

    pass


class BackupManager:
    """Manager for creating and restoring file backups"""

    def __init__(
        self,
        backup_base_dir: str | None = None,
        retention_days: int = 30,
        compress_backups: bool = False,
    ):
        """
        Initialize backup manager.

        Args:
            backup_base_dir: Base directory for backups (defaults to .backups in current dir)
            retention_days: Number of days to keep backups
            compress_backups: Whether to compress backup files
        """
        if backup_base_dir:
            self.backup_base_dir = Path(backup_base_dir)
        else:
            self.backup_base_dir = Path.cwd() / ".backups"

        self.retention_days = retention_days
        self.compress_backups = compress_backups
        self.current_session_dir = None
        self.backup_manifest = {}

        # Ensure backup directory exists
        self.backup_base_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Initialized BackupManager with base dir: {self.backup_base_dir}")

    def start_backup_session(self, session_name: str | None = None) -> Path:
        """
        Start a new backup session.

        Args:
            session_name: Optional name for the session (defaults to timestamp)

        Returns:
            Path to the session directory
        """
        if not session_name:
            session_name = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.current_session_dir = self.backup_base_dir / session_name
        self.current_session_dir.mkdir(parents=True, exist_ok=True)

        # Initialize manifest for this session
        self.backup_manifest = {
            "session_name": session_name,
            "created_at": datetime.now().isoformat(),
            "backups": [],
        }

        logger.info(f"Started backup session: {self.current_session_dir}")
        return self.current_session_dir

    def create_backup(self, file_path: Path, content: str | None = None) -> Path:
        """
        Create a backup of a file.

        Args:
            file_path: Path to the file to backup
            content: Optional content to backup (if None, reads from file)

        Returns:
            Path to the backup file

        Raises:
            BackupError: If backup creation fails
        """
        if not self.current_session_dir:
            self.start_backup_session()

        try:
            # Read content if not provided
            if content is None:
                if not file_path.exists():
                    raise BackupError(f"File does not exist: {file_path}")
                content = file_path.read_text(encoding="utf-8")

            # Create backup file path maintaining directory structure
            relative_path = self._get_relative_backup_path(file_path)
            backup_path = self.current_session_dir / relative_path

            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Write backup content
            backup_path.write_text(content, encoding="utf-8")

            # Calculate checksum
            checksum = self._calculate_checksum(content)

            # Create backup info
            backup_info = BackupInfo(
                original_path=file_path,
                backup_path=backup_path,
                timestamp=datetime.now(),
                file_size=len(content.encode("utf-8")),
                checksum=checksum,
            )

            # Add to manifest
            self.backup_manifest["backups"].append(backup_info.to_dict())

            # Save manifest
            self._save_manifest()

            logger.debug(f"Created backup: {file_path} → {backup_path}")
            return backup_path

        except Exception as e:
            raise BackupError(f"Failed to create backup for {file_path}: {e}")

    def create_batch_backup(self, file_paths: list[Path]) -> dict[Path, Path]:
        """
        Create backups for multiple files.

        Args:
            file_paths: List of file paths to backup

        Returns:
            Dictionary mapping original paths to backup paths
        """
        if not self.current_session_dir:
            self.start_backup_session()

        backup_map = {}
        failed_backups = []

        for file_path in file_paths:
            try:
                backup_path = self.create_backup(file_path)
                backup_map[file_path] = backup_path
            except BackupError as e:
                logger.warning(f"Failed to backup {file_path}: {e}")
                failed_backups.append(file_path)

        logger.info(
            f"Batch backup completed: {len(backup_map)} successful, {len(failed_backups)} failed"
        )

        if failed_backups:
            logger.warning(f"Failed backups: {failed_backups}")

        return backup_map

    def restore_backup(
        self, backup_path: Path, target_path: Path | None = None
    ) -> bool:
        """
        Restore a file from backup.

        Args:
            backup_path: Path to the backup file
            target_path: Target path for restoration (defaults to original path from manifest)

        Returns:
            True if restoration was successful
        """
        try:
            if not backup_path.exists():
                logger.error(f"Backup file does not exist: {backup_path}")
                return False

            # Find original path from manifest if target not specified
            if not target_path:
                target_path = self._get_original_path_from_backup(backup_path)
                if not target_path:
                    logger.error(
                        f"Could not determine original path for backup: {backup_path}"
                    )
                    return False

            # Read backup content
            backup_content = backup_path.read_text(encoding="utf-8")

            # Verify checksum if available
            if not self._verify_backup_integrity(backup_path, backup_content):
                logger.warning(f"Backup integrity check failed for: {backup_path}")

            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Restore content
            target_path.write_text(backup_content, encoding="utf-8")

            logger.info(f"Restored backup: {backup_path} → {target_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore backup {backup_path}: {e}")
            return False

    def restore_session(self, session_dir: Path) -> dict[str, bool]:
        """
        Restore all files from a backup session.

        Args:
            session_dir: Path to the session directory

        Returns:
            Dictionary mapping file paths to restoration success status
        """
        restoration_results = {}

        try:
            # Load session manifest
            manifest_path = session_dir / "backup_manifest.json"
            if not manifest_path.exists():
                logger.error(f"No manifest found in session directory: {session_dir}")
                return restoration_results

            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            # Restore each backup
            for backup_dict in manifest.get("backups", []):
                backup_info = BackupInfo.from_dict(backup_dict)
                success = self.restore_backup(
                    backup_info.backup_path, backup_info.original_path
                )
                restoration_results[str(backup_info.original_path)] = success

            logger.info(
                f"Session restoration completed: {len(restoration_results)} files processed"
            )

        except Exception as e:
            logger.error(f"Failed to restore session {session_dir}: {e}")

        return restoration_results

    def list_backup_sessions(self) -> list[dict]:
        """
        List all available backup sessions.

        Returns:
            List of session information dictionaries
        """
        sessions = []

        for session_dir in self.backup_base_dir.iterdir():
            if session_dir.is_dir():
                manifest_path = session_dir / "backup_manifest.json"

                if manifest_path.exists():
                    try:
                        with open(manifest_path, "r") as f:
                            manifest = json.load(f)

                        sessions.append(
                            {
                                "session_name": manifest.get(
                                    "session_name", session_dir.name
                                ),
                                "session_dir": session_dir,
                                "created_at": manifest.get("created_at"),
                                "backup_count": len(manifest.get("backups", [])),
                                "total_size": sum(
                                    b["file_size"] for b in manifest.get("backups", [])
                                ),
                            }
                        )
                    except Exception as e:
                        logger.warning(
                            f"Could not read manifest for session {session_dir}: {e}"
                        )
                else:
                    # Session without manifest
                    sessions.append(
                        {
                            "session_name": session_dir.name,
                            "session_dir": session_dir,
                            "created_at": None,
                            "backup_count": 0,
                            "total_size": 0,
                        }
                    )

        # Sort by creation time (newest first)
        sessions.sort(key=lambda s: s.get("created_at") or "", reverse=True)

        return sessions

    def cleanup_old_backups(self, force: bool = False) -> int:
        """
        Clean up old backup sessions based on retention policy.

        Args:
            force: Force cleanup even if retention period not exceeded

        Returns:
            Number of sessions cleaned up
        """
        cleanup_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        sessions = self.list_backup_sessions()

        for session in sessions:
            session_dir = session["session_dir"]
            created_at = session.get("created_at")

            should_cleanup = False

            if force:
                should_cleanup = True
            elif created_at:
                session_date = datetime.fromisoformat(created_at)
                if session_date < cutoff_date:
                    should_cleanup = True
            else:
                # No creation date, check directory modification time
                dir_mtime = datetime.fromtimestamp(session_dir.stat().st_mtime)
                if dir_mtime < cutoff_date:
                    should_cleanup = True

            if should_cleanup:
                try:
                    shutil.rmtree(session_dir)
                    cleanup_count += 1
                    logger.info(f"Cleaned up old backup session: {session_dir}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup session {session_dir}: {e}")

        logger.info(f"Cleanup completed: {cleanup_count} sessions removed")
        return cleanup_count

    def get_backup_statistics(self) -> dict:
        """
        Get statistics about backup storage.

        Returns:
            dictionary with backup statistics
        """
        sessions = self.list_backup_sessions()

        total_sessions = len(sessions)
        total_backups = sum(s["backup_count"] for s in sessions)
        total_size = sum(s["total_size"] for s in sessions)

        # Calculate disk usage
        try:
            disk_usage = sum(
                f.stat().st_size for f in self.backup_base_dir.rglob("*") if f.is_file()
            )
        except Exception:
            disk_usage = 0

        return {
            "backup_base_dir": str(self.backup_base_dir),
            "total_sessions": total_sessions,
            "total_backups": total_backups,
            "total_logical_size": total_size,
            "total_disk_usage": disk_usage,
            "retention_days": self.retention_days,
            "current_session": (
                str(self.current_session_dir) if self.current_session_dir else None
            ),
        }

    def _get_relative_backup_path(self, file_path: Path) -> Path:
        """
        Get relative backup path maintaining directory structure.

        Args:
            file_path: Original file path

        Returns:
            Relative path for backup
        """
        # Convert absolute path to relative path suitable for backup
        if file_path.is_absolute():
            # Remove leading slash and drive letter (Windows)
            parts = file_path.parts
            if parts[0] == "/" or ":" in parts[0]:
                parts = parts[1:]
            return Path(*parts)
        else:
            return file_path

    def _calculate_checksum(self, content: str) -> str:
        """
        Calculate SHA-256 checksum of content.

        Args:
            content: Content to checksum

        Returns:
            Hexadecimal checksum
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _verify_backup_integrity(self, backup_path: Path, content: str) -> bool:
        """
        Verify backup integrity using checksum.

        Args:
            backup_path: Path to backup file
            content: Content to verify

        Returns:
            True if integrity check passes
        """
        # Find backup info in manifest
        for backup_dict in self.backup_manifest.get("backups", []):
            if Path(backup_dict["backup_path"]) == backup_path:
                expected_checksum = backup_dict["checksum"]
                actual_checksum = self._calculate_checksum(content)
                return expected_checksum == actual_checksum

        # No checksum found in manifest
        return True

    def _get_original_path_from_backup(self, backup_path: Path) -> Path | None:
        """
        Get original file path from backup path using manifest.

        Args:
            backup_path: Path to backup file

        Returns:
            Original file path or None if not found
        """
        # Try current session first
        for backup_dict in self.backup_manifest.get("backups", []):
            if Path(backup_dict["backup_path"]) == backup_path:
                return Path(backup_dict["original_path"])

        # Try to find in other session manifests
        for session_dir in self.backup_base_dir.iterdir():
            if session_dir.is_dir() and session_dir != self.current_session_dir:
                manifest_path = session_dir / "backup_manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, "r") as f:
                            manifest = json.load(f)

                        for backup_dict in manifest.get("backups", []):
                            if Path(backup_dict["backup_path"]) == backup_path:
                                return Path(backup_dict["original_path"])
                    except Exception:
                        continue

        return None

    def _save_manifest(self):
        """Save backup manifest to disk"""
        if self.current_session_dir:
            manifest_path = self.current_session_dir / "backup_manifest.json"
            try:
                with open(manifest_path, "w") as f:
                    json.dump(self.backup_manifest, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to save backup manifest: {e}")

    def finalize_session(self) -> Path | None:
        """
        Finalize the current backup session.

        Returns:
            Path to the session directory
        """
        if self.current_session_dir:
            self._save_manifest()
            logger.info(f"Finalized backup session: {self.current_session_dir}")

            session_dir = self.current_session_dir
            self.current_session_dir = None
            self.backup_manifest = {}

            return session_dir

        return None
