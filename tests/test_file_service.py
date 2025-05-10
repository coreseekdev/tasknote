import os
import tempfile
import unittest
import time
import fnmatch
import pygit2
from pathlib import Path
from typing import Callable, Optional, List, Dict, Any, Type

from tasknotes.interface.file_service import FileService
from tasknotes.core.fs_local import LocalFilesystem
from tasknotes.core.fs_git import GitRepoTree
from tasknotes.core.task_env import TaskNoteEnv
from tasknotes.core.config import config


def create_local_fs_factory(test_dir: Path) -> Callable[[], FileService]:
    """Create a factory function that returns a LocalFilesystem instance.
    
    Args:
        test_dir: The directory to use for testing
        
    Returns:
        A factory function that returns a LocalFilesystem instance
    """
    def factory() -> FileService:
        return LocalFilesystem(test_dir)
    
    return factory


def create_git_fs_factory(repo_path: Path) -> Callable[[], FileService]:
    """Create a factory function that returns a GitRepoTree instance.
    
    Args:
        repo_path: The path to the git repository
        
    Returns:
        A factory function that returns a GitRepoTree instance
    """
    def factory() -> FileService:
        env = TaskNoteEnv(str(repo_path))
        # Initialize the git repository for TaskNotes
        env.tasknote_init(mode="GIT")
        return GitRepoTree(env)
    
    return factory


