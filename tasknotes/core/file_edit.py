from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union, Set
from pathlib import Path
import json
import time
import uuid
from dataclasses import dataclass, field

from .file_service import FileService


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
