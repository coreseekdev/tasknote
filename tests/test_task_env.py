"""Tests for the TaskNoteEnv class."""

import os
import sys
import shutil
import tempfile
from pathlib import Path
import unittest
import unittest.mock as mock
import pygit2

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tasknotes.core.task_env import TaskNoteEnv


class TestTaskNoteEnv(unittest.TestCase):
    """Test cases for the TaskNoteEnv class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self.test_dir))

    def test_init_non_git_repo(self):
        """Test initialization with a non-git repository."""
        env = TaskNoteEnv(self.test_dir)
        self.assertFalse(env.is_git_repo())
        self.assertIsNone(env._repo)

    def test_is_tasknote_init_false(self):
        """Test is_tasknote_init returns False for non-initialized directory."""
        env = TaskNoteEnv(self.test_dir)
        self.assertFalse(env.is_tasknote_init())

    def test_tasknote_init_local(self):
        """Test initializing TaskNotes in LOCAL mode."""
        env = TaskNoteEnv(self.test_dir)
        result = env.tasknote_init(mode="LOCAL")
        self.assertTrue(result)
        self.assertTrue(env.is_tasknote_init())
        
        # Check that .tasknote directory exists
        tasknote_dir = Path(self.test_dir) / ".tasknote"
        self.assertTrue(tasknote_dir.exists())
        self.assertTrue(tasknote_dir.is_dir())

    def test_init_git_repo(self):
        """Test initialization with a git repository."""
        # Create a git repository in the test directory
        repo_path = os.path.join(self.test_dir, "git_repo")
        os.makedirs(repo_path)
        pygit2.init_repository(repo_path)
        
        env = TaskNoteEnv(repo_path)
        self.assertTrue(env.is_git_repo())
        self.assertIsNotNone(env._repo)

    def test_tasknote_init_git(self):
        """Test initializing TaskNotes in GIT mode."""
        # Create a git repository in the test directory
        repo_path = os.path.join(self.test_dir, "git_repo")
        os.makedirs(repo_path)
        repo = pygit2.init_repository(repo_path)
        
        # Create an initial commit to have a HEAD
        index = repo.index
        author = pygit2.Signature("Test User", "test@example.com")
        tree_id = index.write_tree()
        repo.create_commit("HEAD", author, author, "Initial commit", tree_id, [])
        
        env = TaskNoteEnv(repo_path)
        result = env.tasknote_init(mode="GIT")
        self.assertTrue(result)
        self.assertTrue(env.is_tasknote_init())
        
        # Check that tasknote branch exists
        self.assertIn("tasknote", env._repo.branches)
        
        # Verify .tasknote directory doesn't exist for GIT mode
        self.assertFalse(os.path.exists(os.path.join(repo_path, ".tasknote")))

    def test_get_user_signature(self):
        """Test getting user signature."""
        env = TaskNoteEnv(self.test_dir)
        signature = env._get_user_signature()
        
        # Should return a default signature for non-git repos
        self.assertIsInstance(signature, pygit2.Signature)
        self.assertEqual(signature.name, "TaskNotes User")
        self.assertEqual(signature.email, "user@tasknotes")

    def test_get_repo_root(self):
        """Test getting repository root."""
        env = TaskNoteEnv(self.test_dir)
        
        # For non-git repos, should return None
        self.assertIsNone(env.get_repo_root())
        
        # Create a git repository
        repo_path = os.path.join(self.test_dir, "git_repo")
        os.makedirs(repo_path)
        pygit2.init_repository(repo_path)
        
        env = TaskNoteEnv(repo_path)
        self.assertEqual(env.get_repo_root(), Path(repo_path))

    def test_idempotent_init(self):
        """Test that initializing multiple times is idempotent."""
        env = TaskNoteEnv(self.test_dir)
        
        # First initialization
        result1 = env.tasknote_init(mode="LOCAL")
        self.assertTrue(result1)
        
        # Second initialization should also return True but not create anything new
        result2 = env.tasknote_init(mode="LOCAL")
        self.assertTrue(result2)
        
        # Try with different mode - should still return True without changing anything
        result3 = env.tasknote_init(mode="GIT")
        self.assertTrue(result3)
        
        # Check that we still have the LOCAL mode initialization
        tasknote_dir = Path(self.test_dir) / ".tasknote"
        self.assertTrue(tasknote_dir.exists())
        self.assertTrue(tasknote_dir.is_dir())


if __name__ == "__main__":
    unittest.main()