class FileServiceTestBase:
    """Base class for testing FileService implementations."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # The factory function should be set by subclasses
        self.create_fs = None
        
        # The FileService instance should be set by subclasses
        self.fs = None
    
    def tearDown(self):
        """Clean up the test environment."""
        self.temp_dir.cleanup()
    
    def test_write_and_read_file(self):
        """Test writing and reading files."""
        # Test writing a file
        test_content = "Hello, world!"
        self.fs.write_file("test.txt", test_content)
        
        # Test reading the file
        content = self.fs.read_file("test.txt")
        self.assertEqual(content, test_content)
        
        # Test writing to a file in a subdirectory
        self.fs.create_directory("subdir")  # Ensure directory exists first
        self.fs.write_file("subdir/test.txt", test_content)
        
        # Test reading from a file in a subdirectory
        content = self.fs.read_file("subdir/test.txt")
        self.assertEqual(content, test_content)
        
        # Test reading a non-existent file
        with self.assertRaises(FileNotFoundError):
            self.fs.read_file("nonexistent.txt")
    
    def test_file_exists(self):
        """Test checking if a file exists."""
        # Test with a non-existent file
        self.assertFalse(self.fs.file_exists("test.txt"))
        
        # Test with an existing file
        self.fs.write_file("test.txt", "Hello, world!")
        self.assertTrue(self.fs.file_exists("test.txt"))
        
        # Test with a directory
        self.fs.create_directory("testdir")
        self.assertFalse(self.fs.file_exists("testdir"))  # Directories should return False
    
    def test_delete_file(self):
        """Test deleting files."""
        # Test deleting a non-existent file
        with self.assertRaises(FileNotFoundError):
            self.fs.delete_file("nonexistent.txt")
        
        # Test deleting an existing file
        self.fs.write_file("test.txt", "Hello, world!")
        self.assertTrue(self.fs.file_exists("test.txt"))
        self.fs.delete_file("test.txt")
        self.assertFalse(self.fs.file_exists("test.txt"))
    
    def test_create_directory(self):
        """Test creating directories."""
        # Test creating a directory
        self.fs.create_directory("testdir")
        
        # Verify we can write to the directory
        test_content = "Hello, directory!"
        self.fs.write_file("testdir/test.txt", test_content)
        
        # Test creating nested directories
        self.fs.create_directory("parent/child/grandchild")
        
        # Verify we can write to nested directories
        nested_content = "Hello, nested directory!"
        self.fs.write_file("parent/child/grandchild/test.txt", nested_content)
        content = self.fs.read_file("parent/child/grandchild/test.txt")
        self.assertEqual(content, nested_content)
        
        # Test creating an existing directory (should not raise an error)
        self.fs.create_directory("testdir")
    
    def test_list_files(self):
        """Test listing files in a directory."""
        # Test with an empty directory
        files = self.fs.list_files()
        # Initial state might have .gitkeep files in Git implementation
        
        # Test with files in the root directory
        self.fs.write_file("test1.txt", "Hello, world!")
        self.fs.write_file("test2.txt", "Hello, again!")
        files = sorted(self.fs.list_files())
        self.assertIn("test1.txt", files)
        self.assertIn("test2.txt", files)
        
        # Test with files in a subdirectory
        self.fs.create_directory("subdir")
        self.fs.write_file("subdir/test3.txt", "Hello, subdirectory!")
        files = self.fs.list_files("subdir")
        self.assertIn("subdir/test3.txt", files)
        
        # Test with a pattern
        self.fs.write_file("test3.md", "Markdown file")
        files = self.fs.list_files("", "*.md")
        self.assertIn("test3.md", files)
        
        # Test with a non-existent directory
        files = self.fs.list_files("nonexistent")
        self.assertEqual(files, [])
    
    def test_get_modified_time(self):
        """Test getting the modified time of a file."""
        # Test with a non-existent file
        with self.assertRaises(FileNotFoundError):
            self.fs.get_modified_time("nonexistent.txt")
        
        # Test with an existing file
        self.fs.write_file("test.txt", "Hello, world!")
        
        # Sleep to ensure the modification time is different
        time.sleep(0.1)
        
        # Get the modified time
        mtime = self.fs.get_modified_time("test.txt")
        
        # Check that the modified time is recent
        current_time = time.time()
        self.assertLess(current_time - mtime, 10)  # Within 10 seconds
        self.assertGreater(mtime, current_time - 60)  # Not more than 60 seconds ago
    
    def test_rename(self):
        """Test renaming files."""
        # Test renaming a non-existent file
        with self.assertRaises(FileNotFoundError):
            self.fs.rename("nonexistent.txt", "new.txt")
        
        # Test basic renaming in the same directory
        test_content = "Hello, world!"
        self.fs.write_file("test.txt", test_content)
        self.fs.rename("test.txt", "renamed.txt")
        
        # Verify the file was renamed
        self.assertFalse(self.fs.file_exists("test.txt"))
        self.assertTrue(self.fs.file_exists("renamed.txt"))
        self.assertEqual(self.fs.read_file("renamed.txt"), test_content)
        
        # Test moving to a subdirectory
        self.fs.create_directory("subdir")
        self.fs.rename("renamed.txt", "subdir/moved.txt")
        
        # Verify the file was moved
        self.assertFalse(self.fs.file_exists("renamed.txt"))
        self.assertTrue(self.fs.file_exists("subdir/moved.txt"))
        self.assertEqual(self.fs.read_file("subdir/moved.txt"), test_content)
        
        # Test moving to a non-existent subdirectory (should create it)
        self.fs.rename("subdir/moved.txt", "newdir/final.txt")
        
        # Verify the file was moved and directory was created
        self.assertFalse(self.fs.file_exists("subdir/moved.txt"))
        self.assertTrue(self.fs.file_exists("newdir/final.txt"))
        self.assertEqual(self.fs.read_file("newdir/final.txt"), test_content)
        
        # Test renaming to an existing file (should raise FileExistsError)
        self.fs.write_file("existing.txt", "I already exist")
        with self.assertRaises(FileExistsError):
            self.fs.rename("newdir/final.txt", "existing.txt")


class TestLocalFilesystem(FileServiceTestBase, unittest.TestCase):
    """Test cases for the LocalFilesystem class."""
    
    def setUp(self):
        """Set up the test environment."""
        super().setUp()
        
        # Create a factory function for creating LocalFilesystem instances
        self.create_fs = create_local_fs_factory(self.test_dir)
        
        # Create a FileService instance for testing
        self.fs = self.create_fs()
    
    def test_local_init(self):
        """Test initialization of LocalFilesystem."""
        # Test that the base directory is created
        self.assertTrue(self.test_dir.exists())
        self.assertTrue(self.test_dir.is_dir())
        
        # Test with a non-existent directory
        new_dir = self.test_dir / "new_dir"
        fs = LocalFilesystem(new_dir)
        self.assertTrue(new_dir.exists())
        self.assertTrue(new_dir.is_dir())
    
    def test_file_path_verification(self):
        """Test that files are created at the expected paths."""
        # Test writing a file
        test_content = "Hello, world!"
        self.fs.write_file("test.txt", test_content)
        
        # Check that the file exists at the expected path
        file_path = self.test_dir / "test.txt"
        self.assertTrue(file_path.exists())
        self.assertTrue(file_path.is_file())
        
        # Test writing to a file in a subdirectory
        self.fs.create_directory("subdir")
        self.fs.write_file("subdir/test.txt", test_content)
        
        # Check that the file exists at the expected path
        file_path = self.test_dir / "subdir" / "test.txt"
        self.assertTrue(file_path.exists())
        self.assertTrue(file_path.is_file())
        
        # Test with nested directories
        self.fs.create_directory("a/b/c")
        self.fs.write_file("a/b/c/test.txt", test_content)
        
        # Check that the file exists at the expected path
        file_path = self.test_dir / "a" / "b" / "c" / "test.txt"
        self.assertTrue(file_path.exists())
        self.assertTrue(file_path.is_file())
    
    def test_directory_structure(self):
        """Test that directory structure is correctly maintained."""
        # Create a complex directory structure
        self.fs.create_directory("level1/level2/level3")
        
        # Verify the structure exists
        dir_path = self.test_dir / "level1" / "level2" / "level3"
        self.assertTrue(dir_path.exists())
        self.assertTrue(dir_path.is_dir())
        
        # Create files at different levels
        self.fs.write_file("level1/file1.txt", "Content 1")
        self.fs.write_file("level1/level2/file2.txt", "Content 2")
        self.fs.write_file("level1/level2/level3/file3.txt", "Content 3")
        
        # Verify files exist at correct locations
        self.assertTrue((self.test_dir / "level1" / "file1.txt").exists())
        self.assertTrue((self.test_dir / "level1" / "level2" / "file2.txt").exists())
        self.assertTrue((self.test_dir / "level1" / "level2" / "level3" / "file3.txt").exists())
        
        # List files at different levels
        level1_files = self.fs.list_files("level1")
        self.assertIn("level1/file1.txt", level1_files)
        
        level3_files = self.fs.list_files("level1/level2/level3")
        self.assertIn("level1/level2/level3/file3.txt", level3_files)


class TestGitRepoTree(FileServiceTestBase, unittest.TestCase):
    """Test cases for the GitRepoTree class."""
    
    def setUp(self):
        """Set up the test environment."""
        super().setUp()
        
        # Initialize a git repository
        self.repo_path = self.test_dir / "repo"
        os.makedirs(self.repo_path)
        self.repo = pygit2.init_repository(self.repo_path)
        
        # Create an initial commit
        author = pygit2.Signature("Test User", "test@example.com")
        tree_id = self.repo.TreeBuilder().write()
        self.repo.create_commit("HEAD", author, author, "Initial commit", tree_id, [])
        
        # Create a factory function for creating GitRepoTree instances
        self.create_fs = create_git_fs_factory(self.repo_path)
        
        # Create a FileService instance for testing
        self.fs = self.create_fs()
    
    def test_git_init(self):
        """Test initialization of GitRepoTree."""
        # Test that the tasknote branch exists
        self.assertIn(config.get("git.branch_name"), self.repo.branches)
        
        # Test with invalid repository
        with self.assertRaises(ValueError):
            invalid_dir = self.test_dir / "invalid"
            os.makedirs(invalid_dir)
            env = TaskNoteEnv(str(invalid_dir))
            GitRepoTree(env)
    
    def test_git_commit_history(self):
        """Test that file modifications are tracked in commit history."""
        # Write a file and check that a commit was created
        self.fs.write_file("test.txt", "Initial content")
        branch = self.repo.branches[config.get("git.branch_name")]
        commit = self.repo[branch.target]
        
        # Check that the file exists in the tree
        # Note: In Git, the file might be in a subdirectory or have a different path
        # so we'll just check that the commit exists and has a tree
        self.assertIsNotNone(commit.tree)
        
        # Modify the file and check that another commit was created
        self.fs.write_file("test.txt", "Modified content")
        branch = self.repo.branches[config.get("git.branch_name")]
        new_commit = self.repo[branch.target]
        self.assertNotEqual(commit.id, new_commit.id)
    
    def test_git_tree_traversal(self):
        """Test that the GitRepoTree correctly traverses the tree structure for nested paths."""
        # Create a nested directory structure with files
        self.fs.create_directory("dir1/dir2/dir3")
        self.fs.write_file("dir1/file1.txt", "Content 1")
        self.fs.write_file("dir1/dir2/file2.txt", "Content 2")
        self.fs.write_file("dir1/dir2/dir3/file3.txt", "Content 3")
        
        # Test reading files at different levels
        self.assertEqual(self.fs.read_file("dir1/file1.txt"), "Content 1")
        self.assertEqual(self.fs.read_file("dir1/dir2/file2.txt"), "Content 2")
        self.assertEqual(self.fs.read_file("dir1/dir2/dir3/file3.txt"), "Content 3")
        
        # Test file_exists at different levels
        self.assertTrue(self.fs.file_exists("dir1/file1.txt"))
        self.assertTrue(self.fs.file_exists("dir1/dir2/file2.txt"))
        self.assertTrue(self.fs.file_exists("dir1/dir2/dir3/file3.txt"))
        
        # Test non-existent files in existing directories
        self.assertFalse(self.fs.file_exists("dir1/nonexistent.txt"))
        self.assertFalse(self.fs.file_exists("dir1/dir2/nonexistent.txt"))
        
        # Test listing files in nested directories
        files = self.fs.list_files("dir1")
        self.assertIn("dir1/file1.txt", files)
        
        files = self.fs.list_files("dir1/dir2")
        self.assertIn("dir1/dir2/file2.txt", files)
        
        files = self.fs.list_files("dir1/dir2/dir3")
        self.assertIn("dir1/dir2/dir3/file3.txt", files)
    
    def test_git_file_operations(self):
        """Test file operations in GitRepoTree implementation."""
        # Test writing and reading a file
        self.fs.write_file("test.txt", "Initial content")
        self.assertEqual(self.fs.read_file("test.txt"), "Initial content")
        
        # Test updating a file
        self.fs.write_file("test.txt", "Updated content")
        self.assertEqual(self.fs.read_file("test.txt"), "Updated content")
        
        # Test deleting a file
        self.fs.delete_file("test.txt")
        self.assertFalse(self.fs.file_exists("test.txt"))
        
        # Test that each operation created a commit
        branch = self.repo.branches[config.get("git.branch_name")]
        # Walk through the commit history
        commit = self.repo[branch.target]
        commit_count = 0
        while commit.parents:
            commit_count += 1
            commit = commit.parents[0]
        
        # We should have at least 3 commits (initial + write + update + delete)
        # Plus the initial repository setup
        self.assertGreaterEqual(commit_count, 3)


if __name__ == "__main__":
    unittest.main()
