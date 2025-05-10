import pygit2
import time
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
        
        # Create a signature for commits
        self.signature = pygit2.Signature("TaskNotes", "tasknotes@example.com")
        
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
        """Commit changes to the repository.
        
        Args:
            message: Commit message
            tree_id: ID of the tree to commit
        """
        # Get the current branch
        branch = self.repo.branches[self.branch_name]
        
        # Create the commit
        commit = self.repo.create_commit(
            branch.name,  # Reference name
            self.signature,  # Author
            self.signature,  # Committer
            message,  # Commit message
            tree_id,  # Tree ID
            # Parent commits
            [branch.target] if not self.repo.is_empty else []
        )
        
        # Update the branch reference
        self.repo.references[branch.name].set_target(commit)
    
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
        
        # Handle paths with directories
        path_parts = path.split('/')
        current_tree = tree
        
        # Navigate through the directory structure
        try:
            # If there are directories in the path, traverse them
            for i, part in enumerate(path_parts[:-1]):
                entry = current_tree[part]
                if isinstance(entry, pygit2.Tree):
                    current_tree = entry
                else:
                    raise FileNotFoundError(f"Path component is not a directory: {part}")
            
            # Get the file from the final directory
            filename = path_parts[-1]
            blob = current_tree[filename]
            
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
        # Get the current tree
        tree = self._get_tree_from_branch()
        
        # Create a blob with the file content
        blob_id = self.repo.create_blob(content.encode("utf-8"))
        
        # Handle paths with directories
        path_parts = path.split('/')
        current_tree = tree
        builders = []
        
        # Build intermediate directory trees if needed
        for i, part in enumerate(path_parts[:-1]):
            try:
                entry = current_tree[part]
                if isinstance(entry, pygit2.Tree):
                    current_tree = entry
                else:
                    raise IOError(f"Path component exists but is not a directory: {part}")
            except KeyError:
                # Create a new empty tree for this directory level
                new_builder = self.repo.TreeBuilder()
                tree_id = new_builder.write()
                current_tree = self.repo[tree_id]
            
            # Create a builder for this level, copying existing entries
            builder = self.repo.TreeBuilder(current_tree)
            builders.append((part, builder))
        
        # Insert the file into the final directory
        filename = path_parts[-1]
        if builders:
            last_builder = builders[-1][1]
        else:
            last_builder = self.repo.TreeBuilder(tree)
        
        last_builder.insert(filename, blob_id, pygit2.GIT_FILEMODE_BLOB)
        current_tree_id = last_builder.write()
        
        # Work our way back up, creating new trees with the updated subtrees
        for part, builder in reversed(builders[:-1]):
            builder.insert(path_parts[builders.index((part, builder)) + 1], 
                         current_tree_id, 
                         pygit2.GIT_FILEMODE_TREE)
            current_tree_id = builder.write()
        
        # Finally, update the root tree
        if builders:
            root_builder = self.repo.TreeBuilder(tree)
            root_builder.insert(path_parts[0], current_tree_id, pygit2.GIT_FILEMODE_TREE)
            final_tree_id = root_builder.write()
        else:
            # File is in the root directory
            root_builder = self.repo.TreeBuilder(tree)
            root_builder.insert(filename, blob_id, pygit2.GIT_FILEMODE_BLOB)
            final_tree_id = root_builder.write()
        
        # Commit the changes
        self._commit_changes(f"Write file: {path}", final_tree_id)
    
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
        
        # Get the current tree
        tree = self._get_tree_from_branch()
        
        # If a directory is specified, navigate to it
        if directory:
            try:
                current_tree = tree
                for part in directory.split('/'):
                    if not part:
                        continue
                    entry = current_tree[part]
                    if not isinstance(entry, pygit2.Tree):
                        return []
                    current_tree = self.repo[entry.id]
                tree = current_tree
            except KeyError:
                return []
        
        files = []
        
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
        
        # Handle paths with directories
        path_parts = path.split('/')
        current_tree = tree
        
        try:
            # If there are directories in the path, traverse them
            for i, part in enumerate(path_parts[:-1]):
                entry = current_tree[part]
                if isinstance(entry, pygit2.Tree):
                    current_tree = entry
                else:
                    return False  # Path component is not a directory
            
            # Check if the file exists in the final directory
            filename = path_parts[-1]
            entry = current_tree[filename]
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
            float: The last modified time of the file as a Unix timestamp
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        if not self.file_exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        # Get the commit history for the file
        branch = self.repo.branches[self.branch_name]
        commit_times = []
        print("Commits containing file:", path)
        
        # First, find all commits that contain this file
        for commit in self.repo.walk(branch.target, pygit2.GIT_SORT_NONE):
            try:
                tree = commit.tree
                for part in path.split('/'):
                    tree = tree[part]
                # If we got here, the file exists in this commit
                commit_times.append(commit.commit_time)
                print(f"  {commit.id}: {commit.commit_time} ({time.ctime(commit.commit_time)})")
            except KeyError:
                continue
        
        if not commit_times:
            # This should never happen as we checked file_exists
            raise FileNotFoundError(f"File not found in commit history: {path}")
        
        # Get the most recent commit time
        return float(max(commit_times))

    
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

