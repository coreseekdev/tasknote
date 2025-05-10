"""Edit session interface for TaskNotes.

This module provides the abstract interface for edit sessions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import uuid
import time


class EditSession(ABC):
    """Abstract base class for edit sessions.
    
    An edit session represents a sequence of editing operations on a piece of content.
    Different implementations may use different strategies to handle concurrent edits,
    such as operational transformation (OT) or conflict-free replicated data types (CRDT).
    """
    
    def __init__(self, content: str, session_id: Optional[str] = None):
        """Initialize an edit session.
        
        Args:
            content: Initial content
            session_id: Optional session ID. If not provided, a UUID will be generated
        """
        self.original_content = content
        self.current_content = content
        self._session_id = session_id if session_id is not None else str(uuid.uuid4())
        self.created_at = time.time()
        self.last_modified = self.created_at
    
    @property
    def session_id(self):
        return self._session_id

    @abstractmethod
    def insert(self, position: int, text: str) -> str:
        """Insert text at the specified position.
        
        Args:
            position: Position to insert at
            text: Text to insert
            
        Returns:
            str: The content after inserting
            
        Raises:
            ValueError: If the position is invalid
        """
        pass
    
    @abstractmethod
    def delete(self, start: int, end: int) -> str:
        """Delete text between start and end positions.
        
        Args:
            start: Start position
            end: End position
            
        Returns:
            str: The content after deleting
            
        Raises:
            ValueError: If the positions are invalid
        """
        pass
    
    @abstractmethod
    def replace(self, start: int, end: int, text: str) -> str:
        """Replace text between start and end positions.
        
        Args:
            start: Start position
            end: End position
            text: Replacement text
            
        Returns:
            str: The content after replacing
            
        Raises:
            ValueError: If the positions are invalid
        """
        pass
    
    @abstractmethod
    def get_edit_history(self) -> List[Dict[str, Any]]:
        """Get the history of operations.
        
        Returns:
            List[Dict[str, Any]]: List of operations as dictionaries
        """
        pass
    
    def get_content(self) -> str:
        """Get the current content.
        
        Returns:
            str: The current content
        """
        return self.current_content
