"""Edit service for TaskNotes.

This module provides the EditService class for managing file editing sessions.
"""

from typing import Dict, Optional
from pathlib import Path

from .edit_session_ot import EditSessionOT
from ..interface import EditSession, FileService


def new_edit_service(filename: str, context: str, session_id: Optional[str] = None) -> EditSession:
    """create an edit service for the given file.
    
    Args:
        filename: Name of the file to edit (currently unused)
        context: Initial content for the edit session
        session_id: Optional session ID for the edit session
        
    Returns:
        EditSession: An edit session instance
    """
    return EditSessionOT(context, session_id)


class EditService:
    """Service for managing file editing sessions.
    
    This service is responsible for:
    1. Creating and managing edit sessions
    2. Persisting changes to the file system
    3. Coordinating concurrent edits
    """
    
    def __init__(self, file_service: FileService):
        """Initialize the edit service.
        
        Args:
            file_service: File service for persisting changes
        """
        self.file_service = file_service
        self._sessions: Dict[str, EditSession] = {}
    
    def create_session(self, filename: str, session_id: Optional[str] = None) -> EditSession:
        """Create a new edit session for a file.
        
        Args:
            filename: Name of the file to edit
            session_id: Optional session ID for the edit session
            
        Returns:
            EditSession: The created edit session
            
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        path = Path(filename)
        if not self.file_service.exists(path):
            raise FileNotFoundError(f"File not found: {filename}")
            
        content = self.file_service.read_file(path)
        session = new_edit_service(filename, content, session_id)
        self._sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[EditSession]:
        """Get an existing edit session by its ID.
        
        Args:
            session_id: ID of the session to get
            
        Returns:
            Optional[EditSession]: The edit session if found, None otherwise
        """
        return self._sessions.get(session_id)
    
    def save_session(self, session_id: str, filename: str) -> None:
        """Save the current content of an edit session to a file.
        
        Args:
            session_id: ID of the session to save
            filename: Name of the file to save to
            
        Raises:
            KeyError: If the session doesn't exist
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session not found: {session_id}")
            
        path = Path(filename)
        self.file_service.write_file(path, session.get_content())
    
    def close_session(self, session_id: str) -> None:
        """Close an edit session.
        
        Args:
            session_id: ID of the session to close
            
        Raises:
            KeyError: If the session doesn't exist
        """
        if session_id not in self._sessions:
            raise KeyError(f"Session not found: {session_id}")
            
        del self._sessions[session_id]
