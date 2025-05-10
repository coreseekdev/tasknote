"""File-based project service implementation for TaskNotes.

This module provides a concrete implementation of the ProjectService interface
that stores projects as files using the FileService.
"""

import json
import os
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from tasknotes.interface import FileService, ProjectService, TaskService
from tasknotes.interface.markdown_service import DocumentMeta
from tasknotes.core.config import config
from tasknotes.core.project_meta import ProjectMeta
from .markdown_task_service import MarkdownTaskService
from .numbering_service import TaskNumberingService


class FileProjectService(ProjectService):
    """Implementation of ProjectService that uses FileService for storage.
    
    Projects are stored in two directories:
    - 'projects': Active projects
    - 'archived': Archived projects
    
    Each project is stored as a JSON metadata file and has an associated
    markdown file for tasks.
    """
    
    def __init__(self, file_service: FileService, numbering_service: Optional[TaskNumberingService] = None):
        """Initialize a FileProjectService instance.
        
        Args:
            file_service: The file service to use for storage
            numbering_service: Optional numbering service for project IDs
        """
        self.file_service = file_service
        self.numbering_service = numbering_service
        
        # Get project directories from config
        self.projects_dir = config.get("projects.active_dir", "projects")
        self.archived_dir = config.get("projects.archived_dir", "archived")
        
        # Ensure the project directories exist
        if not self.file_service.file_exists(self.projects_dir):
            self.file_service.create_directory(self.projects_dir)
        
        if not self.file_service.file_exists(self.archived_dir):
            self.file_service.create_directory(self.archived_dir)
            
        # Initialize numbering service if not provided
        if self.numbering_service is None:
            self.numbering_service = TaskNumberingService(file_service)
            
        # Cache for project metadata
        self._meta_cache: Dict[str, Tuple[Union[DocumentMeta, ProjectMeta], float]] = {}
    

    
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
    
    def _get_markdown_service(self):
        """Get the markdown service instance.
        
        Returns:
            MarkdownService: The markdown service instance
        """
        # Import here to avoid circular imports
        from tasknotes.core.markdown import create_markdown_service
        return create_markdown_service()
    
    def _get_document_meta(self, project_id: str, archived: bool = False) -> Optional[DocumentMeta]:
        """Get the DocumentMeta object for a project, with caching.
        
        Args:
            project_id: ID of the project
            archived: Whether the project is archived
            
        Returns:
            DocumentMeta or None: The document metadata object, or None if not found
        """
        tasks_path = self._get_project_tasks_path(project_id, archived)
        cache_key = f"{tasks_path}:{archived}:doc"
        
        # Check if we have a cached version and if it's still valid
        if cache_key in self._meta_cache:
            meta, timestamp = self._meta_cache[cache_key]
            try:
                # Check if the file has been modified since we cached it
                file_timestamp = self.file_service.get_modified_time(tasks_path)
                if file_timestamp <= timestamp:
                    return meta
            except FileNotFoundError:
                # File no longer exists, remove from cache
                del self._meta_cache[cache_key]
                return None
        
        try:
            # Read the file and parse metadata
            content = self.file_service.read_file(tasks_path)
            markdown_service = self._get_markdown_service()
            meta = markdown_service.get_meta(content)
            
            # Cache the result with current timestamp
            current_time = time.time()
            self._meta_cache[cache_key] = (meta, current_time)
            
            return meta
        except FileNotFoundError:
            return None
    
    def _get_project_meta(self, project_id: str, archived: bool = False) -> Optional[ProjectMeta]:
        """Get the ProjectMeta object for a project, with caching.
        
        Args:
            project_id: ID of the project
            archived: Whether the project is archived
            
        Returns:
            ProjectMeta or None: The project metadata object, or None if not found
        """
        tasks_path = self._get_project_tasks_path(project_id, archived)
        cache_key = f"{tasks_path}:{archived}:project"
        
        # Check if we have a cached version and if it's still valid
        if cache_key in self._meta_cache:
            meta, timestamp = self._meta_cache[cache_key]
            try:
                # Check if the file has been modified since we cached it
                file_timestamp = self.file_service.get_modified_time(tasks_path)
                if file_timestamp <= timestamp:
                    return meta
            except FileNotFoundError:
                # File no longer exists, remove from cache
                del self._meta_cache[cache_key]
                return None
        
        # Get the document metadata first
        doc_meta = self._get_document_meta(project_id, archived)
        if doc_meta is None:
            return None
        
        # Extract name and description from the markdown content
        name, description = self._extract_project_info(project_id, archived)
        
        # Create a ProjectMeta object
        project_meta = ProjectMeta(
            _id=project_id,
            _name=name,
            _description=description,
            _doc_meta=doc_meta
        )
        
        # Cache the result with current timestamp
        current_time = time.time()
        self._meta_cache[cache_key] = (project_meta, current_time)
        
        return project_meta
    
    def _extract_project_info(self, project_id: str, archived: bool = False) -> Tuple[str, str]:
        """Extract project name and description from the markdown file.
        
        Args:
            project_id: ID of the project
            archived: Whether the project is archived
            
        Returns:
            Tuple[str, str]: The project name and description
        """
        tasks_path = self._get_project_tasks_path(project_id, archived)
        name = "Untitled Project"
        description = ""
        
        try:
            content = self.file_service.read_file(tasks_path)
            markdown_service = self._get_markdown_service()
            
            # Get the first level-1 header
            headers = list(markdown_service.get_headers(content))
            if headers and headers[0].head_level == 1:
                name = headers[0].text
                
                # Extract description from the text between the first header and the next header
                start, end = headers[0].text_range
                next_header_start = len(content)
                if len(headers) > 1:
                    next_header_start = headers[1].text_range[0]
                
                # Extract text between headers, skipping the header itself
                header_end = content.find('\n', start)
                if header_end > 0 and header_end < next_header_start:
                    description_text = content[header_end:next_header_start].strip()
                    # Remove any markdown formatting
                    # description = re.sub(r'\s+', ' ', description_text).strip()
                    description = description_text
        except FileNotFoundError:
            pass
        
        return name, description
    
    def _load_project_metadata(self, project_id: str, archived: bool = False) -> Optional[Dict]:
        """Load a project's metadata from the markdown file's frontmatter.
        
        Args:
            project_id: ID of the project
            archived: Whether the project is archived
            
        Returns:
            Dict or None: Project metadata, or None if the project doesn't exist
        """
        project_meta = self._get_project_meta(project_id, archived)
        if project_meta is None:
            return None
        
        # Convert the ProjectMeta to a dictionary
        return project_meta.to_dict()
    
    def _save_project_metadata(self, project_id: str, metadata: Dict, archived: bool = False) -> None:
        """Save a project's metadata to the markdown file's frontmatter.
        
        Args:
            project_id: ID of the project
            metadata: Project metadata
            archived: Whether the project is archived
        """
        tasks_path = self._get_project_tasks_path(project_id, archived)
        doc_cache_key = f"{tasks_path}:{archived}:doc"
        project_cache_key = f"{tasks_path}:{archived}:project"
        
        try:
            # Import here to avoid circular imports
            from tasknotes.core.edit_session_ot import EditSessionOT
            
            # 先尝试获取缓存的 project_meta 对象
            project_meta = self._get_project_meta(project_id, archived)
            
            # 读取文件内容创建编辑会话
            content = self.file_service.read_file(tasks_path)
            edit_session = EditSessionOT(content)
            
            # 如果没有缓存的 project_meta 对象，则创建一个新的
            if project_meta is None:
                markdown_service = self._get_markdown_service()
                doc_meta = markdown_service.get_meta(content)
                name, description = self._extract_project_info(project_id, archived)
                project_meta = ProjectMeta(
                    _id=project_id,
                    _name=name,
                    _description=description,
                    _doc_meta=doc_meta
                )
            
            # 更新元数据 (只更新 DocumentMeta 中的数据，不更新 id 和 name)
            for key, value in metadata.items():
                if key not in ['id', 'name']:
                    if key == 'description':
                        project_meta.description = value
                    else:
                        project_meta.set_meta(key, value)
            
            # 应用更改并获取更新后的内容
            updated_content = project_meta.apply(edit_session, self.file_service, tasks_path)
            
            # 保存更新后的内容
            self.file_service.write_file(tasks_path, updated_content)
            
            # 更新缓存
            current_time = time.time()
            self._meta_cache[project_cache_key] = (project_meta, current_time)
            self._meta_cache[doc_cache_key] = (project_meta.doc_meta, current_time)
        except FileNotFoundError:
            # If the file doesn't exist, create it with the metadata
            from tasknotes.core.edit_session_ot import EditSessionOT
            
            # Create a basic markdown file with the metadata
            name = metadata.get('name', 'Untitled Project')
            description = metadata.get('description', '')
            
            # Create content with name and description
            content = f"# {name}\n"
            if description:
                content += f"\n{description}\n"
            content += "\n## Tasks\n\n## Tag Collections\n\n"
            
            edit_session = EditSessionOT(content)
            
            # Create metadata and save it
            markdown_service = self._get_markdown_service()
            doc_meta = markdown_service.get_meta(content)
            
            # Create a ProjectMeta object
            project_meta = ProjectMeta(
                _id=project_id,
                _name=name,
                _description=description,
                _doc_meta=doc_meta
            )
            
            # Update metadata (excluding id and name)
            for key, value in metadata.items():
                if key not in ['id', 'name', 'description']:
                    project_meta.set_meta(key, value)
            
            # 应用更改并获取更新后的内容
            updated_content = project_meta.apply(edit_session, self.file_service, tasks_path)
            
            # 保存更新后的内容
            self.file_service.write_file(tasks_path, updated_content)
            
            # 更新缓存
            current_time = time.time()
            self._meta_cache[project_cache_key] = (project_meta, current_time)
            self._meta_cache[doc_cache_key] = (project_meta.doc_meta, current_time)
    
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
        
        # Generate a new project ID using the numbering service
        project_id = self.numbering_service.get_next_number()
        
        # Create the project metadata - only store creation time and tags in metadata
        # project_id comes from the filename, name from the first header, description from the header text
        metadata = {
            "created_at": time.time(),
            "tags": []
        }
        
        # Create the markdown content with the project name and description
        content = f"# {name}\n"
        if description:
            content += f"\n{description}\n"
        content += "\n## Tasks\n\n## Tag Collections\n\n"
        
        # Create the project file
        tasks_path = self._get_project_tasks_path(project_id)
        self.file_service.write_file(tasks_path, content)
        
        # Save the metadata (this will update the file with frontmatter)
        self._save_project_metadata(project_id, metadata)
        
        return project_id
    
    def archive_project(self, project_id: str) -> bool:
        """Archive a project.
        
        Args:
            project_id: ID of the project to archive
            
        Returns:
            bool: True if the project was archived, False if not found
        """
        # Check if the project exists
        metadata = self._load_project_metadata(project_id)
        if metadata is None:
            return False
        
        # Update metadata with archive timestamp
        metadata["archived_at"] = time.time()
        
        # Get the paths
        tasks_path = self._get_project_tasks_path(project_id)
        archived_tasks_path = self._get_project_tasks_path(project_id, archived=True)
        
        # Use transaction to ensure atomicity
        with self.file_service.transaction(f"Archive project {project_id}"):
            # Move the file to the archived location using rename
            self.file_service.rename(tasks_path, archived_tasks_path)
            
            # Save updated metadata to the archived location
            self._save_project_metadata(project_id, metadata, archived=True)
        
        # Clear the cache for the active project
        doc_cache_key = f"{tasks_path}:False:doc"
        project_cache_key = f"{tasks_path}:False:project"
        if doc_cache_key in self._meta_cache:
            del self._meta_cache[doc_cache_key]
        if project_cache_key in self._meta_cache:
            del self._meta_cache[project_cache_key]
        
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
            tasks_path = self._get_project_tasks_path(project_id, archived=True)
            
            if not self.file_service.file_exists(tasks_path):
                return 0
            
            # Delete the file
            self.file_service.delete_file(tasks_path)
            
            # Clear the cache
            doc_cache_key = f"{tasks_path}:True:doc"
            project_cache_key = f"{tasks_path}:True:project"
            if doc_cache_key in self._meta_cache:
                del self._meta_cache[doc_cache_key]
            if project_cache_key in self._meta_cache:
                del self._meta_cache[project_cache_key]
                
            return 1
        else:
            # Delete all archived projects using a transaction
            md_files = self.file_service.list_files(self.archived_dir, "*.md")
            
            if not md_files:
                return 0
                
            # Use transaction to batch delete all files
            with self.file_service.transaction("Delete all archived projects"):
                for file_path in md_files:
                    full_path = os.path.join(self.archived_dir, file_path)
                    self.file_service.delete_file(full_path)
                    
                    # Clear the cache
                    doc_cache_key = f"{full_path}:True:doc"
                    project_cache_key = f"{full_path}:True:project"
                    if doc_cache_key in self._meta_cache:
                        del self._meta_cache[doc_cache_key]
                    if project_cache_key in self._meta_cache:
                        del self._meta_cache[project_cache_key]
            
            return len(md_files)
    
    def list_projects(self, include_archived: bool = False) -> List[Dict]:
        """List all projects.
        
        Args:
            include_archived: If True, include archived projects in the list
            
        Returns:
            List[dict]: List of project information dictionaries
        """
        projects = []
        
        # List active projects
        active_files = self.file_service.list_files(self.projects_dir, "*.md")
        for file in active_files:
            project_id = os.path.splitext(os.path.basename(file))[0]
            
            # Load project metadata
            metadata = self._load_project_metadata(project_id)
            if metadata is not None:
                metadata["archived"] = False
                projects.append(metadata)
        
        # List archived projects if requested
        if include_archived:
            archived_files = self.file_service.list_files(self.archived_dir, "*.md")
            for file in archived_files:
                project_id = os.path.splitext(os.path.basename(file))[0]
                
                # Load project metadata
                metadata = self._load_project_metadata(project_id, archived=True)
                if metadata is not None:
                    metadata["archived"] = True
                    projects.append(metadata)
        
        # Sort projects by name
        projects.sort(key=lambda p: p.get("name", ""))
        
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
