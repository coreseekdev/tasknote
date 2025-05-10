"""File-based project service implementation for TaskNotes.

This module provides a concrete implementation of the ProjectService interface
that stores projects as files using the FileService.
"""

import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from tasknotes.interface import FileService, ProjectService, TaskService
from .markdown_task_service import MarkdownTaskService


class FileProjectService(ProjectService):
    """Implementation of ProjectService that uses FileService for storage.
    
    Projects are stored in two directories:
    - 'projects': Active projects
    - 'archived': Archived projects
    
    Each project is stored as a JSON metadata file and has an associated
    markdown file for tasks.
    """
    
    def __init__(self, file_service: FileService):
        """Initialize a FileProjectService instance.
        
        Args:
            file_service: The file service to use for storage
        """
        self.file_service = file_service
        self.projects_dir = "projects"
        self.archived_dir = "archived"
        
        # Ensure the project directories exist
        if not self.file_service.file_exists(self.projects_dir):
            self.file_service.create_directory(self.projects_dir)
        
        if not self.file_service.file_exists(self.archived_dir):
            self.file_service.create_directory(self.archived_dir)
    
    def _get_project_metadata_path(self, project_id: str, archived: bool = False) -> str:
        """Get the path to a project's metadata file.
        
        Args:
            project_id: ID of the project
            archived: Whether the project is archived
            
        Returns:
            str: Path to the project's metadata file
        """
        base_dir = self.archived_dir if archived else self.projects_dir
        return os.path.join(base_dir, f"{project_id}.json")
    
    def _get_project_tasks_path(self, project_id: str, archived: bool = False) -> str:
        """Get the path to a project's tasks file.
        
        Args:
            project_id: ID of the project
            archived: Whether the project is archived
            
        Returns:
            str: Path to the project's tasks file
        """
        base_dir = self.archived_dir if archived else self.projects_dir
        return os.path.join(base_dir, f"{project_id}.md")
    
    def _load_project_metadata(self, project_id: str, archived: bool = False) -> Optional[Dict]:
        """Load a project's metadata.
        
        Args:
            project_id: ID of the project
            archived: Whether the project is archived
            
        Returns:
            Dict or None: Project metadata, or None if the project doesn't exist
        """
        metadata_path = self._get_project_metadata_path(project_id, archived)
        
        try:
            content = self.file_service.read_file(metadata_path)
            return json.loads(content)
        except FileNotFoundError:
            return None
    
    def _save_project_metadata(self, project_id: str, metadata: Dict, archived: bool = False) -> None:
        """Save a project's metadata.
        
        Args:
            project_id: ID of the project
            metadata: Project metadata
            archived: Whether the project is archived
        """
        metadata_path = self._get_project_metadata_path(project_id, archived)
        content = json.dumps(metadata, indent=2)
        self.file_service.write_file(metadata_path, content)
    
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
        # Check if a project with the same name already exists
        existing_projects = self.list_projects(include_archived=True)
        for project in existing_projects:
            if project["name"] == name:
                raise ValueError(f"Project with name '{name}' already exists")
        
        # Generate a new project ID
        project_id = str(uuid.uuid4())
        
        # Create project metadata
        timestamp = time.time()
        metadata = {
            "id": project_id,
            "name": name,
            "description": description or "",
            "created_at": timestamp,
            "archived_at": None,
            "tags": []
        }
        
        # Save project metadata
        self._save_project_metadata(project_id, metadata)
        
        # Create an empty tasks file
        tasks_path = self._get_project_tasks_path(project_id)
        self.file_service.write_file(tasks_path, f"# {name}\n\n{description or ''}\n\n## Tasks\n\n")
        
        return project_id
    
    def archive_project(self, project_id: str) -> bool:
        """Archive a project.
        
        Args:
            project_id: ID of the project to archive
            
        Returns:
            bool: True if the project was archived, False if not found
        """
        # Load project metadata
        metadata = self._load_project_metadata(project_id)
        if metadata is None:
            return False
        
        # Update archived timestamp
        metadata["archived_at"] = time.time()
        
        # Move project files to archived directory
        metadata_path = self._get_project_metadata_path(project_id)
        tasks_path = self._get_project_tasks_path(project_id)
        
        archived_metadata_path = self._get_project_metadata_path(project_id, archived=True)
        archived_tasks_path = self._get_project_tasks_path(project_id, archived=True)
        
        # Read the content of the files
        metadata_content = self.file_service.read_file(metadata_path)
        tasks_content = self.file_service.read_file(tasks_path)
        
        # Write the content to the archived location
        self.file_service.write_file(archived_metadata_path, metadata_content)
        self.file_service.write_file(archived_tasks_path, tasks_content)
        
        # Delete the original files
        self.file_service.delete_file(metadata_path)
        self.file_service.delete_file(tasks_path)
        
        # Save updated metadata to the archived location
        self._save_project_metadata(project_id, metadata, archived=True)
        
        return True
    
    def delete_archived_project(self, project_id: Optional[str] = None) -> int:
        """Delete archived projects.
        
        Args:
            project_id: Optional ID of a specific archived project to delete.
                      If None, all archived projects will be deleted.
            
        Returns:
            int: Number of projects deleted
        """
        if project_id is not None:
            # Delete a specific archived project
            metadata_path = self._get_project_metadata_path(project_id, archived=True)
            tasks_path = self._get_project_tasks_path(project_id, archived=True)
            
            if not self.file_service.file_exists(metadata_path):
                return 0
            
            self.file_service.delete_file(metadata_path)
            self.file_service.delete_file(tasks_path)
            return 1
        else:
            # Delete all archived projects
            json_files = self.file_service.list_files(self.archived_dir, "*.json")
            md_files = self.file_service.list_files(self.archived_dir, "*.md")
            
            for file_path in json_files + md_files:
                self.file_service.delete_file(file_path)
            
            return len(json_files)
    
    def list_projects(self, include_archived: bool = False) -> List[Dict]:
        """List all projects.
        
        Args:
            include_archived: If True, include archived projects in the list
            
        Returns:
            List[dict]: List of project information dictionaries
        """
        # Get all project metadata files
        active_json_files = self.file_service.list_files(self.projects_dir, "*.json")
        
        # Load active projects
        projects = []
        for file_path in active_json_files:
            content = self.file_service.read_file(file_path)
            try:
                metadata = json.loads(content)
                projects.append(metadata)
            except json.JSONDecodeError:
                # Skip invalid JSON files
                continue
        
        # Load archived projects if requested
        if include_archived:
            archived_json_files = self.file_service.list_files(self.archived_dir, "*.json")
            for file_path in archived_json_files:
                content = self.file_service.read_file(file_path)
                try:
                    metadata = json.loads(content)
                    projects.append(metadata)
                except json.JSONDecodeError:
                    # Skip invalid JSON files
                    continue
        
        # Sort projects by creation time (newest first)
        projects.sort(key=lambda p: p.get("created_at", 0), reverse=True)
        
        return projects
    
    def get_task_service(self, project_id: str) -> TaskService:
        """Get a TaskService instance for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            TaskService: Task service for the project
            
        Raises:
            ValueError: If the project doesn't exist or is archived
        """
        # Check if the project exists and is not archived
        metadata = self._load_project_metadata(project_id)
        if metadata is None:
            # Check if it's an archived project
            if self._load_project_metadata(project_id, archived=True) is not None:
                raise ValueError(f"Project {project_id} is archived")
            else:
                raise ValueError(f"Project {project_id} does not exist")
        
        # Get the path to the project's tasks file
        tasks_path = self._get_project_tasks_path(project_id)
        
        # Create and return a TaskService for the project
        return MarkdownTaskService(tasks_path)
    
    def add_tag(self, project_id: str, tag: str) -> bool:
        """Add a tag to a project.
        
        Args:
            project_id: ID of the project
            tag: Tag to add
            
        Returns:
            bool: True if the tag was added, False if the project doesn't exist
                 or is archived
        """
        # Load project metadata
        metadata = self._load_project_metadata(project_id)
        if metadata is None:
            return False
        
        # Add the tag if it doesn't already exist
        if tag not in metadata.get("tags", []):
            if "tags" not in metadata:
                metadata["tags"] = []
            metadata["tags"].append(tag)
            
            # Save updated metadata
            self._save_project_metadata(project_id, metadata)
        
        return True
    
    def remove_tag(self, project_id: str, tag: str) -> bool:
        """Remove a tag from a project.
        
        Args:
            project_id: ID of the project
            tag: Tag to remove
            
        Returns:
            bool: True if the tag was removed, False if the project doesn't exist,
                 is archived, or didn't have the tag
        """
        # Load project metadata
        metadata = self._load_project_metadata(project_id)
        if metadata is None:
            return False
        
        # Remove the tag if it exists
        if tag in metadata.get("tags", []):
            metadata["tags"].remove(tag)
            
            # Save updated metadata
            self._save_project_metadata(project_id, metadata)
            return True
        
        return False
    
    def list_projects_by_tag(self, tag: str, include_archived: bool = False) -> List[Dict]:
        """List projects with a specific tag.
        
        Args:
            tag: Tag to filter by
            include_archived: If True, include archived projects in the list
            
        Returns:
            List[dict]: List of project information dictionaries
        """
        # Get all projects
        all_projects = self.list_projects(include_archived=include_archived)
        
        # Filter projects by tag
        return [p for p in all_projects if tag in p.get("tags", [])]
    
    def reset_tags(self, project_id: str) -> bool:
        """Reset (remove all) tags from a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            bool: True if the tags were reset, False if the project doesn't exist
                 or is archived
        """
        # Load project metadata
        metadata = self._load_project_metadata(project_id)
        if metadata is None:
            return False
        
        # Reset tags
        metadata["tags"] = []
        
        # Save updated metadata
        self._save_project_metadata(project_id, metadata)
        
        return True
    
    def get_tags(self, project_id: str) -> Set[str]:
        """Get all tags associated with a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Set[str]: Set of tags. Empty set if the project doesn't exist or is archived.
        """
        # Load project metadata
        metadata = self._load_project_metadata(project_id)
        if metadata is None:
            return set()
        
        return set(metadata.get("tags", []))
