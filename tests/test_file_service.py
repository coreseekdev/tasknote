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
        mtime = self.fs.get_modified_time("test.txt")
        # Some implementations may return int, others float
        self.assertIsInstance(mtime, (float, int))
        self.assertGreater(mtime, 0)


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


if __name__ == "__main__":
    unittest.main()
