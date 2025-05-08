"""Edit service for TaskNotes.

This module provides the EditService for editing markdown files with operational transform support.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union, Set
from pathlib import Path
import json
import time
import uuid
from dataclasses import dataclass, field

from .file_service import FileService
# from .markdown import MarkdownParser


@dataclass
class Operation:
    """Represents an operational transform operation."""
    
    # Operation types
    RETAIN = "retain"  # Keep text unchanged
    INSERT = "insert"  # Insert text
    DELETE = "delete"  # Delete text
    
    type: str
    value: Union[str, int]  # Text for insert, length for retain/delete
    
    def apply(self, text: str) -> str:
        """Apply the operation to the text.
        
        Args:
            text: The text to apply the operation to
            
        Returns:
            str: The text after applying the operation
        """
        if self.type == self.RETAIN:
            # Keep the specified number of characters
            length = int(self.value)
            if length > len(text):
                length = len(text)
            return text[:length]
        elif self.type == self.INSERT:
            # Insert text at the beginning
            return str(self.value) + text
        elif self.type == self.DELETE:
            # Delete the specified number of characters
            length = int(self.value)
            if length > len(text):
                length = len(text)
            return text[length:]
        else:
            raise ValueError(f"Unknown operation type: {self.type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the operation to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the operation
        """
        return {
            "type": self.type,
            "value": self.value
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
            type=data["type"],
            value=data["value"]
        )


class EditSession:
    """Represents an editing session for a file with operational transform support."""
    
    def __init__(self, file_service: FileService, file_path: str, content: str, metadata: Dict[str, Any]):
        """Initialize an edit session.
        
        Args:
            file_service: The file service to use for saving
            file_path: Path to the file being edited
            content: Initial content of the file
            metadata: Metadata extracted from the file
        """
        self.file_service = file_service
        self.file_path = file_path
        self.original_content = content
        self.current_content = content
        self.metadata = metadata
        self.operations: List[Operation] = []
        self.session_id = str(uuid.uuid4())
        self.created_at = time.time()
        self.last_modified = self.created_at
        self.is_closed = False
    
    def apply_operation(self, operation: Operation) -> str:
        """Apply an operation to the current content.
        
        Args:
            operation: The operation to apply
            
        Returns:
            str: The content after applying the operation
            
        Raises:
            ValueError: If the session is closed
        """
        if self.is_closed:
            raise ValueError("Cannot apply operations to a closed session")
        
        self.current_content = operation.apply(self.current_content)
        self.operations.append(operation)
        self.last_modified = time.time()
        return self.current_content
    
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
        
        # Create operations for the insertion
        operations = []
        if position > 0:
            operations.append(Operation(Operation.RETAIN, position))
        operations.append(Operation(Operation.INSERT, text))
        if position < len(self.current_content):
            operations.append(Operation(Operation.RETAIN, len(self.current_content) - position))
        
        # Apply the operations
        result = self.current_content
        for op in operations:
            result = self.apply_operation(op)
        
        return result
    
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
        
        # Create operations for the deletion
        operations = []
        if start > 0:
            operations.append(Operation(Operation.RETAIN, start))
        operations.append(Operation(Operation.DELETE, end - start))
        if end < len(self.current_content):
            operations.append(Operation(Operation.RETAIN, len(self.current_content) - end))
        
        # Apply the operations
        result = self.current_content
        for op in operations:
            result = self.apply_operation(op)
        
        return result
    
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
        
        # Delete then insert
        self.delete(start, end)
        return self.insert(start, text)
    
    def flush(self) -> None:
        """Flush changes to the file without closing the session."""
        if self.is_closed:
            raise ValueError("Cannot flush a closed session")
        
        # Generate markdown with updated content
        updated_markdown = MarkdownParser.generate_markdown(
            title=self.metadata.get("title", "Untitled"),
            content=self.current_content,
            metadata=self.metadata
        )
        
        # Save to file
        self.file_service.write_file(self.file_path, updated_markdown)
    
    def close(self) -> None:
        """Close the session and save changes."""
        if self.is_closed:
            return
        
        self.flush()
        self.is_closed = True
    
    def get_operations_history(self) -> List[Dict[str, Any]]:
        """Get the history of operations.
        
        Returns:
            List[Dict[str, Any]]: List of operations as dictionaries
        """
        return [op.to_dict() for op in self.operations]
    
    def get_diff(self) -> Dict[str, Any]:
        """Get the difference between original and current content.
        
        Returns:
            Dict[str, Any]: Difference information
        """
        return {
            "original_length": len(self.original_content),
            "current_length": len(self.current_content),
            "operations_count": len(self.operations),
            "session_duration": time.time() - self.created_at
        }
        
    def get_content(self) -> str:
        """Get the current content of the file.
        
        Returns:
            str: The current content
        """
        return self.current_content
        
    def get_metadata(self) -> Dict[str, Any]:
        """Get the metadata of the file.
        
        Returns:
            Dict[str, Any]: The metadata
        """
        return self.metadata


