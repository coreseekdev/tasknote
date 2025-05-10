"""
Interface module for TaskNotes.

This package contains service interfaces for the TaskNotes application.
"""

from typing import List
from .edit_session import EditSession, EditOperation
from .file_service import FileService
from .project_service import ProjectService
from .task_service import TaskService
from .markdown_service import MarkdownService

__all__: List[str] = [
    'EditSession',
    'EditOperation',
    'FileService',
    'ProjectService',
    'TaskService',
    'MarkdownService',
    'markdown_service',
]
