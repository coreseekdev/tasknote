"""Edit session implementation using Operational Transform.

This module provides the EditSessionOT class that implements the EditSession interface
using operational transformation for handling concurrent edits.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import time
from ..interface import EditSession


@dataclass
class Operation:
    """Represents an editing operation.
    
    An operation is defined by:
    - start: start position of the operation
    - end: end position of the operation
    - text: text to insert
    
    The operation type is determined by:
    - If start == end and text is not empty: INSERT
    - If start < end and text is empty: DELETE
    - If start < end and text is not empty: REPLACE
    """
    
    start: int   # Start position of the operation
    end: int     # End position of the operation
    text: str    # Text to insert
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the operation to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the operation
        """
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Operation":
        """Create an operation from a dictionary.
        
        Args:
            data: Dictionary representation of the operation
            
        Returns:
            Operation: The created operation
        """
        return cls(
            start=data["start"],
            end=data["end"],
            text=data["text"]
        )


class EditSessionOT(EditSession):
    """Operational transform implementation of EditSession."""
    
    def __init__(self, content: str, session_id: Optional[str] = None):
        """Initialize an edit session.
        
        Args:
            content: Initial content of the file
            session_id: Optional session ID. If not provided, a UUID will be generated
        """
        super().__init__(content, session_id)
        self.operations: List[Operation] = []
    
    def _apply_operation(self, operation: Operation) -> None:
        """Apply an operation to the current content.
        
        Args:
            operation: The operation to apply
        """
        # Get content before and after the operation range
        before = self.current_content[:operation.start]
        after = self.current_content[operation.end:]
        
        # Apply the operation
        if operation.text or not after.startswith(" "):
            self.current_content = before + operation.text + after
        else:
            # If we're deleting and the next character is a space, skip it
            self.current_content = before + after[1:]
        
        # Record the operation
        self.operations.append(operation)
        self.last_modified = time.time()
    
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
        if position < 0 or position > len(self.current_content):
            raise ValueError(f"Invalid position: {position}")
        
        operation = Operation(start=position, end=position, text=text)
        self._apply_operation(operation)
        return self.current_content
    
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
        if start < 0 or start >= len(self.current_content):
            raise ValueError(f"Invalid start position: {start}")
        if end <= start or end > len(self.current_content):
            raise ValueError(f"Invalid end position: {end}")
        
        operation = Operation(start=start, end=end, text="")
        self._apply_operation(operation)
        return self.current_content
    
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
        if start < 0 or start >= len(self.current_content):
            raise ValueError(f"Invalid start position: {start}")
        if end <= start or end > len(self.current_content):
            raise ValueError(f"Invalid end position: {end}")
        
        operation = Operation(start=start, end=end, text=text)
        self._apply_operation(operation)
        return self.current_content

    def get_edit_history(self) -> List[Dict[str, Any]]:
        """Get the history of operations.
        
        Returns:
            List[Dict[str, Any]]: List of operations as dictionaries
        """
        return [op.to_dict() for op in self.operations]
    

