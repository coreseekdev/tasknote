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
        
        # Transaction state
        self._in_transaction = False
        self._transaction_tree = None
        
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
    
    def begin_transaction(self) -> None:
        """Begin a transaction for batching multiple file operations.
        
        This method starts a transaction that allows multiple file operations
        to be batched together and committed atomically.
        """
        if self._in_transaction:
            raise ValueError("Transaction already in progress")
        
        # Start with the current tree
        self._transaction_tree = self._get_tree_from_branch()
        self._in_transaction = True
    
    def commit_transaction(self, message: str = "Batch file operations") -> None:
        """Commit the current transaction.
        
        This method commits all operations performed since the last call to
        begin_transaction.
        
        Args:
            message: Commit message
        
        Raises:
            ValueError: If no transaction is in progress
        """
        if not self._in_transaction:
            raise ValueError("No transaction in progress")
        
        # Commit the changes if the tree has been modified
        if self._transaction_tree is not None:
            self._commit_changes(message, self._transaction_tree.id)
        
        # Reset transaction state
        self._in_transaction = False
        self._transaction_tree = None
    
    def abort_transaction(self) -> None:
        """Abort the current transaction.
        
        This method discards all operations performed since the last call to
        begin_transaction.
        
        Raises:
            ValueError: If no transaction is in progress
        """
        if not self._in_transaction:
            raise ValueError("No transaction in progress")
        
        # Reset transaction state
        self._in_transaction = False
        self._transaction_tree = None
    
    def _get_current_tree(self) -> pygit2.Tree:
        """Get the current tree to operate on.
        
        Returns the transaction tree if in a transaction, otherwise gets the tree from the branch.
        
        Returns:
            pygit2.Tree: The current tree
        """
        if self._in_transaction and self._transaction_tree is not None:
            return self._transaction_tree
        else:
            return self._get_tree_from_branch()
    
    def _get_subtree(self, tree, path_parts):
        """Get a subtree at the specified path.
        
        Args:
            tree: The root tree to start from
            path_parts: List of path components to navigate
            
        Returns:
            pygit2.Tree: The subtree at the specified path
            
        Raises:
            KeyError: If the path does not exist
            ValueError: If a path component is not a directory
        """
        current_tree = tree
        for part in path_parts:
            if not part:  # Skip empty parts
                continue
            entry = current_tree[part]
            if not isinstance(entry, pygit2.Tree):
                raise ValueError(f"Path component is not a directory: {part}")
            current_tree = entry
        return current_tree
    
    def _update_subtree(self, tree, path_parts, name, new_id):
        """Update a subtree at the specified path with a new entry.
        
        Args:
            tree: The root tree to start from
            path_parts: List of path components to navigate
            name: Name of the entry to update
            new_id: ID of the new entry
            
        Returns:
            pygit2.Oid: ID of the updated tree
        """
        if not path_parts:
            # We've reached the target directory, update the entry
            builder = self.repo.TreeBuilder(tree)
            builder.insert(name, new_id, pygit2.GIT_FILEMODE_TREE)
            return builder.write()
        
        # Get the subtree for the current path component
        part = path_parts[0]
        subtree = tree[part]
        
        # Recursively update the subtree
        new_subtree_id = self._update_subtree(subtree, path_parts[1:], name, new_id)
        
        # Create a new tree with the updated subtree
        builder = self.repo.TreeBuilder(tree)
        builder.remove(part)
        builder.insert(part, new_subtree_id, pygit2.GIT_FILEMODE_TREE)
        
        return builder.write()
    
    def _update_tree_recursive(self, builder, tree, path_parts, new_id):
        """Recursively update a tree with a new subtree.
        
        Args:
            builder: TreeBuilder for the root tree
            tree: The root tree
            path_parts: List of path components to navigate
            new_id: ID of the new subtree
            
        Returns:
            pygit2.Oid: ID of the updated tree
        """
        if not path_parts:
            return builder.write()
        
        if len(path_parts) == 1:
            # Update the root tree directly
            builder.remove(path_parts[0])
            builder.insert(path_parts[0], new_id, pygit2.GIT_FILEMODE_TREE)
            return builder.write()
        
        # Update the subtree recursively
        subtree = tree[path_parts[0]]
        new_subtree_id = self._update_subtree(subtree, path_parts[1:], path_parts[-1], new_id)
        
        # Update the root tree with the new subtree
        builder.remove(path_parts[0])
        builder.insert(path_parts[0], new_subtree_id, pygit2.GIT_FILEMODE_TREE)
        
        return builder.write()
    
    def read_file(self, path: str) -> str:
        """Read a file from the storage.
        
        Args:
            path: Path to the file relative to the storage root
            
        Returns:
            str: Content of the file
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        # Use the transaction tree if in a transaction
        tree = self._get_current_tree()
        
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
        tree = self._get_current_tree()
        
        # Create a blob for the file content
        blob_id = self.repo.create_blob(content.encode("utf-8"))
        
        # Split the path into parts
        path_parts = path.split("/")
        filename = path_parts[-1]
        
        # If the file is in a subdirectory, we need to create or update the subtree
        if len(path_parts) > 1:
            # Create a simplified recursive approach to build the directory structure
            new_tree_id = self._write_to_subtree(tree, path_parts, 0, blob_id)
        else:
            # File is in the root directory - simple case
            builder = self.repo.TreeBuilder(tree)
            builder.insert(filename, blob_id, pygit2.GIT_FILEMODE_BLOB)
            new_tree_id = builder.write()
        
        # Get the new tree
        new_tree = self.repo[new_tree_id]
        
        # If in a transaction, update the transaction tree
        if self._in_transaction:
            self._transaction_tree = new_tree
        else:
            # Otherwise, commit the changes immediately
            self._commit_changes(f"Write {path}", new_tree_id)
    
    def _write_to_subtree(self, tree, path_parts, index, blob_id):
        """Recursively write a file to a subtree.
        
        Args:
            tree: Current tree to process
            path_parts: List of path components
            index: Current index in path_parts
            blob_id: ID of the blob to write
            
        Returns:
            pygit2.Oid: ID of the new tree
        """
        if index == len(path_parts) - 1:
            # We've reached the file to write
            builder = self.repo.TreeBuilder(tree)
            builder.insert(path_parts[index], blob_id, pygit2.GIT_FILEMODE_BLOB)
            return builder.write()
        
        # We need to create or update a subtree
        builder = self.repo.TreeBuilder(tree)
        part = path_parts[index]
        
        try:
            # Try to get the existing subtree
            entry = tree[part]
            if isinstance(entry, pygit2.Tree):
                # Subtree exists, recursively update it
                subtree = entry
                new_subtree_id = self._write_to_subtree(subtree, path_parts, index + 1, blob_id)
            else:
                # Path exists but is not a directory
                raise IOError(f"Path component is not a directory: {part}")
        except KeyError:
            # Subtree doesn't exist, create a new empty one and then update it
            empty_builder = self.repo.TreeBuilder()
            empty_tree_id = empty_builder.write()
            empty_tree = self.repo[empty_tree_id]
            
            # Recursively build the rest of the path
            new_subtree_id = self._write_to_subtree(empty_tree, path_parts, index + 1, blob_id)
        
        # Update the current tree with the new subtree
        builder.insert(part, new_subtree_id, pygit2.GIT_FILEMODE_TREE)
        return builder.write()
    
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
        
        # Get the current tree
        tree = self._get_current_tree()
        
        # Split the path into parts
        path_parts = path.split("/")
        
        # If the file is in a subdirectory, we need to update the subtree
        if len(path_parts) > 1:
            # Create a new tree by recursively updating the subtrees
            new_tree_id = self._delete_from_subtree(tree, path_parts, 0)
        else:
            # Remove the file from the root tree
            builder = self.repo.TreeBuilder(tree)
            builder.remove(path_parts[0])
            new_tree_id = builder.write()
        
        # Get the new tree
        new_tree = self.repo[new_tree_id]
        
        # If in a transaction, update the transaction tree
        if self._in_transaction:
            self._transaction_tree = new_tree
        else:
            # Otherwise, commit the changes immediately
            self._commit_changes(f"Delete {path}", new_tree_id)
    
    def _delete_from_subtree(self, tree, path_parts, index):
        """Recursively delete a file from a subtree.
        
        Args:
            tree: Current tree to process
            path_parts: List of path components
            index: Current index in path_parts
            
        Returns:
            pygit2.Oid: ID of the new tree
        """
        if index == len(path_parts) - 1:
            # We've reached the file to delete
            builder = self.repo.TreeBuilder(tree)
            builder.remove(path_parts[index])
            return builder.write()
        
        # Get the subtree for the current path component
        subtree_entry = tree[path_parts[index]]
        if not isinstance(subtree_entry, pygit2.Tree):
            raise ValueError(f"Path component is not a directory: {path_parts[index]}")
        
        # Recursively update the subtree
        new_subtree_id = self._delete_from_subtree(subtree_entry, path_parts, index + 1)
        
        # Create a new tree with the updated subtree
        builder = self.repo.TreeBuilder(tree)
        builder.remove(path_parts[index])  # Remove the old subtree
        builder.insert(path_parts[index], new_subtree_id, pygit2.GIT_FILEMODE_TREE)  # Add the new subtree
        
        return builder.write()
    
    def list_files(self, directory: str = "", pattern: str = "*") -> List[str]:
        """List files in a directory.
        
        Args:
            directory: Directory to list files from, relative to the storage root
            pattern: Pattern to match files against (glob format)
            
        Returns:
            List[str]: List of file paths relative to the storage root
        """
        import fnmatch
        
        # Get the current tree (use transaction tree if in a transaction)
        tree = self._get_current_tree()
        
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
        # Use the transaction tree if in a transaction
        tree = self._get_current_tree()
        
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
        # This will use the transaction if one is in progress
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
        # Check if the file exists using the transaction-aware file_exists method
        if not self.file_exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        # If we're in a transaction and the file has been modified in the transaction,
        # we should return the current time as the modified time
        if self._in_transaction:
            # Check if the file exists in the transaction tree but not in the branch tree
            # or if the content is different
            try:
                # Get the file from the transaction tree
                transaction_content = self.read_file(path)
                
                # Try to get the file from the branch tree
                branch_tree = self._get_tree_from_branch()
                current_tree = branch_tree
                path_parts = path.split('/')
                
                try:
                    # Navigate through the directory structure in the branch tree
                    for i, part in enumerate(path_parts[:-1]):
                        entry = current_tree[part]
                        if isinstance(entry, pygit2.Tree):
                            current_tree = entry
                        else:
                            # File was created in the transaction
                            return time.time()
                    
                    # Get the file from the final directory in the branch tree
                    filename = path_parts[-1]
                    blob = current_tree[filename]
                    
                    if isinstance(blob, pygit2.Blob):
                        branch_content = blob.data.decode("utf-8")
                        if branch_content != transaction_content:
                            # File was modified in the transaction
                            return time.time()
                    else:
                        # File was created in the transaction
                        return time.time()
                except KeyError:
                    # File was created in the transaction
                    return time.time()
            except Exception:
                # If anything goes wrong, fall back to the commit history approach
                pass
        
        # FIXME: 当前的实现反映两次 commit 的时间戳相同，无法区分。

        # Get the commit history for the file
        branch = self.repo.branches[self.branch_name]
        last_commit = None
        last_commit_time = None
        
        for commit in self.repo.walk(branch.target, pygit2.GIT_SORT_TIME):
            try:
                # Try to get the file from this commit
                tree = commit.tree
                for part in path.split('/'):
                    tree = tree[part]
                # If we got here, the file exists in this commit
                commit_time = float(commit.commit_time)
                if last_commit_time is None or commit_time > last_commit_time:
                    last_commit = commit
                    last_commit_time = commit_time
            except KeyError:
                continue
        
        if last_commit is None:
            # This should never happen as we checked file_exists,
            # unless the file only exists in the transaction
            return time.time()
        
        return last_commit_time

    
    def rename(self, old_path: str, new_path: str) -> None:
        """Rename a file or move it to a new location.
        
        Args:
            old_path: Current path of the file relative to the storage root
            new_path: New path for the file relative to the storage root
            
        Raises:
            FileNotFoundError: If the source file does not exist
            FileExistsError: If the destination file already exists
        """
        # Check if source file exists
        if not self.file_exists(old_path):
            raise FileNotFoundError(f"Source file not found: {old_path}")
        
        # Check if destination file already exists
        if self.file_exists(new_path):
            raise FileExistsError(f"Destination file already exists: {new_path}")
        
        # Use a transaction to perform the rename as a single operation
        was_in_transaction = self._in_transaction
        
        try:
            if not was_in_transaction:
                self.begin_transaction()
            
            # Read the content of the source file
            content = self.read_file(old_path)
            
            # Create parent directories for the destination if needed
            new_dir = "/".join(new_path.split("/")[:-1])
            if new_dir and not any(self.list_files(new_dir)):
                self.create_directory(new_dir)
            
            # Write the content to the new location
            self.write_file(new_path, content)
            
            # Delete the old file
            self.delete_file(old_path)
            
            # Commit the transaction if we started it
            if not was_in_transaction:
                self.commit_transaction(f"Renamed {old_path} to {new_path}")
        except Exception:
            # Abort the transaction if we started it and there was an error
            if not was_in_transaction:
                self.abort_transaction()
            raise
    
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

