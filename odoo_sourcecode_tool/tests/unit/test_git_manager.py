"""
Unit tests for Git manager
"""

import subprocess
from pathlib import Path

import pytest
from core.git_manager import CommitInfo, GitManager


class TestGitManager:
    """Test Git manager functionality"""

    def test_initialize_repo(self, test_repo):
        """Test Git repository initialization"""
        git_manager = GitManager(test_repo)

        assert git_manager.repo_path == test_repo
        assert git_manager.repo is not None

    def test_invalid_repo(self, tmp_path):
        """Test initialization with invalid repository"""
        non_repo_path = tmp_path / "not_a_repo"
        non_repo_path.mkdir()

        with pytest.raises(ValueError, match="Not a valid Git repository"):
            GitManager(non_repo_path)

    def test_get_current_branch(self, test_repo):
        """Test getting current branch name"""
        git_manager = GitManager(test_repo)

        # Create and checkout a new branch
        subprocess.run(
            ["git", "checkout", "-b", "test-branch"], cwd=test_repo, capture_output=True
        )

        branch = git_manager.get_current_branch()
        assert branch == "test-branch"

    def test_get_commit_info(self, test_repo):
        """Test getting commit information"""
        git_manager = GitManager(test_repo)

        # Get HEAD commit info
        commit_info = git_manager.get_commit_info("HEAD")

        assert isinstance(commit_info, CommitInfo)
        assert commit_info.author == "Test User"
        assert commit_info.email == "test@test.com"
        assert "Initial commit" in commit_info.message
        assert len(commit_info.sha) == 40

    def test_resolve_commit(self, test_repo):
        """Test commit reference resolution"""
        git_manager = GitManager(test_repo)

        # Resolve HEAD
        sha = git_manager.resolve_commit("HEAD")
        assert len(sha) == 40

        # Invalid reference should raise error
        with pytest.raises(ValueError, match="Invalid commit reference"):
            git_manager.resolve_commit("nonexistent")

    def test_file_operations(self, test_repo):
        """Test file content operations"""
        git_manager = GitManager(test_repo)

        # Create a test file
        test_file = test_repo / "test.py"
        test_file.write_text("print('hello')")
        subprocess.run(["git", "add", "test.py"], cwd=test_repo)
        subprocess.run(["git", "commit", "-m", "Add test file"], cwd=test_repo)

        # Get file content at HEAD
        content = git_manager.get_file_content_at_commit("test.py", "HEAD")
        assert content == "print('hello')"

        # Modify file
        test_file.write_text("print('modified')")
        subprocess.run(["git", "add", "test.py"], cwd=test_repo)
        subprocess.run(["git", "commit", "-m", "Modify test file"], cwd=test_repo)

        # Get content at different commits
        content_new = git_manager.get_file_content_at_commit("test.py", "HEAD")
        content_old = git_manager.get_file_content_at_commit("test.py", "HEAD~1")

        assert content_new == "print('modified')"
        assert content_old == "print('hello')"

    def test_get_modified_files(self, test_repo):
        """Test getting modified files between commits"""
        git_manager = GitManager(test_repo)

        # Create some files
        (test_repo / "file1.py").write_text("content1")
        (test_repo / "file2.py").write_text("content2")
        subprocess.run(["git", "add", "."], cwd=test_repo)
        subprocess.run(["git", "commit", "-m", "Add files"], cwd=test_repo)

        first_commit = git_manager.resolve_commit("HEAD")

        # Modify one file and add another
        (test_repo / "file1.py").write_text("modified")
        (test_repo / "file3.py").write_text("content3")
        subprocess.run(["git", "add", "."], cwd=test_repo)
        subprocess.run(["git", "commit", "-m", "Modify and add"], cwd=test_repo)

        # Get modified files
        modified = git_manager.get_modified_files(first_commit, "HEAD")

        assert "file1.py" in modified
        assert "file3.py" in modified
        assert "file2.py" not in modified

    def test_uncommitted_files(self, test_repo):
        """Test detecting uncommitted changes"""
        git_manager = GitManager(test_repo)

        # Initially clean
        assert not git_manager.is_file_modified()

        # Add untracked file
        (test_repo / "untracked.py").write_text("new file")
        assert git_manager.is_file_modified()

        uncommitted = git_manager.get_uncommitted_files()
        assert "untracked.py" in uncommitted["untracked"]

        # Stage the file
        subprocess.run(["git", "add", "untracked.py"], cwd=test_repo)
        uncommitted = git_manager.get_uncommitted_files()
        assert "untracked.py" in uncommitted["added"]

    def test_stash_operations(self, test_repo):
        """Test stash and restore operations"""
        git_manager = GitManager(test_repo)

        # Create a change
        test_file = test_repo / "stash_test.py"
        test_file.write_text("changes to stash")

        # Stash changes
        stashed = git_manager.stash_changes("Test stash")
        assert stashed is True
        assert not test_file.exists()

        # Restore stash
        restored = git_manager.restore_stash(pop=True)
        assert restored is True
        assert test_file.exists()
        assert test_file.read_text() == "changes to stash"

    def test_diff_between_commits(self, test_repo):
        """Test getting diffs between commits"""
        git_manager = GitManager(test_repo)

        # Create initial state
        (test_repo / "diff_test.py").write_text("original")
        subprocess.run(["git", "add", "."], cwd=test_repo)
        subprocess.run(["git", "commit", "-m", "Original"], cwd=test_repo)

        original_commit = git_manager.resolve_commit("HEAD")

        # Make changes
        (test_repo / "diff_test.py").write_text("modified")
        (test_repo / "new_file.py").write_text("new")
        subprocess.run(["git", "add", "."], cwd=test_repo)
        subprocess.run(["git", "commit", "-m", "Changes"], cwd=test_repo)

        # Get diff
        diffs = git_manager.get_diff_between_commits(original_commit, "HEAD")

        # Check we have the expected changes
        diff_files = [d["a_path"] or d["b_path"] for d in diffs]
        assert "diff_test.py" in diff_files
        assert "new_file.py" in diff_files

    def test_find_commit_by_message(self, test_repo):
        """Test finding commits by message"""
        git_manager = GitManager(test_repo)

        # Create a commit with specific message
        (test_repo / "search_test.py").write_text("content")
        subprocess.run(["git", "add", "."], cwd=test_repo)
        subprocess.run(
            ["git", "commit", "-m", "UNIQUE-MARKER: Special commit"], cwd=test_repo
        )

        # Search for it
        found_sha = git_manager.find_commit_by_message("UNIQUE-MARKER")
        assert found_sha is not None

        # Verify it's the right commit
        commit_info = git_manager.get_commit_info(found_sha)
        assert "UNIQUE-MARKER" in commit_info.message

        # Search for non-existent
        not_found = git_manager.find_commit_by_message("NONEXISTENT")
        assert not_found is None

    def test_get_file_history(self, test_repo):
        """Test getting file history"""
        git_manager = GitManager(test_repo)

        # Create file with history
        test_file = test_repo / "history_test.py"

        for i in range(3):
            test_file.write_text(f"version {i}")
            subprocess.run(["git", "add", "."], cwd=test_repo)
            subprocess.run(["git", "commit", "-m", f"Version {i}"], cwd=test_repo)

        # Get history
        history = git_manager.get_file_history("history_test.py", max_commits=5)

        assert len(history) == 3
        assert "Version 2" in history[0].message
        assert "Version 1" in history[1].message
        assert "Version 0" in history[2].message
