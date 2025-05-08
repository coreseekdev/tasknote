#!/usr/bin/env python
"""
Manual test script for TaskNoteEnv class.
This script tests the core functionality of TaskNoteEnv without relying on unittest.
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
import pygit2

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the TaskNoteEnv class
from tasknotes.core.task_env import TaskNoteEnv

def run_tests():
    """Run manual tests for TaskNoteEnv."""
    print("Testing TaskNoteEnv...")
    
    # Create a temporary directory for tests
    test_dir = tempfile.mkdtemp()
    print(f"Created test directory: {test_dir}")
    
    try:
        # Test 1: Initialize with a non-git repository
        print("\nTest 1: Initialize with a non-git repository")
        env = TaskNoteEnv(test_dir)
        print(f"Is git repo: {env.is_git_repo()}")
        assert not env.is_git_repo(), "Should not be a git repo"
        
        # Test 2: Check if TaskNotes is initialized (should be False initially)
        print("\nTest 2: Check if TaskNotes is initialized")
        is_init = env.is_tasknote_init()
        print(f"Is TaskNotes initialized: {is_init}")
        assert not is_init, "TaskNotes should not be initialized yet"
        
        # Test 3: Initialize TaskNotes in LOCAL mode
        print("\nTest 3: Initialize TaskNotes in LOCAL mode")
        result = env.tasknote_init(mode="LOCAL")
        print(f"Initialization result: {result}")
        assert result, "Initialization should succeed"
        
        # Test 4: Check if TaskNotes is initialized after initialization
        print("\nTest 4: Check if TaskNotes is initialized after initialization")
        is_init = env.is_tasknote_init()
        print(f"Is TaskNotes initialized: {is_init}")
        assert is_init, "TaskNotes should be initialized now"
        
        # Test 5: Check that .tasknote directory exists
        print("\nTest 5: Check that .tasknote directory exists")
        tasknote_dir = Path(test_dir) / ".tasknote"
        print(f"TaskNotes directory exists: {tasknote_dir.exists()}")
        assert tasknote_dir.exists(), ".tasknote directory should exist"
        assert tasknote_dir.is_dir(), ".tasknote should be a directory"
        
        # Test 6: Create a git repository for further tests
        print("\nTest 6: Create a git repository for further tests")
        git_repo_path = os.path.join(test_dir, "git_repo")
        os.makedirs(git_repo_path)
        repo = pygit2.init_repository(git_repo_path)
        print(f"Created git repository at: {git_repo_path}")
        
        # Test 7: Initialize with a git repository
        print("\nTest 7: Initialize with a git repository")
        git_env = TaskNoteEnv(git_repo_path)
        print(f"Is git repo: {git_env.is_git_repo()}")
        assert git_env.is_git_repo(), "Should be a git repo"
        
        # Test 8: Initialize TaskNotes in GIT mode
        print("\nTest 8: Initialize TaskNotes in GIT mode")
        # Create an initial commit to have a HEAD
        try:
            # Create an initial commit
            index = repo.index
            author = pygit2.Signature("Test User", "test@example.com")
            tree_id = index.write_tree()
            repo.create_commit("HEAD", author, author, "Initial commit", tree_id, [])
            print("Created initial commit")
            
            # Initialize TaskNotes in GIT mode
            result = git_env.tasknote_init(mode="GIT")
            print(f"Initialization result: {result}")
            assert result, "Initialization should succeed"
            
            # Check that tasknote branch exists
            print(f"Branches: {list(repo.branches)}")
            assert "tasknote" in repo.branches, "tasknote branch should exist"
            print("TaskNotes GIT mode initialization successful")
        except Exception as e:
            print(f"Error during GIT mode initialization: {e}")
            raise
        
        print("\nAll tests passed!")
        return True
    
    except AssertionError as e:
        print(f"Test failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    finally:
        # Clean up
        try:
            shutil.rmtree(test_dir)
            print(f"\nCleaned up test directory: {test_dir}")
        except Exception as e:
            print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
