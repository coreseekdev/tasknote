"""File service for TaskNotes.

This module provides the FileService interface and implementations for different storage backends:
- LocalFilesystem: For storing tasks in the .tasknote directory
- GitRepoTree: For storing tasks in a git branch
"""

import os
import shutil
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Dict, Any, BinaryIO, Set, Iterator, Generator, ContextManager


class FileService(ABC):
    """Interface for file operations in TaskNotes.
    
    This abstract class defines the interface for file operations
    that can be implemented by different storage backends.
    """
    
    @abstractmethod
    def read_file(self, path: str) -> str:
        """Read a file from the storage.
        
        Args:
            path: Path to the file relative to the storage root
            
        Returns:
            str: Content of the file
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        pass
    
    @abstractmethod
    def write_file(self, path: str, content: str) -> None:
        """Write content to a file in the storage.
        
        Args:
            path: Path to the file relative to the storage root
            content: Content to write to the file
            
        Raises:
            IOError: If the file cannot be written
        """
        pass
    
    @abstractmethod
    def delete_file(self, path: str) -> None:
        """Delete a file from the storage.
        
        Args:
            path: Path to the file relative to the storage root
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        pass
    
    @abstractmethod
    def list_files(self, directory: str = "", pattern: str = "*") -> List[str]:
        """List files in a directory.
        
        Args:
            directory: Directory to list files from, relative to the storage root
            pattern: Pattern to match files against (glob format)
            
        Returns:
            List[str]: List of file paths relative to the storage root
        """
        pass
    
    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in the storage.
        
        Args:
            path: Path to the file relative to the storage root
            
        Returns:
            bool: True if the file exists, False otherwise
        """
        pass
    
    @abstractmethod
    def create_directory(self, path: str) -> None:
        """Create a directory in the storage.
        
        Args:
            path: Path to the directory relative to the storage root
            
        Raises:
            IOError: If the directory cannot be created
        """
        pass
    
    @abstractmethod
    def get_modified_time(self, path: str) -> float:
        """Get the last modified time of a file.
        
        Args:
            path: Path to the file relative to the storage root
            
        Returns:
            float: Last modified time as a timestamp
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        pass
    
    @abstractmethod
    def rename(self, old_path: str, new_path: str) -> None:
        """Rename a file or move it to a new location.
        
        Args:
            old_path: Current path of the file relative to the storage root
            new_path: New path for the file relative to the storage root
            
        Raises:
            FileNotFoundError: If the source file does not exist
            FileExistsError: If the destination file already exists
        """
        pass
    
    @abstractmethod
    def begin_transaction(self) -> None:
        """Begin a transaction for batching multiple file operations.
        
        This method starts a transaction that allows multiple file operations
        to be batched together and committed atomically. Not all implementations
        may support transactions, in which case this method may be a no-op.
        """
        pass
    
    @abstractmethod
    def commit_transaction(self, message: str = "") -> None:
        """Commit the current transaction.
        
        This method commits all operations performed since the last call to
        begin_transaction. Not all implementations may support transactions,
        in which case this method may be a no-op.
        
        Args:
            message: Optional commit message (for implementations that support it)
        """
        pass
    
    @abstractmethod
    def abort_transaction(self) -> None:
        """Abort the current transaction.
        
        This method discards all operations performed since the last call to
        begin_transaction. Not all implementations may support transactions,
        in which case this method may be a no-op.
        """
        pass
    
    @contextmanager
    def transaction(self, message: str = "") -> Generator[None, None, None]:
        """Context manager for transactions.
        
        This method provides a convenient way to use transactions with a
        context manager. It calls begin_transaction() when entering the
        context and commit_transaction() when exiting normally, or
        abort_transaction() if an exception is raised.
        
        Args:
            message: Optional commit message (for implementations that support it)
            
        Yields:
            None
            
        Example:
            with file_service.transaction("Batch operation"):
                file_service.write_file("file1.txt", "content1")
                file_service.write_file("file2.txt", "content2")
        """
        try:
            self.begin_transaction()
            yield
            self.commit_transaction(message)
        except Exception:
            self.abort_transaction()
            raise

