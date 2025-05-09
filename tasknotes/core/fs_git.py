import pygit2
from pathlib import Path
from typing import List, Optional, Dict, Any, BinaryIO, Set, Iterator

from tasknotes.interface.file_service import FileService
from .task_env import TaskNoteEnv


class GitRepoTree(FileService):
    """Implementation of FileService for git repository tree storage.
    
    This implementation stores files in a git branch, allowing for
    version control and collaboration on tasks.
    """
    
    def __init__(self, env: TaskNoteEnv, branch_name: str = "tasknote"):
        """Initialize the GitRepoTree service.
        
        Args:
            env: TaskNoteEnv instance for the repository
            branch_name: Name of the branch to use for storage
        
        Raises:
            ValueError: If the repository is not a git repository
        """
        if not env.is_git_repo():
            raise ValueError("Not a git repository")
        
        self.env = env
        self.repo = env._repo
        self.branch_name = branch_name
        self._ensure_branch_exists()
    
    def _ensure_branch_exists(self) -> None:
        """Ensure that the tasknote branch exists.
        
        If the branch does not exist, it is created from the current HEAD.
        """
        if self.branch_name not in self.repo.branches:
            # Create the branch from the current HEAD
            head = self.repo.head
            ref = self.repo.create_branch(self.branch_name, self.repo[head.target])
    
    def _get_tree_from_branch(self) -> pygit2.Tree:
        """Get the tree from the tasknote branch.
        
        Returns:
            pygit2.Tree: Tree object from the branch
        """
        branch = self.repo.branches[self.branch_name]
        commit = self.repo[branch.target]
        return commit.tree
    
    def _commit_changes(self, message: str, tree_id: pygit2.Oid) -> None:
        """Commit changes to the tasknote branch.
        
        Args:
            message: Commit message
            tree_id: ID of the tree to commit
        """
        # Get the branch and its target commit
        branch = self.repo.branches[self.branch_name]
        parent = self.repo[branch.target]
        
        # Create the commit
        author = pygit2.Signature("TaskNotes", "tasknotes@example.com")
        committer = author
        
        # Create the commit
        commit_id = self.repo.create_commit(
            f"refs/heads/{self.branch_name}",  # Reference to update
            author,
            committer,
            message,
            tree_id,
            [parent.id]
        )
    
    def read_file(self, path: str) -> str:
        """Read a file from the storage.
        
        Args:
            path: Path to the file relative to the storage root
            
        Returns:
            str: Content of the file
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        tree = self._get_tree_from_branch()
        
        try:
            # Find the blob in the tree
            blob = tree[path]
            if isinstance(blob, pygit2.Blob):
                return blob.data.decode("utf-8")
            else:
                raise FileNotFoundError(f"Path is not a file: {path}")
        except KeyError:
            raise FileNotFoundError(f"File not found: {path}")
    
    def write_file(self, path: str, content: str) -> None:
        """Write content to a file in the storage.
        
        Args:
            path: Path to the file relative to the storage root
            content: Content to write to the file
            
        Raises:
            IOError: If the file cannot be written
        """
        # Create a new tree with the file added or modified
        tree = self._get_tree_from_branch()
        builder = self.repo.TreeBuilder(tree)
        
        # Create the blob
        blob_id = self.repo.create_blob(content.encode("utf-8"))
        
        # Add the blob to the tree
        path_parts = path.split("/")
        if len(path_parts) > 1:
            # We need to create or update subtrees
            current_tree = tree
            current_path = ""
            
            # Process all directories except the last one (which is the file)
            for i, part in enumerate(path_parts[:-1]):
                current_path = "/".join(path_parts[:i+1])
                
                try:
                    entry = current_tree[part]
                    if isinstance(entry, pygit2.Tree):
                        # Directory exists, get its tree
                        current_tree = entry
                    else:
                        # Entry exists but is not a directory
                        raise IOError(f"Path exists but is not a directory: {current_path}")
                except KeyError:
                    # Directory doesn't exist, create it
                    subtree_builder = self.repo.TreeBuilder()
                    subtree_id = subtree_builder.write()
                    
                    # Add the new subtree to the current tree
                    builder.insert(part, subtree_id, pygit2.GIT_FILEMODE_TREE)
                    
                    # Update the current tree
                    current_tree = self.repo[subtree_id]
        
        # Add the file to the tree
        filename = path_parts[-1]
        builder.insert(filename, blob_id, pygit2.GIT_FILEMODE_BLOB)
        
        # Write the new tree
        new_tree_id = builder.write()
        
        # Commit the changes
        self._commit_changes(f"Update {path}", new_tree_id)
    
    def delete_file(self, path: str) -> None:
        """Delete a file from the storage.
        
        Args:
            path: Path to the file relative to the storage root
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        # Check if the file exists
        if not self.file_exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        # Create a new tree with the file removed
        tree = self._get_tree_from_branch()
        builder = self.repo.TreeBuilder(tree)
        
        # Remove the file from the tree
        path_parts = path.split("/")
        filename = path_parts[-1]
        
        # If the file is in a subdirectory, we need to update the subtree
        if len(path_parts) > 1:
            # TODO: Implement removal from subtrees
            # This is more complex and requires recursive tree building
            raise NotImplementedError("Deletion from subdirectories not yet implemented")
        else:
            # Remove the file from the root tree
            builder.remove(filename)
        
        # Write the new tree
        new_tree_id = builder.write()
        
        # Commit the changes
        self._commit_changes(f"Delete {path}", new_tree_id)
    
    def list_files(self, directory: str = "", pattern: str = "*") -> List[str]:
        """List files in a directory.
        
        Args:
            directory: Directory to list files from, relative to the storage root
            pattern: Pattern to match files against (glob format)
            
        Returns:
            List[str]: List of file paths relative to the storage root
        """
        import fnmatch
        
        tree = self._get_tree_from_branch()
        files = []
        
        # If directory is specified, get the subtree
        if directory:
            try:
                entry = tree[directory]
                if isinstance(entry, pygit2.Tree):
                    tree = entry
                else:
                    # Entry exists but is not a directory
                    return []
            except KeyError:
                # Directory doesn't exist
                return []
        
        # Helper function to recursively list files
        def _list_files_recursive(tree, prefix=""):
            for entry in tree:
                entry_path = f"{prefix}{entry.name}"
                if entry.type_str == "tree":
                    # It's a directory, recurse
                    subtree = self.repo[entry.id]
                    _list_files_recursive(subtree, f"{entry_path}/")
                elif entry.type_str == "blob":
                    # It's a file, add it to the list if it matches the pattern
                    if fnmatch.fnmatch(entry.name, pattern):
                        files.append(entry_path)
        
        # Start the recursive listing
        _list_files_recursive(tree, "" if not directory else f"{directory}/")
        
        return files
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in the storage.
        
        Args:
            path: Path to the file relative to the storage root
            
        Returns:
            bool: True if the file exists, False otherwise
        """
        tree = self._get_tree_from_branch()
        
        try:
            entry = tree[path]
            return isinstance(entry, pygit2.Blob)
        except KeyError:
            return False
    
    def create_directory(self, path: str) -> None:
        """Create a directory in the storage.
        
        Args:
            path: Path to the directory relative to the storage root
            
        Raises:
            IOError: If the directory cannot be created
        """
        # In Git, directories are created implicitly when files are added
        # So we create an empty .gitkeep file in the directory
        self.write_file(f"{path}/.gitkeep", "")
    
    def get_modified_time(self, path: str) -> float:
        """Get the last modified time of a file.
        
        Args:
            path: Path to the file relative to the storage root
            
        Returns:
            float: Last modified time as a timestamp
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        if not self.file_exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        # Get the commit history for the file
        branch = self.repo.branches[self.branch_name]
        commit = self.repo[branch.target]
        
        # Find the most recent commit that modified the file
        walker = self.repo.walk(commit.id, pygit2.GIT_SORT_TIME)
        for commit in walker:
            if path in self._get_changed_files(commit):
                return commit.commit_time
        
        # If no commit found, use the repository creation time
        return commit.commit_time
    
    def _get_changed_files(self, commit) -> Set[str]:
        """Get the files changed in a commit.
        
        Args:
            commit: Commit object
            
        Returns:
            Set[str]: Set of file paths changed in the commit
        """
        changed_files = set()
        
        if len(commit.parents) == 0:
            # Initial commit, all files are new
            for entry in commit.tree:
                changed_files.add(entry.name)
        else:
            # Compare with parent
            parent = commit.parents[0]
            diff = parent.tree.diff_to_tree(commit.tree)
            
            for patch in diff:
                if patch.delta.new_file.path:
                    changed_files.add(patch.delta.new_file.path)
        
        return changed_files

