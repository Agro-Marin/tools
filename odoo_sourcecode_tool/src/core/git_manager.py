"""
Centralized Git operations manager using GitPython directly
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from git import GitCommandError, Repo

logger = logging.getLogger(__name__)


@dataclass
class CommitInfo:
    """Information about a Git commit"""

    sha: str
    author: str
    email: str
    date: str
    message: str
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0


class GitManager:
    """Centralized manager for Git operations using GitPython directly"""

    def __init__(self, repo_path: str | None = None):
        """
        Initialize Git manager

        Args:
            repo_path: Path to Git repository. If None, tries to find repository from current directory
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.repo = None
        self._initialize_repo()

    def _initialize_repo(self) -> None:
        """Initialize Git repository object"""
        try:
            self.repo = Repo(self.repo_path, search_parent_directories=True)
            self.repo_path = Path(self.repo.working_dir)
            logger.debug(f"Initialized Git repository at {self.repo_path}")
        except Exception as e:
            logger.error(f"Failed to initialize Git repository: {e}")
            raise ValueError(f"Not a valid Git repository: {self.repo_path}")

    def get_current_branch(self) -> str:
        """Get current branch name"""
        try:
            return self.repo.active_branch.name
        except TypeError:
            # Detached HEAD state
            return self.repo.head.commit.hexsha[:8]

    def get_commit_info(self, commit_sha: str) -> CommitInfo:
        """Get information about a specific commit"""
        try:
            commit = self.repo.commit(commit_sha)
            stats = commit.stats.total

            return CommitInfo(
                sha=commit.hexsha,
                author=commit.author.name,
                email=commit.author.email,
                date=commit.authored_datetime.isoformat(),
                message=commit.message.strip(),
                files_changed=stats.get("files", 0),
                insertions=stats.get("insertions", 0),
                deletions=stats.get("deletions", 0),
            )
        except Exception as e:
            logger.error(f"Error getting commit info for {commit_sha}: {e}")
            raise

    def get_file_content_at_commit(
        self,
        file_path: str,
        commit_sha: str,
    ) -> str | None:
        """Get file content at a specific commit"""
        try:
            commit = self.repo.commit(commit_sha)
            # Make path relative to repo root
            rel_path = (
                Path(file_path).relative_to(self.repo_path)
                if Path(file_path).is_absolute()
                else Path(file_path)
            )

            # Use forward slashes for Git paths
            git_path = str(rel_path).replace("\\", "/")

            try:
                blob = commit.tree / git_path
                return blob.data_stream.read().decode("utf-8")
            except KeyError:
                logger.debug(f"File {git_path} not found at commit {commit_sha[:8]}")
                return None
        except Exception as e:
            logger.error(f"Error getting file content: {e}")
            return None

    def get_diff_between_commits(
        self,
        from_commit: str,
        to_commit: str,
        paths: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get diff between two commits"""
        try:
            commit_from = self.repo.commit(from_commit)
            commit_to = self.repo.commit(to_commit)

            diffs = commit_from.diff(commit_to, paths=paths)

            results = []
            for diff in diffs:
                diff_info = {
                    "a_path": diff.a_path,
                    "b_path": diff.b_path,
                    "change_type": diff.change_type,
                    "renamed": diff.renamed,
                    "renamed_file": diff.renamed_file,
                }

                if diff.change_type != "D":  # Not deleted
                    diff_info["b_blob"] = diff.b_blob.hexsha if diff.b_blob else None
                if diff.change_type != "A":  # Not added
                    diff_info["a_blob"] = diff.a_blob.hexsha if diff.a_blob else None

                results.append(diff_info)

            return results
        except Exception as e:
            logger.error(f"Error getting diff: {e}")
            return []

    def get_modified_files(
        self,
        from_commit: str,
        to_commit: str,
    ) -> list[str]:
        """Get list of modified files between commits"""
        diffs = self.get_diff_between_commits(from_commit, to_commit)
        files = set()

        for diff in diffs:
            if diff["a_path"]:
                files.add(diff["a_path"])
            if diff["b_path"]:
                files.add(diff["b_path"])

        return sorted(list(files))

    def find_commit_by_message(
        self,
        pattern: str,
        max_commits: int = 100,
    ) -> str | None:
        """Find commit by message pattern"""
        try:
            for commit in self.repo.iter_commits(max_count=max_commits):
                if pattern.lower() in commit.message.lower():
                    return commit.hexsha
            return None
        except Exception as e:
            logger.error(f"Error searching commits: {e}")
            return None

    def get_commits_between(
        self,
        from_commit: str,
        to_commit: str,
    ) -> list[str]:
        """Get list of commit SHAs between two commits"""
        try:
            commits = []
            for commit in self.repo.iter_commits(f"{from_commit}..{to_commit}"):
                commits.append(commit.hexsha)
            return commits
        except Exception as e:
            logger.error(
                f"Error getting commits between {from_commit} and {to_commit}: {e}"
            )
            return []

    def resolve_commit(
        self,
        ref: str,
    ) -> str:
        """Resolve a commit reference to full SHA"""
        try:
            commit = self.repo.commit(ref)
            return commit.hexsha
        except Exception as e:
            logger.error(f"Error resolving commit {ref}: {e}")
            raise ValueError(f"Invalid commit reference: {ref}")

    def get_file_history(
        self,
        file_path: str,
        max_commits: int = 10,
    ) -> list[CommitInfo]:
        """Get commit history for a specific file"""
        try:
            rel_path = (
                Path(file_path).relative_to(self.repo_path)
                if Path(file_path).is_absolute()
                else Path(file_path)
            )
            git_path = str(rel_path).replace("\\", "/")

            commits = []
            for commit in self.repo.iter_commits(paths=git_path, max_count=max_commits):
                commits.append(self.get_commit_info(commit.hexsha))
            return commits
        except Exception as e:
            logger.error(f"Error getting file history: {e}")
            return []

    def is_file_modified(self) -> bool:
        """Check if there are uncommitted changes"""
        return self.repo.is_dirty()

    def get_uncommitted_files(self) -> dict[str, list[str]]:
        """Get lists of uncommitted files by status"""
        result = {
            "modified": [],
            "added": [],
            "deleted": [],
            "renamed": [],
            "untracked": [],
        }

        # Get staged files
        for item in self.repo.index.diff("HEAD"):
            if item.change_type == "M":
                result["modified"].append(item.a_path)
            elif item.change_type == "A":
                result["added"].append(item.a_path)
            elif item.change_type == "D":
                result["deleted"].append(item.a_path)
            elif item.change_type == "R":
                result["renamed"].append(f"{item.a_path} -> {item.b_path}")

        # Get unstaged files
        for item in self.repo.index.diff(None):
            if item.a_path not in result["modified"]:
                result["modified"].append(item.a_path)

        # Get untracked files
        result["untracked"] = self.repo.untracked_files

        return result

    def stash_changes(
        self,
        message: str | None = None,
    ) -> bool:
        """Stash current changes"""
        try:
            if self.repo.is_dirty() or self.repo.untracked_files:
                self.repo.git.stash(
                    "push", "-u", "-m", message or "Auto-stash by odoo-tools"
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Error stashing changes: {e}")
            return False

    def restore_stash(
        self,
        pop: bool = True,
    ) -> bool:
        """Restore stashed changes"""
        try:
            if pop:
                self.repo.git.stash("pop")
            else:
                self.repo.git.stash("apply")
            return True
        except GitCommandError as e:
            if "No stash entries found" in str(e):
                logger.debug("No stash to restore")
                return False
            logger.error(f"Error restoring stash: {e}")
            return False

    def get_merge_base(
        self,
        ref1: str,
        ref2: str,
    ) -> str | None:
        """Find merge base between two commits/branches"""
        try:
            merge_base = self.repo.merge_base(ref1, ref2)
            if merge_base:
                return merge_base[0].hexsha
            return None
        except Exception as e:
            logger.error(f"Error finding merge base: {e}")
            return None
