"""File-based task service implementation for TaskNotes.

This module provides a concrete implementation of the TaskService interface
that uses MarkdownService to parse markdown text files and EditSession to edit them.
"""

import re
import time
from typing import Dict, List, Optional, Set, Tuple, Any, Iterator
from dataclasses import dataclass, field
from enum import Enum

from tasknotes.interface.file_service import FileService
from tasknotes.interface.task_service import TaskService, Task, TaskStatus
from tasknotes.interface.edit_session import EditSession, EditOperation
from tasknotes.interface.markdown_service import (
    MarkdownService,
    HeadSection,
    ListBlock,
    ListItem,
    DocumentMeta
)
from tasknotes.core.markdown import create_markdown_service


class TaskSection(Enum):
    """Enum for task sections in the markdown file."""
    TASKS = "Tasks"
    NOTES = "Notes"
    TAGS = "Tags"
    MILESTONES = "Milestones"
    KANBAN = "Kanban"


@dataclass
class FileTask(Task):
    """Implementation of Task interface for file-based tasks."""
    task_id: str
    context: Dict[str, Any] = field(default_factory=dict)
    _title: str = ""
    _description: str = ""
    _status: TaskStatus = TaskStatus.OPEN
    _tags: List[str] = field(default_factory=list)
    _parent_id: Optional[str] = None
    _subtasks: List[str] = field(default_factory=list)
    _notes: List[Dict[str, Any]] = field(default_factory=list)
    _created_at: float = field(default_factory=time.time)
    _modified_at: float = field(default_factory=time.time)
    
    @property
    def title(self) -> str:
        return self._title
    
    @title.setter
    def title(self, value: str) -> None:
        self._title = value
        self._modified_at = time.time()
    
    @property
    def description(self) -> str:
        return self._description
    
    @description.setter
    def description(self, value: str) -> None:
        self._description = value
        self._modified_at = time.time()
    
    @property
    def status(self) -> TaskStatus:
        return self._status
    
    @status.setter
    def status(self, value: TaskStatus) -> None:
        self._status = value
        self._modified_at = time.time()
    
    @property
    def tags(self) -> List[str]:
        return self._tags.copy()
    
    def add_tag(self, tag: str) -> bool:
        if tag in self._tags:
            return False
        self._tags.append(tag)
        self._modified_at = time.time()
        return True
    
    def remove_tag(self, tag: str) -> bool:
        if tag not in self._tags:
            return False
        self._tags.remove(tag)
        self._modified_at = time.time()
        return True
    
    @property
    def parent_id(self) -> Optional[str]:
        return self._parent_id
    
    @parent_id.setter
    def parent_id(self, value: Optional[str]) -> None:
        self._parent_id = value
        self._modified_at = time.time()
    
    @property
    def subtasks(self) -> List[str]:
        return self._subtasks.copy()
    
    def add_subtask(self, task_id: str) -> bool:
        if task_id in self._subtasks:
            return False
        self._subtasks.append(task_id)
        self._modified_at = time.time()
        return True
    
    def remove_subtask(self, task_id: str) -> bool:
        if task_id not in self._subtasks:
            return False
        self._subtasks.remove(task_id)
        self._modified_at = time.time()
        return True
    
    @property
    def notes(self) -> List[Dict[str, Any]]:
        return self._notes.copy()
    
    def add_note(self, note: Dict[str, Any]) -> str:
        note_id = note.get("id", f"note-{len(self._notes) + 1}")
        note["id"] = note_id
        note["created_at"] = note.get("created_at", time.time())
        self._notes.append(note)
        self._modified_at = time.time()
        return note_id
    
    def update_note(self, note_id: str, note: Dict[str, Any]) -> bool:
        for i, existing_note in enumerate(self._notes):
            if existing_note.get("id") == note_id:
                note["id"] = note_id
                note["created_at"] = existing_note.get("created_at", time.time())
                note["modified_at"] = time.time()
                self._notes[i] = note
                self._modified_at = time.time()
                return True
        return False
    
    def remove_note(self, note_id: str) -> bool:
        for i, note in enumerate(self._notes):
            if note.get("id") == note_id:
                del self._notes[i]
                self._modified_at = time.time()
                return True
        return False
    
    @property
    def created_at(self) -> float:
        return self._created_at
    
    @property
    def modified_at(self) -> float:
        return self._modified_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the task to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the task
        """
        return {
            "id": self.task_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "tags": self.tags,
            "parent_id": self.parent_id,
            "subtasks": self.subtasks,
            "notes": self.notes,
            "created_at": self.created_at,
            "modified_at": self.modified_at
        }


class FileTaskService:
    """Implementation of TaskService that uses markdown files for storage."""
    
    def __init__(self, file_service: FileService, task_file_path: str):
        """Initialize a FileTaskService instance.
        
        Args:
            file_service: The file service to use for storage
            task_file_path: Path to the markdown file containing tasks
        """
        self.file_service = file_service
        self.task_file_path = task_file_path
        self.markdown_service = create_markdown_service()
        
        # Cache for task data
        self._tasks: Dict[str, FileTask] = {}
        self._content: Optional[str] = None
        self._last_modified: float = 0
        
    def _get_content(self) -> str:
        """Get the current content of the task file.
        
        Returns:
            str: The content of the task file
        """
        try:
            # Check if the file has been modified since last read
            modified_time = self.file_service.get_modified_time(self.task_file_path)
            if self._content is None or modified_time > self._last_modified:
                self._content = self.file_service.read_file(self.task_file_path)
                self._last_modified = modified_time
            return self._content
        except FileNotFoundError:
            # If the file doesn't exist, return an empty string
            return ""
    
    def _create_edit_session(self) -> EditSession:
        """Create an edit session for the task file.
        
        Returns:
            EditSession: An edit session for the task file
        """
        content = self._get_content()
        
        # Import here to avoid circular imports
        from tasknotes.core.edit_session import SimpleEditSession
        return SimpleEditSession(content)
    
    def _save_content(self, content: str) -> None:
        """Save content to the task file.
        
        Args:
            content: The content to save
        """
        self.file_service.write_file(self.task_file_path, content)
        self._content = content
        self._last_modified = time.time()
    
    def _parse_tasks(self, content: str) -> Dict[str, FileTask]:
        """Parse tasks from markdown content.
        
        Args:
            content: Markdown content to parse
            
        Returns:
            Dict[str, FileTask]: Dictionary of tasks by ID
        """
        tasks = {}
        
        # Parse the markdown content
        headers = list(self.markdown_service.get_headers(content))
        
        # Find the Tasks section
        tasks_section = None
        for header in headers:
            if header.text == TaskSection.TASKS.value and header.head_level == 2:
                tasks_section = header
                break
        
        if tasks_section is None:
            return tasks
        
        # Process task lists
        for list_block in tasks_section.get_lists():
            for list_item in list_block.list_items():
                # Check if this is a task item
                text = list_item.text
                
                # Parse task ID and title
                match = re.match(r'^\s*\[([^\]]+)\]\s+(.+)$', text)
                if match:
                    task_id = match.group(1).strip()
                    title = match.group(2).strip()
                    
                    # Create a task object
                    task = FileTask(
                        task_id=task_id,
                        _title=title
                    )
                    
                    # Check for task status
                    if list_item.is_task():
                        if list_item.is_completed_task():
                            task._status = TaskStatus.DONE
                        else:
                            task._status = TaskStatus.ACTIVE
                    
                    # Add to tasks dictionary
                    tasks[task_id] = task
        
        # Process notes section
        notes_section = None
        for header in headers:
            if header.text == TaskSection.NOTES.value and header.head_level == 2:
                notes_section = header
                break
        
        if notes_section:
            for list_block in notes_section.get_lists():
                for list_item in list_block.list_items():
                    text = list_item.text
                    
                    # Parse note format: [TASK-001] Note content
                    match = re.match(r'^\s*\[([^\]]+)\]\s+(.+)$', text)
                    if match:
                        task_id = match.group(1).strip()
                        note_content = match.group(2).strip()
                        
                        if task_id in tasks:
                            tasks[task_id].add_note({
                                "content": note_content,
                                "category": "general"
                            })
        
        # Process tags section
        tags_section = None
        for header in headers:
            if header.text == TaskSection.TAGS.value and header.head_level == 2:
                tags_section = header
                break
        
        if tags_section:
            for list_block in tags_section.get_lists():
                for list_item in list_block.list_items():
                    text = list_item.text
                    
                    # Parse tag format: tag: TASK-001, TASK-002
                    match = re.match(r'^\s*([^:]+):\s+(.+)$', text)
                    if match:
                        tag = match.group(1).strip()
                        task_ids = [tid.strip() for tid in match.group(2).split(',')]
                        
                        for task_id in task_ids:
                            if task_id in tasks:
                                tasks[task_id].add_tag(tag)
        
        return tasks
    
    def _update_task_in_markdown(self, task: FileTask, edit_session: EditSession) -> None:
        """Update a task in the markdown content.
        
        Args:
            task: The task to update
            edit_session: The edit session to use for updates
        """
        content = edit_session.get_content()
        
        # Parse the markdown content
        headers = list(self.markdown_service.get_headers(content))
        
        # Find the Tasks section
        tasks_section = None
        for header in headers:
            if header.text == TaskSection.TASKS.value and header.head_level == 2:
                tasks_section = header
                break
        
        if tasks_section is None:
            # If no Tasks section exists, create one
            # Find the position to insert the section
            pos = 0
            if len(headers) > 0:
                # Insert after the last header
                last_header = headers[-1]
                pos = last_header.text_range[1]
            
            # Insert the Tasks section
            tasks_section_text = f"\n\n## {TaskSection.TASKS.value}\n\n"
            edit_session.insert(pos, tasks_section_text)
            
            # Re-parse the content
            content = edit_session.get_content()
            headers = list(self.markdown_service.get_headers(content))
            
            for header in headers:
                if header.text == TaskSection.TASKS.value and header.head_level == 2:
                    tasks_section = header
                    break
        
        # Check if the task already exists in the Tasks section
        task_found = False
        for list_block in tasks_section.get_lists():
            for list_item in list_block.list_items():
                text = list_item.text
                
                # Parse task ID and title
                match = re.match(r'^\s*\[([^\]]+)\]\s+(.+)$', text)
                if match and match.group(1).strip() == task.task_id:
                    # Update the task
                    start, end = list_item.text_range
                    
                    # Format the task status
                    status_marker = ""
                    if task.status == TaskStatus.ACTIVE:
                        status_marker = "- [ ] "
                    elif task.status == TaskStatus.DONE:
                        status_marker = "- [x] "
                    else:
                        status_marker = "- "
                    
                    # Create the updated task text
                    updated_text = f"{status_marker}[{task.task_id}] {task.title}"
                    
                    # Replace the task text
                    edit_session.replace(start, end, updated_text)
                    task_found = True
                    break
            
            if task_found:
                break
        
        if not task_found:
            # If the task doesn't exist, add it to the Tasks section
            # Find the position to insert the task
            pos = tasks_section.text_range[1]
            
            # Format the task status
            status_marker = ""
            if task.status == TaskStatus.ACTIVE:
                status_marker = "- [ ] "
            elif task.status == TaskStatus.DONE:
                status_marker = "- [x] "
            else:
                status_marker = "- "
            
            # Create the task text
            task_text = f"\n{status_marker}[{task.task_id}] {task.title}\n"
            
            # Insert the task
            edit_session.insert(pos, task_text)
        
        # Update tags
        self._update_tags_in_markdown(task, edit_session)
        
        # Update notes
        self._update_notes_in_markdown(task, edit_session)
    
    def _update_tags_in_markdown(self, task: FileTask, edit_session: EditSession) -> None:
        """Update task tags in the markdown content.
        
        Args:
            task: The task to update tags for
            edit_session: The edit session to use for updates
        """
        content = edit_session.get_content()
        
        # Parse the markdown content
        headers = list(self.markdown_service.get_headers(content))
        
        # Find the Tags section
        tags_section = None
        for header in headers:
            if header.text == TaskSection.TAGS.value and header.head_level == 2:
                tags_section = header
                break
        
        if tags_section is None:
            # If no Tags section exists, create one
            # Find the position to insert the section
            pos = 0
            if len(headers) > 0:
                # Insert after the last header
                last_header = headers[-1]
                pos = last_header.text_range[1]
            
            # Insert the Tags section
            tags_section_text = f"\n\n## {TaskSection.TAGS.value}\n\n"
            edit_session.insert(pos, tags_section_text)
            
            # Re-parse the content
            content = edit_session.get_content()
            headers = list(self.markdown_service.get_headers(content))
            
            for header in headers:
                if header.text == TaskSection.TAGS.value and header.head_level == 2:
                    tags_section = header
                    break
        
        # Process existing tags
        tag_items: Dict[str, Tuple[ListItem, List[str]]] = {}
        
        for list_block in tags_section.get_lists():
            for list_item in list_block.list_items():
                text = list_item.text
                
                # Parse tag format: tag: TASK-001, TASK-002
                match = re.match(r'^\s*([^:]+):\s+(.+)$', text)
                if match:
                    tag = match.group(1).strip()
                    task_ids = [tid.strip() for tid in match.group(2).split(',')]
                    tag_items[tag] = (list_item, task_ids)
        
        # Update tags for the task
        for tag in task.tags:
            if tag in tag_items:
                # Update existing tag
                list_item, task_ids = tag_items[tag]
                
                if task.task_id not in task_ids:
                    task_ids.append(task.task_id)
                    
                    # Update the tag item
                    start, end = list_item.text_range
                    updated_text = f"{tag}: {', '.join(task_ids)}"
                    edit_session.replace(start, end, updated_text)
            else:
                # Add new tag
                pos = tags_section.text_range[1]
                tag_text = f"\n- {tag}: {task.task_id}\n"
                edit_session.insert(pos, tag_text)
        
        # Remove task from tags it no longer has
        for tag, (list_item, task_ids) in tag_items.items():
            if tag not in task.tags and task.task_id in task_ids:
                task_ids.remove(task.task_id)
                
                if task_ids:
                    # Update the tag item
                    start, end = list_item.text_range
                    updated_text = f"{tag}: {', '.join(task_ids)}"
                    edit_session.replace(start, end, updated_text)
                else:
                    # Remove the tag item if no tasks are left
                    start, end = list_item.text_range
                    edit_session.delete(start, end)
    
    def _update_notes_in_markdown(self, task: FileTask, edit_session: EditSession) -> None:
        """Update task notes in the markdown content.
        
        Args:
            task: The task to update notes for
            edit_session: The edit session to use for updates
        """
        content = edit_session.get_content()
        
        # Parse the markdown content
        headers = list(self.markdown_service.get_headers(content))
        
        # Find the Notes section
        notes_section = None
        for header in headers:
            if header.text == TaskSection.NOTES.value and header.head_level == 2:
                notes_section = header
                break
        
        if notes_section is None:
            # If no Notes section exists, create one
            # Find the position to insert the section
            pos = 0
            if len(headers) > 0:
                # Insert after the last header
                last_header = headers[-1]
                pos = last_header.text_range[1]
            
            # Insert the Notes section
            notes_section_text = f"\n\n## {TaskSection.NOTES.value}\n\n"
            edit_session.insert(pos, notes_section_text)
            
            # Re-parse the content
            content = edit_session.get_content()
            headers = list(self.markdown_service.get_headers(content))
            
            for header in headers:
                if header.text == TaskSection.NOTES.value and header.head_level == 2:
                    notes_section = header
                    break
        
        # Find existing notes for this task
        task_notes: List[ListItem] = []
        
        for list_block in notes_section.get_lists():
            for list_item in list_block.list_items():
                text = list_item.text
                
                # Parse note format: [TASK-001] Note content
                match = re.match(r'^\s*\[([^\]]+)\]\s+(.+)$', text)
                if match and match.group(1).strip() == task.task_id:
                    task_notes.append(list_item)
        
        # If the number of notes in the markdown doesn't match the task, update them
        if len(task_notes) != len(task.notes):
            # Remove all existing notes for this task
            for note_item in task_notes:
                start, end = note_item.text_range
                edit_session.delete(start, end)
            
            # Add all notes
            pos = notes_section.text_range[1]
            for note in task.notes:
                note_text = f"\n- [{task.task_id}] {note['content']}\n"
                edit_session.insert(pos, note_text)
                pos += len(note_text)
    
    def get_task(self, task_id: str) -> Optional[FileTask]:
        """Get a task by ID.
        
        Args:
            task_id: ID of the task to get
            
        Returns:
            Optional[FileTask]: The task, or None if not found
        """
        # Get the latest content
        content = self._get_content()
        
        # Parse tasks
        tasks = self._parse_tasks(content)
        
        # Update cache
        self._tasks = tasks
        
        # Return the requested task
        return tasks.get(task_id)
    
    def create_task(self, task_id: str, title: str, **kwargs) -> FileTask:
        """Create a new task.
        
        Args:
            task_id: ID of the task to create
            title: Title of the task
            **kwargs: Additional task properties
            
        Returns:
            FileTask: The created task
            
        Raises:
            ValueError: If a task with the same ID already exists
        """
        # Check if the task already exists
        if self.get_task(task_id) is not None:
            raise ValueError(f"Task with ID {task_id} already exists")
        
        # Create a new task
        task = FileTask(
            task_id=task_id,
            _title=title,
            **kwargs
        )
        
        # Create an edit session
        edit_session = self._create_edit_session()
        
        # Update the task in the markdown
        self._update_task_in_markdown(task, edit_session)
        
        # Save the content
        self._save_content(edit_session.get_content())
        
        # Update cache
        self._tasks[task_id] = task
        
        return task
    
    def update_task(self, task: FileTask) -> bool:
        """Update a task.
        
        Args:
            task: The task to update
            
        Returns:
            bool: True if the task was updated, False if not found
        """
        # Check if the task exists
        if self.get_task(task.task_id) is None:
            return False
        
        # Create an edit session
        edit_session = self._create_edit_session()
        
        # Update the task in the markdown
        self._update_task_in_markdown(task, edit_session)
        
        # Save the content
        self._save_content(edit_session.get_content())
        
        # Update cache
        self._tasks[task.task_id] = task
        
        return True
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task.
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            bool: True if the task was deleted, False if not found
        """
        # Check if the task exists
        task = self.get_task(task_id)
        if task is None:
            return False
        
        # Create an edit session
        edit_session = self._create_edit_session()
        content = edit_session.get_content()
        
        # Parse the markdown content
        headers = list(self.markdown_service.get_headers(content))
        
        # Find the Tasks section
        tasks_section = None
        for header in headers:
            if header.text == TaskSection.TASKS.value and header.head_level == 2:
                tasks_section = header
                break
        
        if tasks_section is None:
            return False
        
        # Find the task in the Tasks section
        for list_block in tasks_section.get_lists():
            for list_item in list_block.list_items():
                text = list_item.text
                
                # Parse task ID and title
                match = re.match(r'^\s*\[([^\]]+)\]\s+(.+)$', text)
                if match and match.group(1).strip() == task_id:
                    # Delete the task
                    start, end = list_item.text_range
                    edit_session.delete(start, end)
                    break
        
        # Remove task from tags
        tags_section = None
        for header in headers:
            if header.text == TaskSection.TAGS.value and header.head_level == 2:
                tags_section = header
                break
        
        if tags_section:
            for list_block in tags_section.get_lists():
                for list_item in list_block.list_items():
                    text = list_item.text
                    
                    # Parse tag format: tag: TASK-001, TASK-002
                    match = re.match(r'^\s*([^:]+):\s+(.+)$', text)
                    if match:
                        tag = match.group(1).strip()
                        task_ids = [tid.strip() for tid in match.group(2).split(',')]
                        
                        if task_id in task_ids:
                            task_ids.remove(task_id)
                            
                            if task_ids:
                                # Update the tag item
                                start, end = list_item.text_range
                                updated_text = f"{tag}: {', '.join(task_ids)}"
                                edit_session.replace(start, end, updated_text)
                            else:
                                # Remove the tag item if no tasks are left
                                start, end = list_item.text_range
                                edit_session.delete(start, end)
        
        # Remove task notes
        notes_section = None
        for header in headers:
            if header.text == TaskSection.NOTES.value and header.head_level == 2:
                notes_section = header
                break
        
        if notes_section:
            for list_block in notes_section.get_lists():
                for list_item in list_block.list_items():
                    text = list_item.text
                    
                    # Parse note format: [TASK-001] Note content
                    match = re.match(r'^\s*\[([^\]]+)\]\s+(.+)$', text)
                    if match and match.group(1).strip() == task_id:
                        # Delete the note
                        start, end = list_item.text_range
                        edit_session.delete(start, end)
        
        # Save the content
        self._save_content(edit_session.get_content())
        
        # Update cache
        if task_id in self._tasks:
            del self._tasks[task_id]
        
        return True
    
    def list_tasks(self, **filters) -> List[FileTask]:
        """List tasks with optional filtering.
        
        Args:
            **filters: Filters to apply
            
        Returns:
            List[FileTask]: List of tasks matching the filters
        """
        # Get the latest content
        content = self._get_content()
        
        # Parse tasks
        tasks = self._parse_tasks(content)
        
        # Update cache
        self._tasks = tasks
        
        # Apply filters
        filtered_tasks = list(tasks.values())
        
        # Filter by status
        if "status" in filters:
            status = filters["status"]
            if isinstance(status, str):
                status = TaskStatus(status)
            filtered_tasks = [t for t in filtered_tasks if t.status == status]
        
        # Filter by tag
        if "tag" in filters:
            tag = filters["tag"]
            filtered_tasks = [t for t in filtered_tasks if tag in t.tags]
        
        # Filter by parent
        if "parent_id" in filters:
            parent_id = filters["parent_id"]
            filtered_tasks = [t for t in filtered_tasks if t.parent_id == parent_id]
        
        # Sort by creation time (newest first)
        filtered_tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return filtered_tasks
    
    def search_tasks(self, query: str, **filters) -> List[FileTask]:
        """Search for tasks.
        
        Args:
            query: Search query
            **filters: Additional filters
            
        Returns:
            List[FileTask]: List of tasks matching the search query and filters
        """
        # Get all tasks
        tasks = self.list_tasks(**filters)
        
        # Filter by query
        if query:
            query = query.lower()
            filtered_tasks = []
            
            for task in tasks:
                # Search in title
                if query in task.title.lower():
                    filtered_tasks.append(task)
                    continue
                
                # Search in description
                if query in task.description.lower():
                    filtered_tasks.append(task)
                    continue
                
                # Search in notes
                for note in task.notes:
                    if query in note.get("content", "").lower():
                        filtered_tasks.append(task)
                        break
            
            return filtered_tasks
        
        return tasks
