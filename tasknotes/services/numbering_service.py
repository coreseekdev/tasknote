"""Task numbering service implementation for TaskNotes.

This module provides a service for automatically generating sequential
task and project identifiers with customizable prefixes.
"""

import yaml
from typing import Dict, Optional

from tasknotes.interface.file_service import FileService


class TaskNumberingService:
    """Service for generating sequential task and project identifiers.
    
    This service maintains a YAML file that stores the current sequence numbers
    for each prefix (e.g., TASK-001, PROJ-002). It ensures that numbers are
    always incremented and never reused.
    """
    
    DEFAULT_PREFIX = "TASK"
    PREFIX_FILE = "prefixes.yaml"
    
    def __init__(self, file_service: FileService):
        """Initialize the TaskNumberingService.
        
        Args:
            file_service: The file service to use for storage
        """
        self.file_service = file_service
        self._prefixes = self._load_prefixes()
    
    def _load_prefixes(self) -> Dict[str, int]:
        """Load prefixes and their current sequence numbers from the YAML file.
        
        Returns:
            Dict[str, int]: Dictionary mapping prefixes to their current sequence numbers
        """
        try:
            content = self.file_service.read_file(self.PREFIX_FILE)
            data = yaml.safe_load(content)
            
            if not data:
                return self._initialize_prefixes()
                
            # Ensure the default prefix exists
            if "default" not in data:
                data["default"] = self.DEFAULT_PREFIX
                
            # Ensure the default prefix has a sequence number
            if data["default"] not in data:
                data[data["default"]] = 0
                
            return data
        except FileNotFoundError:
            return self._initialize_prefixes()
        except yaml.YAMLError:
            # If the file is corrupted, initialize with defaults
            return self._initialize_prefixes()
    
    def _initialize_prefixes(self) -> Dict[str, int]:
        """Initialize the prefixes dictionary with default values.
        
        Returns:
            Dict[str, int]: Dictionary with default prefix configuration
        """
        prefixes = {
            "default": self.DEFAULT_PREFIX,
            self.DEFAULT_PREFIX: 0
        }
        
        # Save the initial configuration
        self._save_prefixes(prefixes)
        
        return prefixes
    
    def _save_prefixes(self, prefixes: Dict[str, int]) -> None:
        """Save the prefixes dictionary to the YAML file.
        
        Args:
            prefixes: Dictionary mapping prefixes to their current sequence numbers
        """
        content = yaml.dump(prefixes, default_flow_style=False)
        
        try:
            self.file_service.write_file(self.PREFIX_FILE, content)
        except Exception as e:
            # Log the error but don't crash
            print(f"Error saving prefixes: {e}")
    
    def get_next_number(self, prefix: Optional[str] = None) -> str:
        """Get the next sequential identifier for the given prefix.
        
        Args:
            prefix: The prefix to use (e.g., "TASK", "PROJ"). If None, the default prefix is used.
            
        Returns:
            str: The next identifier in the sequence (e.g., "TASK-001")
        """
        # Use the default prefix if none is provided
        if prefix is None:
            prefix = self._prefixes["default"]
        
        # Initialize the prefix if it doesn't exist
        if prefix not in self._prefixes:
            self._prefixes[prefix] = 0
        
        # Increment the sequence number
        self._prefixes[prefix] += 1
        
        # Format the identifier (e.g., "TASK-001")
        identifier = f"{prefix}-{self._prefixes[prefix]:03d}"
        
        # Save the updated prefixes
        self._save_prefixes(self._prefixes)
        
        return identifier
    
    def set_default_prefix(self, prefix: str) -> None:
        """Set the default prefix to use when no prefix is specified.
        
        Args:
            prefix: The prefix to set as default
        """
        # Initialize the prefix if it doesn't exist
        if prefix not in self._prefixes:
            self._prefixes[prefix] = 0
        
        # Set the default prefix
        self._prefixes["default"] = prefix
        
        # Save the updated prefixes
        self._save_prefixes(self._prefixes)
    
    def get_default_prefix(self) -> str:
        """Get the current default prefix.
        
        Returns:
            str: The current default prefix
        """
        return self._prefixes["default"]
    
    def get_current_number(self, prefix: Optional[str] = None) -> int:
        """Get the current sequence number for the given prefix.
        
        Args:
            prefix: The prefix to check. If None, the default prefix is used.
            
        Returns:
            int: The current sequence number
        """
        # Use the default prefix if none is provided
        if prefix is None:
            prefix = self._prefixes["default"]
        
        # Return 0 if the prefix doesn't exist
        return self._prefixes.get(prefix, 0)
    
    def get_all_prefixes(self) -> Dict[str, int]:
        """Get all prefixes and their current sequence numbers.
        
        Returns:
            Dict[str, int]: Dictionary mapping prefixes to their current sequence numbers
        """
        # Return a copy of the prefixes dictionary, excluding the "default" key
        return {k: v for k, v in self._prefixes.items() if k != "default"}
    
    def reset_prefix(self, prefix: str, value: int = 0) -> None:
        """Reset the sequence number for a prefix.
        
        Args:
            prefix: The prefix to reset
            value: The value to reset to (default: 0)
        """
        if prefix in self._prefixes:
            self._prefixes[prefix] = value
            self._save_prefixes(self._prefixes)
