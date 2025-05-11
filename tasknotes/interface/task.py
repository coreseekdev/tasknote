"""
Task and Project Interface for TaskNotes.

This module defines the interfaces for managing tasks and projects in TaskNotes.
It provides a unified model where projects are special cases of tasks.
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Set

from tasknotes.interface.file_service import FileService
from tasknotes.interface.numbering_service import NumberingService

class Task(ABC):
    """
    Abstract base class for all types of tasks.
    
    This class defines the common interface that all task implementations must provide.
    """
    
    @property
    @abstractmethod
    def task_id(self) -> str:
        """Get the task ID."""
        pass

    @property
    @abstractmethod
    def task_message(self) -> str:
        """Get the task single line message."""
        pass
    
    @abstractmethod
    def mark_as_done(self) -> bool:
        """
        Mark the task as done.
        
        Returns:
            bool: True if the operation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def mark_as_undone(self) -> bool:
        """
        Mark the task as not done.
        
        Returns:
            bool: True if the operation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, force: bool = False) -> bool:
        """
        Delete the task.
        
        Args:
            force: If True, force deletion even if there are dependencies
            
        Returns:
            bool: True if the operation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def modify_task(self, task_msg: str) -> bool:
        """
        Update the task description or title.
        
        Args:
            task_msg: New description or title for the task
            
        Returns:
            bool: True if the operation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def tags(self, new_tags: Optional[List[str]] = None) -> List[str]:
        """
        Get or replace the list of tags associated with this task.
        
        Args:
            new_tags: Optional new list of tags to associate with the task.
                      If provided, replaces the existing tags.
            
        Returns:
            List[str]: Current list of tags (after any updates)
        """
        pass


class InlineTask(Task):
    """
    Implementation of a task that is represented as a single line in a markdown file.
    
    These tasks are typically part of a FileTask and don't have their own file.
    """
    
    @abstractmethod
    def convert_task(self) -> 'FileTask':
        """
        Convert this inline task to a file task.
        
        Returns:
            FileTask: The newly created file task
        """
        pass


class FileTask(Task):
    """
    Implementation of a task that is represented as a markdown file.
    
    These tasks can contain inline tasks and other file tasks as subtasks.
    """
    
    @abstractmethod
    def __init__(self, file_service: FileService, numbering_service: NumberingService, task_id: str, context: str) -> None:
        """
        Initialize a FileTask instance.
        
        Args:
            file_service: The file service to use for storage operations
            numbering_service: The numbering service to use for generating task IDs
            task_id: The ID of the task
            context: The markdown content of the task
        """
        pass
    
    @abstractmethod
    def new_sub_task(self, task_msg: str, task_prefix: Optional[str] = None) -> Optional[InlineTask]:
        """
        Create a new inline task as a subtask of this file task.
        
        Args:
            task_msg: Description of the task
            task_prefix: Optional prefix for the task ID
            
        Returns:
            InlineTask: The newly created inline task
        """
        pass
    
    @abstractmethod
    def tasks(self) -> List[Task]:
        """
        Get all subtasks of this file task.
        
        Returns:
            List[Task]: List of subtasks (can be InlineTask or FileTask)
        """
        pass
    
    @abstractmethod
    def delete(self, task_id: Optional[str] = None, force: bool = False) -> bool:
        """
        Delete this task or a subtask.
        
        Args:
            task_id: ID of the subtask to delete, or None to delete this task
            force: If True, force deletion even if there are dependencies
            
        Returns:
            bool: True if the operation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def mark_as_archived(self, force: bool = False) -> bool:
        """
        Mark this task as archived.
        
        Args:
            force: If True, force archiving even if there are active subtasks
            
        Returns:
            bool: True if the operation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def add_related_task(self, task_id: str) -> 'FileTask':
        """
        Add an existing task as a related task to this task.
        
        Args:
            task_id: ID of the task to add as related
            
        Returns:
            FileTask: The related file task
        """
        pass
    
    @abstractmethod
    def convert_task(self, task_id: str) -> 'FileTask':
        """
        Convert a subtask to a file task.
        
        Args:
            task_id: ID of the subtask to convert
            
        Returns:
            FileTask: The newly created file task
        """
        pass
    
    @abstractmethod
    def modify_task(self, task_id: Optional[str] = None, task_msg: Optional[str] = None) -> bool:
        """
        Update this task or a subtask.
        
        Args:
            task_id: ID of the subtask to update, or None to update this task
            task_msg: New description or title
            
        Returns:
            bool: True if the operation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def tag_groups(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the tag groups defined in this task.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of tag groups, where each value is a dictionary
                with 'ordered' (bool) and 'items' (List[str]) keys
        """
        pass


class TaskService(FileTask):
    """
    Task service interface that manages a collection of tasks.
    
    TaskService is a special case of FileTask that serves as the root task
    for a project. It provides additional methods for project management.
    """
    
    @abstractmethod
    def __init__(self, file_service: FileService, numbering_service: NumberingService) -> None:
        """
        Initialize a TaskService instance.
        
        Args:
            file_service: The file service to use for storage operations
            numbering_service: The numbering service to use for generating task IDs
        """
        pass

    @abstractmethod
    def new_task(self, task_msg: str, task_prefix: Optional[str] = None) -> Task:
        """
        Create a new task as a subtask of this file task.
        
        Args:
            task_msg: Description of the task
            task_prefix: Optional prefix for the task ID
            
        Returns:
            Task: The newly created task
        """
        # 对于 TaskService，返回的是 FileTask 
        pass
    
    @abstractmethod
    def list_tasks(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        List all tasks managed by this service.
        
        Args:
            include_archived: If True, include archived tasks in the list
            
        Returns:
            List[Dict[str, Any]]: List of task information dictionaries containing:
                - id: Task ID
                - name: Task name
                - description: Task description
                - created_at: Creation timestamp
                - archived_at: Archive timestamp (None if not archived)
                - tags: List of associated tags
        """
        pass
    
    @abstractmethod
    def get_task(self, task_id: str) -> Optional[FileTask]:
        """
        Get a specific task by ID.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            Optional[FileTask]: The task, or None if not found
            
        Raises:
            ValueError: If the task is archived
        """
        pass
    
    @abstractmethod
    def archive_task(self, task_id: str) -> bool:
        """
        Archive a task.
        
        Args:
            task_id: ID of the task to archive
            
        Returns:
            bool: True if the task was archived, False if not found
        """
        pass
    
    @abstractmethod
    def delete_archived_task(self, task_id: Optional[str] = None) -> int:
        """
        Delete archived tasks.
        
        Args:
            task_id: Optional ID of a specific archived task to delete.
                   If None, all archived tasks will be deleted.
            
        Returns:
            int: Number of tasks deleted
        """
        pass


# Alias for backward compatibility and clarity
ProjectService = TaskService