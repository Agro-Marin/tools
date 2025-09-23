"""
Git Repository Analyzer
========================

Handles Git repository operations, commit resolution, and file content retrieval.
"""

import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class GitRepositoryError(Exception):
    """Exception raised for Git repository related errors"""

    pass


class GitAnalyzer:
    """Git repository analyzer for commit and file operations"""

    def __init__(self, repo_path: str):
        """
        Initialize Git analyzer with repository path.

        Args:
            repo_path: Path to the Git repository

        Raises:
            GitRepositoryError: If repository is not valid
        """
        self.repo_path = Path(repo_path).resolve()
        self._validate_repository()

    def _validate_repository(self):
        """Validate that the path contains a valid Git repository"""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise GitRepositoryError(f"No Git repository found at {self.repo_path}")

        try:
            self._run_git_command(["status"], capture_output=True)
        except subprocess.CalledProcessError as e:
            raise GitRepositoryError(f"Invalid Git repository: {e}")

    def _run_git_command(
        self, args: list[str], capture_output: bool = True, cwd: str | None = None
    ) -> subprocess.CompletedProcess:
        """
        Run a Git command in the repository.

        Args:
            args: Git command arguments
            capture_output: Whether to capture stdout/stderr
            cwd: Working directory (defaults to repo_path)

        Returns:
            Completed process result
        """
        cmd = ["git"] + args
        working_dir = cwd or str(self.repo_path)

        logger.debug(f"Running: {' '.join(cmd)} in {working_dir}")

        try:
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=capture_output,
                text=True,
                check=True,
            )
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {' '.join(cmd)}")
            logger.error(f"Error: {e.stderr}")
            raise GitRepositoryError(f"Git command failed: {e}")

    def resolve_commits(
        self,
        commit_from: str | None = None,
        commit_to: str | None = None,
        json_data: dict | None = None,
    ) -> tuple[str, str]:
        """
        Resolve commit SHAs for analysis.

        Args:
            commit_from: Starting commit SHA (optional)
            commit_to: Ending commit SHA (optional)
            json_data: Modified modules JSON data (optional)

        Returns:
            tuple of (commit_from, commit_to) SHAs
        """
        # Resolve commit_to
        if commit_to:
            resolved_commit_to = self._resolve_commit_sha(commit_to)
        elif json_data and "commit_info" in json_data:
            resolved_commit_to = json_data["commit_info"]["hash"]
        else:
            # Use HEAD as default
            resolved_commit_to = self._get_current_commit()

        # Resolve commit_from
        if commit_from:
            resolved_commit_from = self._resolve_commit_sha(commit_from)
        else:
            # Get previous commit
            resolved_commit_from = self._get_previous_commit(resolved_commit_to)

        # Validate both commits exist
        self._validate_commit(resolved_commit_from)
        self._validate_commit(resolved_commit_to)

        logger.info(
            f"Resolved commits: {resolved_commit_from[:8]}..{resolved_commit_to[:8]}"
        )

        return resolved_commit_from, resolved_commit_to

    def _resolve_commit_sha(self, commit_ref: str) -> str:
        """Resolve a commit reference to full SHA"""
        try:
            result = self._run_git_command(["rev-parse", commit_ref])
            return result.stdout.strip()
        except GitRepositoryError:
            raise GitRepositoryError(f"Cannot resolve commit reference: {commit_ref}")

    def _get_current_commit(self) -> str:
        """Get current HEAD commit SHA"""
        result = self._run_git_command(["rev-parse", "HEAD"])
        return result.stdout.strip()

    def _get_previous_commit(self, commit_sha: str) -> str:
        """Get the previous commit SHA"""
        try:
            result = self._run_git_command(["rev-parse", f"{commit_sha}^"])
            return result.stdout.strip()
        except GitRepositoryError:
            raise GitRepositoryError(f"Cannot get previous commit for {commit_sha}")

    def _validate_commit(self, commit_sha: str):
        """Validate that a commit exists in the repository"""
        try:
            self._run_git_command(["cat-file", "-e", commit_sha])
        except GitRepositoryError:
            raise GitRepositoryError(f"Commit {commit_sha} does not exist")

    def get_file_content_at_commit(self, file_path: str, commit_sha: str) -> str | None:
        """
        Get file content at a specific commit.

        Args:
            file_path: Relative path to file from repository root
            commit_sha: Commit SHA to retrieve file from

        Returns:
            File content as string, or None if file doesn't exist at commit
        """
        try:
            result = self._run_git_command(["show", f"{commit_sha}:{file_path}"])
            return result.stdout
        except GitRepositoryError:
            logger.debug(f"File {file_path} not found at commit {commit_sha}")
            return None

    def get_file_diff(
        self, file_path: str, commit_from: str, commit_to: str
    ) -> str | None:
        """
        Get diff for a specific file between two commits.

        Args:
            file_path: Relative path to file from repository root
            commit_from: Starting commit SHA
            commit_to: Ending commit SHA

        Returns:
            Diff output as string, or None if no diff
        """
        try:
            result = self._run_git_command(
                [
                    "diff",
                    "--no-color",
                    "--unified=3",
                    f"{commit_from}..{commit_to}",
                    "--",
                    file_path,
                ]
            )
            return result.stdout if result.stdout.strip() else None
        except GitRepositoryError:
            logger.debug(f"No diff available for {file_path}")
            return None

    def get_changed_files(self, commit_from: str, commit_to: str) -> list[str]:
        """
        Get list of files changed between two commits.

        Args:
            commit_from: Starting commit SHA
            commit_to: Ending commit SHA

        Returns:
            List of changed file paths
        """
        try:
            result = self._run_git_command(
                ["diff", "--name-only", f"{commit_from}..{commit_to}"]
            )
            return [line.strip() for line in result.stdout.split("\n") if line.strip()]
        except GitRepositoryError:
            logger.error(
                f"Cannot get changed files between {commit_from} and {commit_to}"
            )
            return []

    def get_commit_info(self, commit_sha: str) -> dict[str, str]:
        """
        Get detailed information about a commit.

        Args:
            commit_sha: Commit SHA to get info for

        Returns:
            Dictionary with commit information
        """
        try:
            result = self._run_git_command(
                [
                    "show",
                    "--format=format:%H%n%an <%ae>%n%ad%n%s",
                    "--no-patch",
                    "--date=iso",
                    commit_sha,
                ]
            )

            lines = result.stdout.strip().split("\n")
            if len(lines) >= 4:
                return {
                    "hash": lines[0],
                    "author": lines[1],
                    "date": lines[2],
                    "message": lines[3],
                }
        except GitRepositoryError:
            pass

        return {
            "hash": commit_sha,
            "author": "Unknown",
            "date": "Unknown",
            "message": "Unknown",
        }

    def file_exists_at_commit(self, file_path: str, commit_sha: str) -> bool:
        """
        Check if file exists at a specific commit.

        Args:
            file_path: Relative path to file from repository root
            commit_sha: Commit SHA to check

        Returns:
            True if file exists at commit
        """
        try:
            self._run_git_command(["cat-file", "-e", f"{commit_sha}:{file_path}"])
            return True
        except GitRepositoryError:
            return False

    def get_repository_info(self) -> dict[str, str]:
        """
        Get general repository information.

        Returns:
            Dictionary with repository information
        """
        try:
            # Get current branch
            branch_result = self._run_git_command(["branch", "--show-current"])
            current_branch = branch_result.stdout.strip()

            # Get remote origin URL
            try:
                remote_result = self._run_git_command(["remote", "get-url", "origin"])
                remote_url = remote_result.stdout.strip()
            except GitRepositoryError:
                remote_url = "No remote origin"

            # Get latest commit
            latest_commit = self._get_current_commit()

            return {
                "path": str(self.repo_path),
                "current_branch": current_branch,
                "remote_url": remote_url,
                "latest_commit": latest_commit,
            }

        except GitRepositoryError:
            return {
                "path": str(self.repo_path),
                "current_branch": "Unknown",
                "remote_url": "Unknown",
                "latest_commit": "Unknown",
            }

    def extract_commit_from_json(self, json_file_path: str) -> str | None:
        """
        Extract commit hash from modified_modules.json file.

        Args:
            json_file_path: Path to the JSON file

        Returns:
            Commit hash or None if not found
        """
        try:
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "commit_info" in data and "hash" in data["commit_info"]:
                return data["commit_info"]["hash"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Cannot extract commit from JSON: {e}")

        return None
