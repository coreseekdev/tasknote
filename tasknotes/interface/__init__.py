"""
Interface module for TaskNotes.

This package contains service interfaces for the TaskNotes application.
"""

from typing import List
from .edit_session import EditSession, EditOperation
from .file_service import FileService
from .numbering_service import NumberingService
from .project_service import ProjectService
from .task import FileTask, InlineTask
from .markdown_service import MarkdownService

__all__: List[str] = [
    'EditSession',
    'EditOperation',
    'FileService',
    'NumberingService',
    'ProjectService',
    'FileTask',
    'InlineTask',
    'MarkdownService',
    'markdown_service',
]
