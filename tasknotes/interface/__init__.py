"""
Interface module for TaskNotes.

This package contains service interfaces for the TaskNotes application.
"""

from typing import List
from .edit_session import EditSession
from .file_service import FileService
from .project_service import ProjectService

__all__: List[str] = [
    'EditSession',
    'FileService',
    'ProjectService',
    'edit_session',
    'file_service',
    'project_service',
    'task_service',
]
