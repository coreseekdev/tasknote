"""Services package for TaskNotes.

This package contains concrete implementations of the service interfaces.
"""
from .numbering_service import TaskNumberingService as NumberingService
from .file_task_service import FileTaskService as TaskService

# 为了向后兼容性，提供ProjectService别名
ProjectService = TaskService

__all__ = [
    "TaskService",
    "ProjectService",
    "NumberingService"
]