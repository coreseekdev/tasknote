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

from tasknotes.interface import FileService, ProjectService, FileTask
from tasknotes.interface.markdown_service import DocumentMeta
from tasknotes.core.config import config
from tasknotes.core.project_meta import ProjectMeta
# from .markdown_task_service import MarkdownTaskService
from .numbering_service import TaskNumberingService

# 项目模板 - 用于创建新项目
PROJECT_TEMPLATE = """# {name}

{description}

## Tasks

## Notes

## Tags

### Milestones 

### Kanban

1. TODO
2. DOING
3. DONE

"""

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

        try:
            # Read the file and parse metadata
            content = self.file_service.read_file(tasks_path)
            markdown_service = self._get_markdown_service()
            meta = markdown_service.get_meta(content)
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
    
    def _load_project_metadata(self, project_id: str, archived: bool = False) -> ProjectMeta:
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
        return project_meta
    
    def _save_project_metadata(self, project_id: str, project_meta: ProjectMeta, archived: bool = False) -> None:
        """Save a project's metadata to the markdown file's frontmatter.
        
        Args:
            project_id: ID of the project
            project_meta: The project metadata to save
            archived: Whether the project is archived
        """
        tasks_path = self._get_project_tasks_path(project_id, archived)
        
        try:
            # 导入 EditSession
            from tasknotes.core.edit_session_ot import EditSessionOT
            
            # 读取文件内容创建编辑会话
            content = self.file_service.read_file(tasks_path)
            edit_session = EditSessionOT(content)
            
            # 应用更改并获取更新后的内容
            updated_content = project_meta.apply(edit_session)
            
            # 保存更新后的内容
            self.file_service.write_file(tasks_path, updated_content)

        except FileNotFoundError:
            pass # 简单忽略
    
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
        
        # 使用模板创建项目内容
        content = PROJECT_TEMPLATE.format(
            name=name,
            description=description or ""
        )
        
        # 创建项目文件
        tasks_path = self._get_project_tasks_path(project_id)
        self.file_service.write_file(tasks_path, content)
        
        # 读取文件并解析元数据
        markdown_service = self._get_markdown_service()
        doc_meta = markdown_service.get_meta(content)
        
        # 创建 ProjectMeta 对象
        project_meta = ProjectMeta(
            _id=project_id,
            _name=name,
            _description=description or "",
            _doc_meta=doc_meta
        )
        
        # 设置创建时间和初始标签
        project_meta.set_meta("created_at", time.time())
        project_meta.set_meta("tags", [])
        
        # 保存元数据
        self._save_project_metadata(project_id, project_meta)
        
        return project_id
    
    def archive_project(self, project_id: str) -> bool:
        """Archive a project.
        
        Args:
            project_id: ID of the project to archive
            
        Returns:
            bool: True if the project was archived, False if not found
        """
        # Check if the project exists
        project_meta = self._load_project_metadata(project_id)
        if project_meta is None:
            return False
        
        # Update metadata with archive timestamp
        project_meta.set_meta("archived_at", time.time())
        
        # Get the paths
        tasks_path = self._get_project_tasks_path(project_id)
        archived_tasks_path = self._get_project_tasks_path(project_id, archived=True)
        
        # Use transaction to ensure atomicity
        with self.file_service.transaction(f"Archive project {project_id}"):
            # Move the file to the archived location using rename
            self.file_service.rename(tasks_path, archived_tasks_path)
            
            # Save updated metadata to the archived location
            self._save_project_metadata(project_id, project_meta, archived=True)
        
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
            project_meta = self._load_project_metadata(project_id)
            if project_meta is not None:
                # 转换为字典并添加归档标志
                project_dict = project_meta.to_dict()
                project_dict["archived"] = False
                projects.append(project_dict)
        
        # List archived projects if requested
        if include_archived:
            archived_files = self.file_service.list_files(self.archived_dir, "*.md")
            for file in archived_files:
                project_id = os.path.splitext(os.path.basename(file))[0]
                
                # Load project metadata
                project_meta = self._load_project_metadata(project_id, archived=True)
                if project_meta is not None:
                    # 转换为字典并添加归档标志
                    project_dict = project_meta.to_dict()
                    project_dict["archived"] = True
                    projects.append(project_dict)
        
        # Sort projects by name
        projects.sort(key=lambda p: p.get("name", ""))
        
        return projects
    
    def get_task(self, project_id: str) -> Optional[FileTask]:
        """Get a task service for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            FileTask or None: A task service for the project, or None if not found
        """
        raise NotImplementedError
    
    def add_tag(self, project_id: str, tag: str) -> bool:
        """Add a tag to a project.
        
        Args:
            project_id: ID of the project
            tag: Tag to add
            
        Returns:
            bool: True if the tag was added, False if not found or already exists
        """
        # Check if the project exists
        project_meta = self._load_project_metadata(project_id)
        if project_meta is None:
            return False
        
        # Get current tags
        tags = project_meta.tags
        
        # Check if the tag already exists
        if tag in tags:
            return False
        
        # Add the tag
        if tag not in tags:
            tags.append(tag)
            project_meta.tags = tags
            
            # Save the updated metadata
            self._save_project_metadata(project_id, project_meta)
            
        return True
    
    def remove_tag(self, project_id: str, tag: str) -> bool:
        """Remove a tag from a project.
        
        Args:
            project_id: ID of the project
            tag: Tag to remove
            
        Returns:
            bool: True if the tag was removed, False if not found
        """
        # Check if the project exists
        project_meta = self._load_project_metadata(project_id)
        if project_meta is None:
            return False
        
        # Get current tags
        tags = project_meta.tags
        
        # Check if the tag exists
        if tag in tags:
                    
            # Remove the tag
            tags.remove(tag)
            project_meta.tags = tags
            
            # Save the updated metadata
            self._save_project_metadata(project_id, project_meta)
        
        return True
      
    def reset_tags(self, project_id: str, tags: List[str]) -> bool:
        """Reset all tags for a project.
        
        Args:
            project_id: ID of the project
            tags: New list of tags
            
        Returns:
            bool: True if the tags were reset, False if not found
        """
        # Check if the project exists
        project_meta = self._load_project_metadata(project_id)
        if project_meta is None:
            return False
        
        # Reset the tags
        project_meta.tags = tags
        
        # Save the updated metadata
        self._save_project_metadata(project_id, project_meta)
        
        return True
    
    def get_tags(self, project_id: str) -> Optional[List[str]]:
        """Get all tags for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            List[str] or None: List of tags, or None if not found
        """
        # Check if the project exists
        project_meta = self._load_project_metadata(project_id)
        if project_meta is None:
            return None
        
        # Return the tags
        return project_meta.tags
