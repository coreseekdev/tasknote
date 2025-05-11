"""Numbering service interface for TaskNotes.

This module defines the interface for generating sequential task and project identifiers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional


class NumberingService(ABC):
    """Interface for generating sequential task and project identifiers.
    
    This abstract class defines the interface for numbering services
    that can generate sequential identifiers with customizable prefixes.
    """
    
    @abstractmethod
    def get_next_number(self, prefix: Optional[str] = None) -> str:
        """Get the next sequential identifier for the given prefix.
        
        Args:
            prefix: The prefix to use (e.g., "TASK", "PROJ"). If None, the default prefix is used.
            
        Returns:
            str: The next identifier in the sequence (e.g., "TASK-001")
        """
        pass
    
    @abstractmethod
    def set_default_prefix(self, prefix: str) -> None:
        """Set the default prefix to use when no prefix is specified.
        
        Args:
            prefix: The prefix to set as default
        """
        pass
    
    @abstractmethod
    def get_default_prefix(self) -> str:
        """Get the current default prefix.
        
        Returns:
            str: The current default prefix
        """
        pass
    
    @abstractmethod
    def get_current_number(self, prefix: Optional[str] = None) -> int:
        """Get the current sequence number for the given prefix.
        
        Args:
            prefix: The prefix to check. If None, the default prefix is used.
            
        Returns:
            int: The current sequence number
        """
        pass
    
    @abstractmethod
    def get_all_prefixes(self) -> Dict[str, int]:
        """Get all prefixes and their current sequence numbers.
        
        Returns:
            Dict[str, int]: Dictionary mapping prefixes to their current sequence numbers
        """
        pass
    
    @abstractmethod
    def reset_prefix(self, prefix: str, value: int = 0) -> None:
        """Reset the sequence number for a prefix.
        
        Args:
            prefix: The prefix to reset
            value: The value to reset to (default: 0)
        """
        pass
