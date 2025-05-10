"""Project service interface for TaskNotes.

This module defines the interface for managing projects in TaskNotes.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Set

from .task_service import TaskService


class ProjectService(ABC):
    """Interface for managing projects."""

    @abstractmethod
    def create_project(self, name: str, description: Optional[str] = None) -> str:
        """Create a new project.
        
        Args:
            name: Name of the project
            description: Optional description of the project
            
        Returns:
            str: ID of the created project
            
        Raises:
            ValueError: If a project with the same name already exists
        """
        pass

    @abstractmethod
    def archive_project(self, project_id: str) -> bool:
        """Archive a project.
        
        Args:
            project_id: ID of the project to archive
            
        Returns:
            bool: True if the project was archived, False if not found
        """
        pass

    @abstractmethod
    def delete_archived_project(self, project_id: Optional[str] = None) -> int:
        """Delete archived projects.
        
        Args:
            project_id: Optional ID of a specific archived project to delete.
                      If None, all archived projects will be deleted.
            
        Returns:
            int: Number of projects deleted
        """
        pass

    @abstractmethod
    def list_projects(self, include_archived: bool = False) -> List[dict]:
        """List all projects.
        
        Args:
            include_archived: If True, include archived projects in the list
            
        Returns:
            List[dict]: List of project information dictionaries containing:
                - id: Project ID
                - name: Project name
                - description: Project description
                - created_at: Creation timestamp
                - archived_at: Archive timestamp (None if not archived)
                - tags: List of associated tags
        """
        pass

    @abstractmethod
    def get_task_service(self, project_id: str) -> TaskService:
        """Get a TaskService instance for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            TaskService: Task service for the project
            
        Raises:
            ValueError: If the project doesn't exist or is archived
        """
        pass

    @abstractmethod
    def add_tag(self, project_id: str, tag: str) -> bool:
        """Add a tag to a project.
        
        Args:
            project_id: ID of the project
            tag: Tag to add
            
        Returns:
            bool: True if the tag was added, False if the project doesn't exist
                 or is archived
        """
        pass

    @abstractmethod
    def remove_tag(self, project_id: str, tag: str) -> bool:
        """Remove a tag from a project.
        
        Args:
            project_id: ID of the project
            tag: Tag to remove
            
        Returns:
            bool: True if the tag was removed, False if the project doesn't exist,
                 is archived, or didn't have the tag
        """
        pass

    @abstractmethod
    def reset_tags(self, project_id: str) -> bool:
        """Reset (remove all) tags from a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            bool: True if the tags were reset, False if the project doesn't exist
                 or is archived
        """
        pass

    @abstractmethod
    def get_tags(self, project_id: str) -> Set[str]:
        """Get all tags associated with a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Set[str]: Set of tags. Empty set if the project doesn't exist or is archived.
        """
        pass
