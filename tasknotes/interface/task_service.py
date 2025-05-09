"""
Task Service Interface for TaskNotes.

This module defines the interface for managing tasks within projects.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Union


class TaskService(ABC):
    """Interface for managing tasks within a project."""

    @abstractmethod
    def __init__(self, file_path: Union[str, Path], content: Optional[str] = None) -> None:
        """
        Initialize a TaskService instance from a file or content.

        Args:
            file_path: Path to the markdown file representing the project
            content: Optional content to use instead of reading from file_path
        """
        pass

    @abstractmethod
    def add_task(self, task_description: str, tags: Optional[List[str]] = None) -> str:
        """
        Add a new task to the project.

        Args:
            task_description: Description of the task
            tags: Optional list of tags to associate with the task

        Returns:
            Task ID of the newly created task
        """
        pass

    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from the project.

        Args:
            task_id: ID of the task to delete

        Returns:
            True if the task was deleted, False otherwise
        """
        pass

    @abstractmethod
    def modify_task(self, task_id: str, new_description: str) -> bool:
        """
        Modify the description of a task.

        Args:
            task_id: ID of the task to modify
            new_description: New description for the task

        Returns:
            True if the task was modified, False otherwise
        """
        pass

    @abstractmethod
    def mark_as_completed(self, task_id: str, completed: bool = True) -> bool:
        """
        Mark a task as completed or not completed.

        Args:
            task_id: ID of the task to mark
            completed: True to mark as completed, False to mark as not completed

        Returns:
            True if the task status was updated, False otherwise
        """
        pass

    @abstractmethod
    def add_tag_to_task(self, task_id: str, tag: str) -> bool:
        """
        Add a tag to a task.

        Args:
            task_id: ID of the task to tag
            tag: Tag to add to the task

        Returns:
            True if the tag was added, False otherwise
        """
        pass

    @abstractmethod
    def remove_tag_from_task(self, task_id: str, tag: str) -> bool:
        """
        Remove a tag from a task.

        Args:
            task_id: ID of the task
            tag: Tag to remove from the task

        Returns:
            True if the tag was removed, False otherwise
        """
        pass

    @abstractmethod
    def replace_task_tags(self, task_id: str, tags: List[str]) -> bool:
        """
        Replace all tags associated with a task.

        Args:
            task_id: ID of the task
            tags: New list of tags to associate with the task

        Returns:
            True if the tags were replaced, False otherwise
        """
        pass

    @abstractmethod
    def list_tasks_by_tag(self, tag: str) -> List[Dict[str, Union[str, List[str], bool]]]:
        """
        List all tasks associated with a specific tag.

        Args:
            tag: Tag to filter tasks by

        Returns:
            List of task dictionaries containing id, description, tags, and completion status
        """
        pass

    @abstractmethod
    def list_tasks_by_tags(self, tags: List[str]) -> List[Dict[str, Union[str, List[str], bool]]]:
        """
        List all tasks associated with any of the specified tags (OR relationship).

        Args:
            tags: List of tags to filter tasks by

        Returns:
            List of task dictionaries containing id, description, tags, and completion status
        """
        pass

    @abstractmethod
    def create_tag_collection(self, collection_name: str, tags: List[str]) -> bool:
        """
        Create a named collection of tags that can be referenced together.

        Args:
            collection_name: Name for the tag collection
            tags: List of tags to include in the collection

        Returns:
            True if the collection was created, False otherwise
        """
        pass

    @abstractmethod
    def list_tasks_by_tag_collection(self, collection_name: str) -> List[Dict[str, Union[str, List[str], bool]]]:
        """
        List all tasks associated with any tag in the specified collection.

        Args:
            collection_name: Name of the tag collection to use for filtering

        Returns:
            List of task dictionaries containing id, description, tags, and completion status
        """
        pass

    @abstractmethod
    def get_all_tasks(self) -> List[Dict[str, Union[str, List[str], bool]]]:
        """
        Get all tasks in the project.

        Returns:
            List of task dictionaries containing id, description, tags, and completion status
        """
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Dict[str, Union[str, List[str], bool]]]:
        """
        Get a specific task by ID.

        Args:
            task_id: ID of the task to retrieve

        Returns:
            Task dictionary containing id, description, tags, and completion status,
            or None if the task does not exist
        """
        pass

    @abstractmethod
    def flush(self) -> bool:
        """
        Save the current state of the project to its file.

        Returns:
            True if the project was saved successfully, False otherwise
        """
        pass
