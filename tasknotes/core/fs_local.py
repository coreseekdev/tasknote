from pathlib import Path
from typing import List, Optional, Dict, Any, BinaryIO, Set, Iterator

from .file_service import FileService
from .task_env import TaskNoteEnv

class LocalFilesystem(FileService):
    """Implementation of FileService for local filesystem storage.
    
    This implementation stores files in the .tasknote directory
    in the repository root or in a specified directory.
    """
    
    def __init__(self, base_path: Path):
        """Initialize the LocalFilesystem service.
        
        Args:
            base_path: Base path for the storage (usually .tasknote directory)
        """
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)
    
    def _get_full_path(self, path: str) -> Path:
        """Get the full path for a file.
        
        Args:
            path: Path relative to the storage root
            
        Returns:
            Path: Full path to the file
        """
        return self.base_path / path
    
    def read_file(self, path: str) -> str:
        """Read a file from the storage.
        
        Args:
            path: Path to the file relative to the storage root
            
        Returns:
            str: Content of the file
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        full_path = self._get_full_path(path)
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def write_file(self, path: str, content: str) -> None:
        """Write content to a file in the storage.
        
        Args:
            path: Path to the file relative to the storage root
            content: Content to write to the file
            
        Raises:
            IOError: If the file cannot be written
        """
        full_path = self._get_full_path(path)
        os.makedirs(full_path.parent, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    def delete_file(self, path: str) -> None:
        """Delete a file from the storage.
        
        Args:
            path: Path to the file relative to the storage root
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        full_path = self._get_full_path(path)
        if full_path.exists():
            os.remove(full_path)
        else:
            raise FileNotFoundError(f"File not found: {path}")
    
    def list_files(self, directory: str = "", pattern: str = "*") -> List[str]:
        """List files in a directory.
        
        Args:
            directory: Directory to list files from, relative to the storage root
            pattern: Pattern to match files against (glob format)
            
        Returns:
            List[str]: List of file paths relative to the storage root
        """
        full_path = self._get_full_path(directory)
        if not full_path.exists() or not full_path.is_dir():
            return []
        
        files = []
        for item in full_path.glob(pattern):
            if item.is_file():
                rel_path = item.relative_to(self.base_path)
                files.append(str(rel_path))
        
        return files
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists in the storage.
        
        Args:
            path: Path to the file relative to the storage root
            
        Returns:
            bool: True if the file exists, False otherwise
        """
        full_path = self._get_full_path(path)
        return full_path.exists() and full_path.is_file()
    
    def create_directory(self, path: str) -> None:
        """Create a directory in the storage.
        
        Args:
            path: Path to the directory relative to the storage root
            
        Raises:
            IOError: If the directory cannot be created
        """
        full_path = self._get_full_path(path)
        os.makedirs(full_path, exist_ok=True)
    
    def get_modified_time(self, path: str) -> float:
        """Get the last modified time of a file.
        
        Args:
            path: Path to the file relative to the storage root
            
        Returns:
            float: Last modified time as a timestamp
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        full_path = self._get_full_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        return full_path.stat().st_mtime

