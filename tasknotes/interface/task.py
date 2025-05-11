"""
Task Service Interface for TaskNotes.

This module defines the interface for managing tasks within projects.
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

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
    def new_task(self, task_msg: str, task_prefix: Optional[str] = None) -> InlineTask:
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