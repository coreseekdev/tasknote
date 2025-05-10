"""Git integration for TaskNotes."""

import os
import subprocess
from typing import List, Optional, Tuple, Dict, Any, Literal
from pathlib import Path
import pygit2
from pygit2.repository import RepositoryOpenFlag

# Import config
from .config import config

# Import FileService from interface package
from tasknotes.interface.file_service import FileService


def setup_git_alias() -> bool:
    """Set up the 'git task' alias."""
    try:
        # Check if the alias already exists
        result = subprocess.run(
            ["git", "config", "--global", "--get", "alias.task"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if result.returncode == 0 and result.stdout.strip():
            # Alias already exists
            return True
            
        # Set up the alias
        subprocess.run(
            ["git", "config", "--global", "alias.task", "!tasknotes"],
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


class TaskNoteEnv:
    """Environment class for TaskNotes that can be constructed with a git repository path.
    
    This class provides methods to check if a path is a git repository and if TaskNotes
    has been initialized in the repository.
    """
    
    def __init__(self, repo_path: str, flags: RepositoryOpenFlag = RepositoryOpenFlag.DEFAULT):
        """Initialize the TaskNoteEnv with a repository path.
        
        Args:
            repo_path: Path to the git repository
            flags: Optional flags for opening the repository
        """
        self.repo_path = Path(repo_path).resolve()
        self._repo = None
        
        # Try to open the repository if it exists
        try:
            self._repo = pygit2.Repository(self.repo_path, flags)
        except pygit2.GitError:
            self._repo = None
    
    def is_git_repo(self) -> bool:
        """Check if the path is a git repository.
        
        Returns:
            bool: True if the path is a git repository, False otherwise
        """
        return self._repo is not None
    
    def is_tasknote_init(self) -> bool:
        """Check if TaskNotes has been initialized in the repository.
        
        TaskNotes is considered initialized if either:
        1. The .tasknote directory exists in the repository root
        2. A specific TaskNotes branch exists
        
        Returns:
            bool: True if TaskNotes is initialized, False otherwise
        """
        # 不需要额外检查 is_git_repo ， 因为支持 本地目录的方式

        # Check if .tasknote directory exists
        tasknote_dir = self.repo_path / config.get("local.task_dir")
        if tasknote_dir.exists() and tasknote_dir.is_dir():
            return True
        
        # Check for TaskNotes branch if we have a valid repository
        if self._repo is not None:
            # Look for a branch with 'tasknote' in the name
            for branch in self._repo.branches:
                if config.get("git.branch_name") in branch.lower():
                    return True
                    
        return False
    
    def _get_user_signature(self) -> pygit2.Signature:
        """Get a signature for the current user from git config.
        
        Returns:
            pygit2.Signature: Signature with user name and email
        """
        # Default values
        user_name = config.get("git.user_name")
        user_email = config.get("git.user_email")
        
        if self._repo is not None:
            try:
                # Try to get user name and email from repository config
                repo_config = self._repo.config
                try:
                    user_name = repo_config["user.name"]
                    user_email = repo_config["user.email"]
                except KeyError:
                    pass
            except (pygit2.GitError, KeyError):
                # Try to get from global config
                try:
                    global_config_path = pygit2.Config.find_global()
                    if global_config_path:
                        global_config = pygit2.Config.open(global_config_path)
                        try:
                            user_name = global_config["user.name"]
                            user_email = global_config["user.email"]
                        except KeyError:
                            pass
                except (pygit2.GitError, KeyError):
                    # Use defaults if there's an error
                    pass
        
        return pygit2.Signature(user_name, user_email)
    
    def get_repo_root(self) -> Optional[Path]:
        """Get the root directory of the git repository.
        
        Returns:
            Optional[Path]: Path to the repository root, or None if not a git repository
        """
        if not self.is_git_repo():
            return None
        return self.repo_path
    
    def get_tasknote_fs(self) -> Optional[FileService]:
        """Get the TaskNotes directory for the repository.
        
        Returns:
            Optional[FileService]: FileService for the TaskNotes storage, or None if not initialized
        """
        if not self.is_tasknote_init():
            return None
            
        return find_file_service(self.repo_path, self)
    
    def tasknote_init(self, mode: Literal["LOCAL", "GIT"] = "LOCAL") -> bool:
        """Initialize TaskNotes in the repository.
        
        Args:
            mode: Initialization mode - LOCAL for directory-based, GIT for branch-based
                 LOCAL: Creates a .tasknote directory in the repository root
                 GIT: Creates an empty tasknote branch in the git repository
        
        Returns:
            bool: True if initialization was successful, False otherwise
        
        Note:
            If TaskNotes is already initialized, this method will return True
            without performing any action, regardless of the mode.
        """
        # Check if already initialized
        if self.is_tasknote_init():
            return True
        
        # Initialize based on mode
        if mode == "LOCAL":
            # Create .tasknote directory
            tasknote_dir = self.repo_path / config.get("local.task_dir")
            try:
                tasknote_dir.mkdir(exist_ok=True)
                return True
            except Exception as e:
                print(f"Error creating TaskNotes directory: {str(e)}")
                return False
        elif mode == "GIT":
            # Check if this is a git repository
            if not self.is_git_repo():
                return False
            
            try:
                # Get user signature
                author = self._get_user_signature()
                
                # Create an empty tree
                empty_tree_id = self._repo.TreeBuilder().write()
                
                # Get parent commits if HEAD exists
                parent_commits = []
                try:
                    head = self._repo.head
                    parent_commits = [head.target]
                except (pygit2.GitError, KeyError):
                    # Repository might be empty, create orphan commit
                    pass
                    
                # Create the commit on a new branch directly
                branch_name = config.get("git.branch_name")
                reference_name = f"refs/heads/{branch_name}"
                
                # Create the commit
                commit_id = self._repo.create_commit(
                    reference_name,  # Create commit directly on the new branch
                    author,
                    author,
                    "Initial TaskNotes commit",
                    empty_tree_id,
                    parent_commits
                )
                
                return True
            except Exception as e:
                print(f"Error initializing TaskNotes in GIT mode: {str(e)}")
                return False
        else:
            # Invalid mode
            raise ValueError(f"Invalid mode: {mode}. Must be 'LOCAL' or 'GIT'.")

def find_file_service(path: str, env: Optional[TaskNoteEnv] = None) -> Optional[FileService]:
    """Create a FileService instance based on the path and environment.
    
    Args:
        path: Path to the repository or directory
        env: Optional TaskNoteEnv instance, will be created if not provided
        
    Returns:
        Optional[FileService]: FileService instance or None if path doesn't exist
    """
    # Check if path exists
    path_obj = Path(path)
    if not path_obj.exists():
        return None
        
    # Create environment if not provided
    if env is None:
        env = TaskNoteEnv(path)
    
    # Check if the repository is a git repository
    if env.is_git_repo():
        # Check if there's a tasknote branch
        repo = env._repo
        if config.get("git.branch_name") in repo.branches:
            from .fs_git import GitRepoTree
            # Use GitRepoTree if there's a tasknote branch
            return GitRepoTree(env)
    
    from .fs_local import LocalFilesystem
    # Use LocalFilesystem as fallback, with the correct path to the task directory
    task_dir_path = Path(path) / config.get("local.task_dir")
    return LocalFilesystem(task_dir_path)

# 似乎应该单独构造一个文件

from .edit_session_ot import EditSessionOT
from ..interface.edit_session import EditSession


def connect_edit_service(filename: str, context: str, session_id: Optional[str] = None) -> EditSession:
    """Connect to an edit service for the given file.
    
    Args:
        filename: Name of the file to edit (currently unused)
        context: Initial content for the edit session
        session_id: Optional session ID for the edit session
        
    Returns:
        EditSession: An edit session instance
    """
    return EditSessionOT(context, session_id)