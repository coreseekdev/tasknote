"""Tests for the NumberingService.

This module contains tests for the TaskNumberingService class which is exported
as NumberingService from the services package.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

import yaml

from tasknotes.services import NumberingService
from tasknotes.interface.file_service import FileService


class MockFileService(FileService):
    """Mock implementation of FileService for testing."""
    
    def __init__(self):
        self.files = {}
        self._transaction_active = False
        self._transaction_files = {}
    
    def read_file(self, path: str) -> str:
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        return self.files[path]
    
    def write_file(self, path: str, content: str) -> None:
        self.files[path] = content
    
    def delete_file(self, path: str) -> None:
        if path in self.files:
            del self.files[path]
        else:
            raise FileNotFoundError(f"File not found: {path}")
    
    def list_files(self, directory: str = "", pattern: str = "*") -> list:
        return [path for path in self.files.keys() if path.startswith(directory)]
    
    def file_exists(self, path: str) -> bool:
        return path in self.files
    
    def create_directory(self, path: str) -> None:
        pass
    
    def get_modified_time(self, path: str) -> float:
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        return 0.0
        
    def transaction(self, commit_message: str = None):
        """Start a transaction."""
        return self
        
    def begin_transaction(self) -> None:
        """Begin a transaction."""
        self._transaction_active = True
        self._transaction_files = {}
        
    def abort_transaction(self) -> None:
        """Abort a transaction."""
        self._transaction_active = False
        self._transaction_files = {}
        
    def __enter__(self):
        self.begin_transaction()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # No exception, commit the transaction
            for path, content in self._transaction_files.items():
                self.files[path] = content
        self._transaction_active = False
        self._transaction_files = {}


class TestNumberingService(unittest.TestCase):
    """Test cases for the NumberingService class."""
    
    def setUp(self):
        """Set up the test environment."""
        self.file_service = MockFileService()
        self.service = NumberingService(self.file_service)
    
    def test_initialization(self):
        """Test that the service initializes with default values."""
        # Check that the default prefix is set
        self.assertEqual(self.service.get_default_prefix(), "TASK")
        
        # Check that the default prefix has a sequence number of 0
        self.assertEqual(self.service.get_current_number(), 0)
        
        # Check that the prefixes file was created
        self.assertTrue(self.file_service.file_exists("prefixes.yaml"))
        
        # Check the content of the prefixes file
        content = self.file_service.read_file("prefixes.yaml")
        data = yaml.safe_load(content)
        self.assertEqual(data["default"], "TASK")
        self.assertEqual(data["TASK"], 0)
    
    def test_get_next_number(self):
        """Test getting the next number for a prefix."""
        # Get the next number for the default prefix
        identifier = self.service.get_next_number()
        self.assertEqual(identifier, "TASK-001")
        
        # Get the next number for the default prefix again
        identifier = self.service.get_next_number()
        self.assertEqual(identifier, "TASK-002")
        
        # Get the next number for a different prefix
        identifier = self.service.get_next_number("PROJ")
        self.assertEqual(identifier, "PROJ-001")
        
        # Get the next number for that prefix again
        identifier = self.service.get_next_number("PROJ")
        self.assertEqual(identifier, "PROJ-002")
        
        # Check that the prefixes file was updated
        content = self.file_service.read_file("prefixes.yaml")
        data = yaml.safe_load(content)
        self.assertEqual(data["TASK"], 2)
        self.assertEqual(data["PROJ"], 2)
    
    def test_set_default_prefix(self):
        """Test setting the default prefix."""
        # Set a new default prefix
        self.service.set_default_prefix("PROJ")
        
        # Check that the default prefix was updated
        self.assertEqual(self.service.get_default_prefix(), "PROJ")
        
        # Get the next number for the default prefix
        identifier = self.service.get_next_number()
        self.assertEqual(identifier, "PROJ-001")
        
        # Check that the prefixes file was updated
        content = self.file_service.read_file("prefixes.yaml")
        data = yaml.safe_load(content)
        self.assertEqual(data["default"], "PROJ")
        self.assertEqual(data["PROJ"], 1)
    
    def test_get_current_number(self):
        """Test getting the current number for a prefix."""
        # Get the current number for the default prefix
        number = self.service.get_current_number()
        self.assertEqual(number, 0)
        
        # Get the next number for the default prefix
        self.service.get_next_number()
        
        # Get the current number for the default prefix again
        number = self.service.get_current_number()
        self.assertEqual(number, 1)
        
        # Get the current number for a non-existent prefix
        number = self.service.get_current_number("NONEXISTENT")
        self.assertEqual(number, 0)
    
    def test_get_all_prefixes(self):
        """Test getting all prefixes."""
        # Initially, only the default prefix exists
        prefixes = self.service.get_all_prefixes()
        self.assertEqual(prefixes, {"TASK": 0})
        
        # Add a new prefix
        self.service.get_next_number("PROJ")
        
        # Get all prefixes again
        prefixes = self.service.get_all_prefixes()
        self.assertEqual(prefixes, {"TASK": 0, "PROJ": 1})
    
    def test_reset_prefix(self):
        """Test resetting a prefix."""
        # Get the next number for the default prefix
        self.service.get_next_number()
        self.service.get_next_number()
        
        # Reset the default prefix
        self.service.reset_prefix("TASK")
        
        # Get the current number for the default prefix
        number = self.service.get_current_number()
        self.assertEqual(number, 0)
        
        # Get the next number for the default prefix
        identifier = self.service.get_next_number()
        self.assertEqual(identifier, "TASK-001")
        
        # Reset the default prefix to a specific value
        self.service.reset_prefix("TASK", 42)
        
        # Get the current number for the default prefix
        number = self.service.get_current_number()
        self.assertEqual(number, 42)
        
        # Get the next number for the default prefix
        identifier = self.service.get_next_number()
        self.assertEqual(identifier, "TASK-043")
    
    def test_file_not_found(self):
        """Test behavior when the prefixes file is not found."""
        # Delete the prefixes file
        self.file_service.delete_file("prefixes.yaml")
        
        # Create a new service
        service = NumberingService(self.file_service)
        
        # Check that the default prefix is set
        self.assertEqual(service.get_default_prefix(), "TASK")
        
        # Check that the prefixes file was recreated
        self.assertTrue(self.file_service.file_exists("prefixes.yaml"))
    
    def test_corrupted_file(self):
        """Test behavior when the prefixes file is corrupted."""
        # Write corrupted YAML to the prefixes file
        self.file_service.write_file("prefixes.yaml", "corrupted: yaml: file:")
        
        # Create a new service
        service = NumberingService(self.file_service)
        
        # Check that the default prefix is set
        self.assertEqual(service.get_default_prefix(), "TASK")
        
        # Check that the prefixes file was recreated
        content = self.file_service.read_file("prefixes.yaml")
        data = yaml.safe_load(content)
        self.assertEqual(data["default"], "TASK")
        self.assertEqual(data["TASK"], 0)
    
    def test_large_numbers(self):
        """Test behavior with large sequence numbers."""
        # Set a large sequence number
        self.service.reset_prefix("TASK", 999)
        
        # Get the next number
        identifier = self.service.get_next_number()
        self.assertEqual(identifier, "TASK-1000")
        
        # Set an even larger sequence number
        self.service.reset_prefix("TASK", 9999)
        
        # Get the next number
        identifier = self.service.get_next_number()
        self.assertEqual(identifier, "TASK-10000")
    
    def test_save_error(self):
        """Test behavior when saving the prefixes file fails."""
        # Create a mock that raises an exception when write_file is called
        file_service = MockFileService()
        file_service.write_file = MagicMock(side_effect=Exception("Failed to write file"))
        
        # Patch the print function to capture the error message
        with patch('builtins.print') as mock_print:
            service = NumberingService(file_service)
            
            # Get the next number
            service.get_next_number()
            
            # Check that the error was logged
            mock_print.assert_called_with("Error saving prefixes: Failed to write file")


if __name__ == "__main__":
    unittest.main()
