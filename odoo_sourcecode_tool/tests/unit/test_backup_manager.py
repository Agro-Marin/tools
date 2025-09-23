"""
Unit tests for backup manager
"""

import json
from pathlib import Path

import pytest
from core.backup_manager import BackupManager, BackupSession


class TestBackupManager:
    """Test backup manager functionality"""

    def test_initialization(self, tmp_path):
        """Test backup manager initialization"""
        backup_dir = tmp_path / "backups"
        manager = BackupManager(backup_dir=str(backup_dir))

        assert manager.backup_dir == backup_dir
        assert backup_dir.exists()
        assert manager.current_session is None

    def test_start_session(self, tmp_path):
        """Test starting a backup session"""
        manager = BackupManager(backup_dir=str(tmp_path / "backups"))

        session_dir = manager.start_session("test_session")

        assert session_dir.exists()
        assert manager.current_session is not None
        assert "test_session" in manager.current_session.session_id
        assert manager.current_session.directory == session_dir

    def test_backup_file(self, tmp_path):
        """Test backing up a file"""
        manager = BackupManager(backup_dir=str(tmp_path / "backups"))

        # Create a test file
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")

        # Start session and backup file
        manager.start_session()
        backup_path = manager.backup_file(test_file)

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == "test content"
        assert str(test_file) in manager.current_session.files_backed_up

    def test_backup_nonexistent_file(self, tmp_path):
        """Test backing up a non-existent file"""
        manager = BackupManager(backup_dir=str(tmp_path / "backups"))
        manager.start_session()

        nonexistent = tmp_path / "nonexistent.txt"
        backup_path = manager.backup_file(nonexistent)

        assert backup_path is None

    def test_restore_file(self, tmp_path):
        """Test restoring a file from backup"""
        manager = BackupManager(backup_dir=str(tmp_path / "backups"))

        # Create and backup a file
        test_file = tmp_path / "restore_test.txt"
        test_file.write_text("original content")

        manager.start_session()
        backup_path = manager.backup_file(test_file)

        # Modify the original file
        test_file.write_text("modified content")

        # Restore from backup
        restored = manager.restore_file(test_file, backup_path)

        assert restored is True
        assert test_file.read_text() == "original content"

    def test_restore_from_current_session(self, tmp_path):
        """Test restoring from current session without specific path"""
        manager = BackupManager(backup_dir=str(tmp_path / "backups"))

        test_file = tmp_path / "session_restore.txt"
        test_file.write_text("session content")

        manager.start_session()
        manager.backup_file(test_file)

        # Modify file
        test_file.write_text("changed")

        # Restore without specifying backup path
        restored = manager.restore_file(test_file)

        assert restored is True
        assert test_file.read_text() == "session content"

    def test_finalize_session(self, tmp_path):
        """Test finalizing a backup session"""
        manager = BackupManager(backup_dir=str(tmp_path / "backups"))

        # Create session with backups
        test_file = tmp_path / "final_test.txt"
        test_file.write_text("content")

        manager.start_session()
        manager.backup_file(test_file)
        session_id = manager.current_session.session_id

        # Finalize session
        result = manager.finalize_session()

        assert result is not None
        assert manager.current_session is None

        # Check metadata was saved
        metadata_file = result / "session_metadata.json"
        assert metadata_file.exists()

        with open(metadata_file) as f:
            metadata = json.load(f)
            assert metadata["session_id"] == session_id
            assert len(metadata["files_backed_up"]) == 1

    def test_session_compression(self, tmp_path):
        """Test session compression"""
        manager = BackupManager(backup_dir=str(tmp_path / "backups"), compression=True)

        # Create session with files
        test_file = tmp_path / "compress_test.txt"
        test_file.write_text("compress me")

        manager.start_session("compress_session")
        manager.backup_file(test_file)
        session_id = manager.current_session.session_id

        # Finalize with compression
        result = manager.finalize_session()

        # Check that archive was created
        assert result.suffix == ".gz"
        assert result.exists()

        # Original directory should be removed
        session_dir = tmp_path / "backups" / session_id
        assert not session_dir.exists()

    def test_list_sessions(self, tmp_path):
        """Test listing backup sessions"""
        manager = BackupManager(backup_dir=str(tmp_path / "backups"))

        # Create multiple sessions
        for i in range(3):
            manager.start_session(f"session_{i}")
            test_file = tmp_path / f"file_{i}.txt"
            test_file.write_text(f"content {i}")
            manager.backup_file(test_file)
            manager.finalize_session()

        # List sessions
        sessions = manager.list_sessions()

        assert len(sessions) == 3
        assert all("session_id" in s for s in sessions)

    def test_cleanup_old_sessions(self, tmp_path):
        """Test cleaning up old sessions"""
        manager = BackupManager(backup_dir=str(tmp_path / "backups"), keep_sessions=2)

        # Create 5 sessions
        for i in range(5):
            manager.start_session(f"old_session_{i}")
            test_file = tmp_path / f"old_file_{i}.txt"
            test_file.write_text(f"old content {i}")
            manager.backup_file(test_file)
            manager.finalize_session()

        # Cleanup should happen automatically on finalize
        # Only 2 most recent should remain
        sessions = manager.list_sessions()
        assert len(sessions) == 2

    def test_restore_session(self, tmp_path):
        """Test restoring an entire session"""
        manager = BackupManager(backup_dir=str(tmp_path / "backups"))

        # Create test files
        files = []
        for i in range(3):
            test_file = tmp_path / f"restore_{i}.txt"
            test_file.write_text(f"original {i}")
            files.append(test_file)

        # Backup all files
        manager.start_session("full_restore")
        for f in files:
            manager.backup_file(f)
        session_id = manager.current_session.session_id
        manager.finalize_session()

        # Modify all files
        for i, f in enumerate(files):
            f.write_text(f"modified {i}")

        # Restore session
        restored = manager.restore_session(session_id)

        assert restored is True
        # Check all files were restored
        for i, f in enumerate(files):
            assert f.read_text() == f"original {i}"

    def test_get_backup_for_file(self, tmp_path):
        """Test getting backup path for specific file"""
        manager = BackupManager(backup_dir=str(tmp_path / "backups"))

        test_file = tmp_path / "specific.txt"
        test_file.write_text("specific content")

        manager.start_session()
        manager.backup_file(test_file)

        # Get backup path
        backup_path = manager.get_backup_for_file(test_file)

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == "specific content"

    def test_multiple_sessions_no_interference(self, tmp_path):
        """Test that multiple sessions don't interfere"""
        manager = BackupManager(backup_dir=str(tmp_path / "backups"))

        test_file = tmp_path / "multi_session.txt"

        # First session
        test_file.write_text("version 1")
        manager.start_session("session1")
        manager.backup_file(test_file)
        session1_id = manager.current_session.session_id
        manager.finalize_session()

        # Second session with different content
        test_file.write_text("version 2")
        manager.start_session("session2")
        manager.backup_file(test_file)
        manager.finalize_session()

        # Restore from first session
        manager.restore_session(session1_id)
        assert test_file.read_text() == "version 1"
