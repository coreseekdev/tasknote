import os
import tempfile
import unittest
from pathlib import Path
from typing import Callable, Optional, List

from tasknotes.interface.file_service import FileService
from tasknotes.core.fs_local import LocalFilesystem
from tasknotes.core.task_env import TaskNoteEnv


def create_file_service_factory(test_dir: Path) -> Callable[[], FileService]:
    """Create a factory function that returns a FileService instance.
    
    This factory function can be reused by other FileService implementation tests.
    
    Args:
        test_dir: The directory to use for testing
        
    Returns:
        A factory function that returns a FileService instance
    """
    def factory() -> FileService:
        return LocalFilesystem(test_dir)
    
    return factory


class TestLocalFilesystem(unittest.TestCase):
    """Test cases for the LocalFilesystem class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create a factory function for creating FileService instances
        self.create_fs = create_file_service_factory(self.test_dir)
        
        # Create a FileService instance for testing
        self.fs = self.create_fs()
    
    def tearDown(self):
        """Clean up the test environment."""
        self.temp_dir.cleanup()
    
    def test_init(self):
        """Test initialization of LocalFilesystem."""
        # Test that the base directory is created
        self.assertTrue(self.test_dir.exists())
        self.assertTrue(self.test_dir.is_dir())
        
        # Test with a non-existent directory
        new_dir = self.test_dir / "new_dir"
        fs = LocalFilesystem(new_dir)
        self.assertTrue(new_dir.exists())
        self.assertTrue(new_dir.is_dir())
    
    def test_write_and_read_file(self):
        """Test writing and reading files."""
        # Test writing a file
        test_content = "Hello, world!"
        self.fs.write_file("test.txt", test_content)
        
        # Check that the file exists
        file_path = self.test_dir / "test.txt"
        self.assertTrue(file_path.exists())
        self.assertTrue(file_path.is_file())
        
        # Test reading the file
        content = self.fs.read_file("test.txt")
        self.assertEqual(content, test_content)
        
        # Test writing to a file in a subdirectory
        self.fs.write_file("subdir/test.txt", test_content)
        file_path = self.test_dir / "subdir" / "test.txt"
        self.assertTrue(file_path.exists())
        self.assertTrue(file_path.is_file())
        
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
        self.assertFalse(self.fs.file_exists("testdir"))
    
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
        dir_path = self.test_dir / "testdir"
        self.assertTrue(dir_path.exists())
        self.assertTrue(dir_path.is_dir())
        
        # Test creating nested directories
        self.fs.create_directory("parent/child/grandchild")
        dir_path = self.test_dir / "parent" / "child" / "grandchild"
        self.assertTrue(dir_path.exists())
        self.assertTrue(dir_path.is_dir())
        
        # Test creating an existing directory (should not raise an error)
        self.fs.create_directory("testdir")
    
    def test_list_files(self):
        """Test listing files in a directory."""
        # Test with an empty directory
        files = self.fs.list_files()
        self.assertEqual(files, [])
        
        # Test with files in the root directory
        self.fs.write_file("test1.txt", "Hello, world!")
        self.fs.write_file("test2.txt", "Hello, again!")
        files = self.fs.list_files()
        self.assertEqual(sorted(files), ["test1.txt", "test2.txt"])
        
        # Test with files in a subdirectory
        self.fs.create_directory("subdir")
        self.fs.write_file("subdir/test3.txt", "Hello, subdirectory!")
        files = self.fs.list_files("subdir")
        self.assertEqual(files, ["subdir/test3.txt"])
        
        # Test with a pattern
        self.fs.write_file("test3.md", "Markdown file")
        files = self.fs.list_files("", "*.md")
        self.assertEqual(files, ["test3.md"])
        
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
        self.assertIsInstance(mtime, float)
        self.assertGreater(mtime, 0)
        
        # Test that the modified time changes when the file is updated
        import time
        time.sleep(0.1)  # Ensure the timestamp will be different
        self.fs.write_file("test.txt", "Updated content")
        new_mtime = self.fs.get_modified_time("test.txt")
        self.assertGreater(new_mtime, mtime)


if __name__ == "__main__":
    unittest.main()
