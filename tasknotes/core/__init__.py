"""Core functionality package for TaskNotes."""

# from .task_manager import TaskManager
# from .config import Config
# from .models import Task
from .task_env import TaskNoteEnv, setup_git_alias, find_file_service
# from .file_service import FileService
from .fs_local import LocalFilesystem
from .fs_git import GitRepoTree
# from .edit_service import EditService, EditSession, Operation
# from .markdown import MarkdownParser

__all__ = [
    # "TaskManager",  
    "TaskNoteEnv", 
    "setup_git_alias",
    # "LocalFilesystem", 
    # "GitRepoTree", 
    # "create_file_service",
    "MarkdownParser"
]