class EditService:
    """Service for editing files with operational transform support."""
    
    def __init__(self, file_service: FileService):
        """Initialize the edit service.
        
        Args:
            file_service: The file service to use for file operations
        """
        self.file_service = file_service
        self.active_sessions: Dict[str, EditSession] = {}
    
    def edit_text_file(self, file_path: str) -> EditSession:
        """Open a file for editing.
        
        Args:
            file_path: Path to the file to edit
            
        Returns:
            EditSession: The edit session for the file
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        # Check if file exists
        if not self.file_service.file_exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file content
        content = self.file_service.read_file(file_path)
        
        # Parse markdown
        parsed = MarkdownParser.parse_markdown(content)
        
        # Create edit session
        session = EditSession(
            file_service=self.file_service,
            file_path=file_path,
            content=parsed["content"],
            metadata=parsed["metadata"]
        )
        
        # Store session
        self.active_sessions[session.session_id] = session
        
        return session
    
    def get_session(self, session_id: str) -> Optional[EditSession]:
        """Get an active edit session by ID.
        
        Args:
            session_id: ID of the session to get
            
        Returns:
            Optional[EditSession]: The edit session or None if not found
        """
        return self.active_sessions.get(session_id)
    
    def close_session(self, session_id: str) -> bool:
        """Close an edit session.
        
        Args:
            session_id: ID of the session to close
            
        Returns:
            bool: True if the session was closed, False if not found
        """
        session = self.active_sessions.get(session_id)
        if session:
            session.close()
            del self.active_sessions[session_id]
            return True
        return False
    
    def create_markdown_file(self, file_path: str, title: str, content: str = "", metadata: Optional[Dict[str, Any]] = None) -> EditSession:
        """Create a new markdown file and open it for editing.
        
        Args:
            file_path: Path to create the file at
            title: Title of the markdown document
            content: Initial content
            metadata: Additional metadata
            
        Returns:
            EditSession: The edit session for the new file
            
        Raises:
            FileExistsError: If the file already exists
        """
        # Check if file exists
        if self.file_service.file_exists(file_path):
            raise FileExistsError(f"File already exists: {file_path}")
        
        # Generate markdown content
        markdown_content = MarkdownParser.generate_markdown(
            title=title,
            content=content,
            metadata=metadata
        )
        
        # Write file
        self.file_service.write_file(file_path, markdown_content)
        
        # Parse to get the actual content and metadata
        parsed = MarkdownParser.parse_markdown(markdown_content)
        
        # Create edit session
        session = EditSession(
            file_service=self.file_service,
            file_path=file_path,
            content=parsed["content"],
            metadata=parsed["metadata"]
        )
        
        # Store session
        self.active_sessions[session.session_id] = session
        
        return session
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get information about all active edit sessions.
        
        Returns:
            List[Dict[str, Any]]: Information about active sessions
        """
        return [
            {
                "session_id": session.session_id,
                "file_path": session.file_path,
                "created_at": session.created_at,
                "last_modified": session.last_modified,
                "operations_count": len(session.operations)
            }
            for session in self.active_sessions.values()
        ]
