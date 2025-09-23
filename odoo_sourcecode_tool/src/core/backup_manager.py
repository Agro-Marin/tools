"""
Unified backup manager for file operations
"""

import json
import logging
import shutil
import tarfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BackupSession:
    """Information about a backup session"""

    session_id: str
    timestamp: str
    directory: Path
    files_backed_up: list[str] = field(default_factory=list)
    total_size: int = 0
    compressed: bool = False


class BackupManager:
    """Unified backup manager for file operations"""

    def __init__(
        self,
        backup_dir: str = ".backups",
        compression: bool = False,
        keep_sessions: int = 10,
    ):
        """
        Initialize backup manager

        Args:
            backup_dir: Directory to store backups
            compression: Whether to compress backups
            keep_sessions: Number of backup sessions to keep
        """
        self.backup_dir = Path(backup_dir)
        self.compression = compression
        self.keep_sessions = keep_sessions
        self.current_session: BackupSession | None = None
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def start_session(self, description: str | None = None) -> Path:
        """Start a new backup session"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{timestamp}"
        if description:
            session_id = f"{session_id}_{description}"
        session_dir = self.backup_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        self.current_session = BackupSession(
            session_id=session_id, timestamp=timestamp, directory=session_dir
        )
        logger.info(f"Started backup session: {session_id}")
        return session_dir

    def backup_file(self, file_path: Path) -> Path | None:
        """Backup a single file"""
        if not self.current_session:
            self.start_session()

        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return None

        try:
            # Create relative path structure in backup
            if file_path.is_absolute():
                # For absolute paths, create a safe relative structure
                rel_path = (
                    Path(*file_path.parts[1:])
                    if len(file_path.parts) > 1
                    else file_path.name
                )
            else:
                rel_path = file_path

            backup_path = self.current_session.directory / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(file_path, backup_path)

            # Update session info
            self.current_session.files_backed_up.append(str(file_path))
            self.current_session.total_size += file_path.stat().st_size

            logger.debug(f"Backed up: {file_path} -> {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Error backing up {file_path}: {e}")
            return None

    def restore_file(
        self, original_path: Path, backup_path: Path | None = None
    ) -> bool:
        """Restore a file from backup"""
        try:
            if backup_path and backup_path.exists():
                # Restore from specific backup path
                shutil.copy2(backup_path, original_path)
                logger.info(f"Restored {original_path} from {backup_path}")
                return True

            # Try to find in current session
            if self.current_session:
                rel_path = (
                    Path(*original_path.parts[1:])
                    if original_path.is_absolute()
                    else original_path
                )
                session_backup = self.current_session.directory / rel_path
                if session_backup.exists():
                    shutil.copy2(session_backup, original_path)
                    logger.info(f"Restored {original_path} from current session")
                    return True

            logger.warning(f"No backup found for {original_path}")
            return False

        except Exception as e:
            logger.error(f"Error restoring {original_path}: {e}")
            return False

    def finalize_session(self) -> Path | None:
        """Finalize current backup session"""
        if not self.current_session:
            logger.warning("No active backup session")
            return None

        try:
            # Save session metadata
            metadata_file = self.current_session.directory / "session_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(asdict(self.current_session), f, indent=2, default=str)

            # Compress if requested
            if self.compression:
                archive_path = self._compress_session()
                if archive_path:
                    # Remove uncompressed directory
                    shutil.rmtree(self.current_session.directory)
                    self.current_session.compressed = True
                    logger.info(f"Compressed backup session to {archive_path}")
                    result = archive_path
                else:
                    result = self.current_session.directory
            else:
                result = self.current_session.directory

            # Clean old sessions
            self._cleanup_old_sessions()

            logger.info(f"Finalized backup session: {self.current_session.session_id}")
            self.current_session = None
            return result

        except Exception as e:
            logger.error(f"Error finalizing backup session: {e}")
            return None

    def _compress_session(self) -> Path | None:
        """Compress current session directory"""
        if not self.current_session:
            return None

        try:
            archive_path = self.backup_dir / f"{self.current_session.session_id}.tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(
                    self.current_session.directory,
                    arcname=self.current_session.session_id,
                )
            return archive_path
        except Exception as e:
            logger.error(f"Error compressing session: {e}")
            return None

    def _cleanup_old_sessions(self) -> None:
        """Remove old backup sessions beyond keep_sessions limit"""
        try:
            # Get all session directories and archives
            sessions = []
            for item in self.backup_dir.iterdir():
                if item.is_dir() and item.name.startswith("session_"):
                    sessions.append(item)
                elif item.suffix in [".tar", ".gz"] and item.stem.startswith(
                    "session_"
                ):
                    sessions.append(item)

            # Sort by modification time
            sessions.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Remove old sessions
            for session in sessions[self.keep_sessions :]:
                if session.is_dir():
                    shutil.rmtree(session)
                else:
                    session.unlink()
                logger.debug(f"Removed old backup: {session}")

        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {e}")

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all backup sessions"""
        sessions = []

        for item in self.backup_dir.iterdir():
            if item.is_dir() and item.name.startswith("session_"):
                # Try to load metadata
                metadata_file = item / "session_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, "r") as f:
                        sessions.append(json.load(f))
                else:
                    # Create basic info
                    sessions.append(
                        {
                            "session_id": item.name,
                            "directory": str(item),
                            "timestamp": datetime.fromtimestamp(
                                item.stat().st_mtime
                            ).isoformat(),
                        }
                    )
            elif item.suffix in [".tar", ".gz"] and item.stem.startswith("session_"):
                sessions.append(
                    {
                        "session_id": item.stem,
                        "archive": str(item),
                        "compressed": True,
                        "timestamp": datetime.fromtimestamp(
                            item.stat().st_mtime
                        ).isoformat(),
                    }
                )

        return sorted(sessions, key=lambda x: x.get("timestamp", ""), reverse=True)

    def restore_session(self, session_id: str) -> bool:
        """Restore all files from a backup session"""
        try:
            session_path = self.backup_dir / session_id
            archive_path = self.backup_dir / f"{session_id}.tar.gz"

            # Check if compressed archive exists
            if archive_path.exists():
                # Extract archive
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(self.backup_dir)
                session_path = self.backup_dir / session_id

            if not session_path.exists():
                logger.error(f"Backup session not found: {session_id}")
                return False

            # Load metadata
            metadata_file = session_path / "session_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)

                # Restore each file
                for file_path in metadata.get("files_backed_up", []):
                    original = Path(file_path)
                    rel_path = (
                        Path(*original.parts[1:])
                        if original.is_absolute()
                        else original
                    )
                    backup = session_path / rel_path

                    if backup.exists():
                        original.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup, original)
                        logger.info(f"Restored: {original}")

            # Clean up extracted directory if it was compressed
            if archive_path.exists() and session_path.exists():
                shutil.rmtree(session_path)

            return True

        except Exception as e:
            logger.error(f"Error restoring session {session_id}: {e}")
            return False

    def get_backup_for_file(
        self, file_path: Path, session_id: str | None = None
    ) -> Path | None:
        """Get backup path for a specific file"""
        if session_id:
            session_path = self.backup_dir / session_id
        elif self.current_session:
            session_path = self.current_session.directory
        else:
            return None

        rel_path = Path(*file_path.parts[1:]) if file_path.is_absolute() else file_path
        backup_path = session_path / rel_path

        return backup_path if backup_path.exists() else None
