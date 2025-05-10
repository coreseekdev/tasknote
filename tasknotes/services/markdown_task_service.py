"""Markdown-based task service implementation for TaskNotes.

This module provides a concrete implementation of the TaskService interface
that stores tasks in markdown files and uses the MarkdownService for parsing.
"""

import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any, Iterator

from tasknotes.interface import TaskService, MarkdownService, EditSession
from tasknotes.interface.markdown_service import HeadSection, ListItem


class MarkdownTaskService(TaskService):
    """Implementation of TaskService that uses markdown files for storage.
    
    Tasks are stored as markdown list items with checkboxes, and can be
    organized under headers and tagged.
    """
    
    TASK_HEADER = "## Tasks"
    TAG_COLLECTION_HEADER = "## Tag Collections"
    
    def __init__(self, file_path: Union[str, Path], content: Optional[str] = None):
        """
        Initialize a TaskService instance from a file or content.

        Args:
            file_path: Path to the markdown file representing the project
            content: Optional content to use instead of reading from file_path
        """
        self.file_path = Path(file_path) if isinstance(file_path, str) else file_path
        
        # Import here to avoid circular imports
        from ...core.markdown import MarkdownServiceImpl
        
        self.markdown_service = MarkdownServiceImpl()
        
        # Import here to avoid circular imports
        from ...core.edit_session_ot import OTEditSession
        
        # Initialize content
        if content is not None:
            self.content = content
        else:
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.content = f.read()
            except FileNotFoundError:
                self.content = f"# Untitled Project\n\n{self.TASK_HEADER}\n\n{self.TAG_COLLECTION_HEADER}\n\n"
        
        # Create an edit session for tracking changes
        self.edit_session = OTEditSession(self.content)
        
        # Cache for tag collections
        self._tag_collections = self._load_tag_collections()
    
    def _get_task_section(self) -> Optional[HeadSection]:
        """Get the tasks section from the markdown content.
        
        Returns:
            HeadSection or None: The tasks section, or None if not found
        """
        headers = self.markdown_service.get_headers(self.edit_session.get_content())
        for header in headers:
            if header.text.strip() == self.TASK_HEADER.strip():
                return header
        return None
    
    def _get_tag_collection_section(self) -> Optional[HeadSection]:
        """Get the tag collections section from the markdown content.
        
        Returns:
            HeadSection or None: The tag collections section, or None if not found
        """
        headers = self.markdown_service.get_headers(self.edit_session.get_content())
        for header in headers:
            if header.text.strip() == self.TAG_COLLECTION_HEADER.strip():
                return header
        return None
    
    def _extract_task_id(self, task_text: str) -> Optional[str]:
        """Extract the task ID from a task description.
        
        Args:
            task_text: Text of the task
            
        Returns:
            str or None: Task ID if found, None otherwise
        """
        match = re.search(r'\[ID:([a-f0-9-]+)\]', task_text)
        return match.group(1) if match else None
    
    def _extract_tags(self, task_text: str) -> List[str]:
        """Extract tags from a task description.
        
        Args:
            task_text: Text of the task
            
        Returns:
            List[str]: List of tags
        """
        matches = re.findall(r'#(\w+)', task_text)
        return matches
    
    def _create_task_text(self, description: str, task_id: str, tags: List[str]) -> str:
        """Create the text for a task.
        
        Args:
            description: Task description
            task_id: Task ID
            tags: List of tags
            
        Returns:
            str: Task text
        """
        tag_text = ' '.join([f'#{tag}' for tag in tags]) if tags else ''
        return f"{description} [ID:{task_id}] {tag_text}".strip()
    
    def _load_tag_collections(self) -> Dict[str, List[str]]:
        """Load tag collections from the markdown content.
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping collection names to lists of tags
        """
        collections = {}
        section = self._get_tag_collection_section()
        
        if section is None:
            return collections
        
        for list_block in section.get_lists():
            for item in list_block.list_items():
                text = item.text.strip()
                if ':' in text:
                    name, tags_text = text.split(':', 1)
                    name = name.strip()
                    tags = [tag.strip() for tag in tags_text.split(',')]
                    collections[name] = tags
        
        return collections
    
    def _find_task_item(self, task_id: str) -> Optional[tuple[ListItem, HeadSection]]:
        """Find a task item by ID.
        
        Args:
            task_id: ID of the task to find
            
        Returns:
            tuple or None: Tuple of (ListItem, HeadSection) if found, None otherwise
        """
        task_section = self._get_task_section()
        if task_section is None:
            return None
        
        for list_block in task_section.get_lists():
            for item in list_block.list_items():
                if item.is_task and self._extract_task_id(item.text) == task_id:
                    return (item, task_section)
        
        return None
    
    def add_task(self, task_description: str, tags: Optional[List[str]] = None) -> str:
        """
        Add a new task to the project.

        Args:
            task_description: Description of the task
            tags: Optional list of tags to associate with the task

        Returns:
            Task ID of the newly created task
        """
        task_id = str(uuid.uuid4())
        tags = tags or []
        
        task_section = self._get_task_section()
        if task_section is None:
            # Create the tasks section if it doesn't exist
            content = self.edit_session.get_content()
            if self.TASK_HEADER not in content:
                position = len(content)
                self.edit_session.insert(position, f"\n\n{self.TASK_HEADER}\n\n")
            task_section = self._get_task_section()
        
        # Create the task text
        task_text = self._create_task_text(task_description, task_id, tags)
        
        # Add the task to the tasks section
        section_range = task_section.text_range
        position = section_range[1]  # End of the section
        
        # Check if there are existing tasks
        has_existing_tasks = False
        for list_block in task_section.get_lists():
            has_existing_tasks = True
            break
        
        if has_existing_tasks:
            self.edit_session.insert(position, f"- [ ] {task_text}\n")
        else:
            self.edit_session.insert(position, f"\n- [ ] {task_text}\n")
        
        return task_id
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from the project.

        Args:
            task_id: ID of the task to delete

        Returns:
            True if the task was deleted, False otherwise
        """
        result = self._find_task_item(task_id)
        if result is None:
            return False
        
        task_item, _ = result
        item_range = task_item.text_range
        
        # Delete the task line including the newline
        start = item_range[0] - 6  # Include "- [ ] " or "- [x] "
        end = item_range[1] + 1  # Include newline
        
        self.edit_session.delete(start, end)
        return True
    
    def modify_task(self, task_id: str, new_description: str) -> bool:
        """
        Modify the description of a task.

        Args:
            task_id: ID of the task to modify
            new_description: New description for the task

        Returns:
            True if the task was modified, False otherwise
        """
        result = self._find_task_item(task_id)
        if result is None:
            return False
        
        task_item, _ = result
        
        # Extract existing tags
        tags = self._extract_tags(task_item.text)
        
        # Create new task text
        new_text = self._create_task_text(new_description, task_id, tags)
        
        # Replace the task text
        item_range = task_item.text_range
        self.edit_session.replace(item_range[0], item_range[1], new_text)
        
        return True
    
    def mark_as_completed(self, task_id: str, completed: bool = True) -> bool:
        """
        Mark a task as completed or not completed.

        Args:
            task_id: ID of the task to mark
            completed: True to mark as completed, False to mark as not completed

        Returns:
            True if the task status was updated, False otherwise
        """
        result = self._find_task_item(task_id)
        if result is None:
            return False
        
        task_item, _ = result
        item_range = task_item.text_range
        
        # Determine the current state and position
        content = self.edit_session.get_content()
        line_start = content.rfind('\n', 0, item_range[0]) + 1
        checkbox_start = line_start + 2  # After "- "
        
        # Replace the checkbox
        if completed:
            self.edit_session.replace(checkbox_start, checkbox_start + 3, "[x]")
        else:
            self.edit_session.replace(checkbox_start, checkbox_start + 3, "[ ]")
        
        return True
    
    def add_tag_to_task(self, task_id: str, tag: str) -> bool:
        """
        Add a tag to a task.

        Args:
            task_id: ID of the task to tag
            tag: Tag to add to the task

        Returns:
            True if the tag was added, False otherwise
        """
        result = self._find_task_item(task_id)
        if result is None:
            return False
        
        task_item, _ = result
        
        # Check if the tag already exists
        existing_tags = self._extract_tags(task_item.text)
        if tag in existing_tags:
            return True
        
        # Add the tag to the end of the task text
        item_range = task_item.text_range
        self.edit_session.insert(item_range[1], f" #{tag}")
        
        return True
    
    def remove_tag_from_task(self, task_id: str, tag: str) -> bool:
        """
        Remove a tag from a task.

        Args:
            task_id: ID of the task
            tag: Tag to remove from the task

        Returns:
            True if the tag was removed, False otherwise
        """
        result = self._find_task_item(task_id)
        if result is None:
            return False
        
        task_item, _ = result
        text = task_item.text
        
        # Check if the tag exists
        pattern = rf'#{tag}\b'
        if not re.search(pattern, text):
            return False
        
        # Remove the tag
        new_text = re.sub(pattern, '', text)
        # Clean up any double spaces
        new_text = re.sub(r'  +', ' ', new_text).strip()
        
        # Replace the task text
        item_range = task_item.text_range
        self.edit_session.replace(item_range[0], item_range[1], new_text)
        
        return True
    
    def replace_task_tags(self, task_id: str, tags: List[str]) -> bool:
        """
        Replace all tags associated with a task.

        Args:
            task_id: ID of the task
            tags: New list of tags to associate with the task

        Returns:
            True if the tags were replaced, False otherwise
        """
        result = self._find_task_item(task_id)
        if result is None:
            return False
        
        task_item, _ = result
        text = task_item.text
        
        # Remove existing tags
        text_without_tags = re.sub(r'#\w+', '', text)
        # Clean up any double spaces
        text_without_tags = re.sub(r'  +', ' ', text_without_tags).strip()
        
        # Extract task ID
        task_id_match = re.search(r'\[ID:([a-f0-9-]+)\]', text_without_tags)
        if not task_id_match:
            return False
        
        # Extract description (everything before the ID)
        description = text_without_tags.split(f"[ID:{task_id_match.group(1)}]")[0].strip()
        
        # Create new task text with updated tags
        new_text = self._create_task_text(description, task_id, tags)
        
        # Replace the task text
        item_range = task_item.text_range
        self.edit_session.replace(item_range[0], item_range[1], new_text)
        
        return True
    
    def list_tasks_by_tag(self, tag: str) -> List[Dict[str, Union[str, List[str], bool]]]:
        """
        List all tasks associated with a specific tag.

        Args:
            tag: Tag to filter tasks by

        Returns:
            List of task dictionaries containing id, description, tags, and completion status
        """
        return self.list_tasks_by_tags([tag])
    
    def list_tasks_by_tags(self, tags: List[str]) -> List[Dict[str, Union[str, List[str], bool]]]:
        """
        List all tasks associated with any of the specified tags (OR relationship).

        Args:
            tags: List of tags to filter tasks by

        Returns:
            List of task dictionaries containing id, description, tags, and completion status
        """
        all_tasks = self.get_all_tasks()
        
        if not tags:
            return all_tasks
        
        # Filter tasks by tags (OR relationship)
        filtered_tasks = []
        for task in all_tasks:
            task_tags = task.get("tags", [])
            if any(tag in task_tags for tag in tags):
                filtered_tasks.append(task)
        
        return filtered_tasks
    
    def create_tag_collection(self, collection_name: str, tags: List[str]) -> bool:
        """
        Create a named collection of tags that can be referenced together.

        Args:
            collection_name: Name for the tag collection
            tags: List of tags to include in the collection

        Returns:
            True if the collection was created, False otherwise
        """
        # Get or create the tag collections section
        section = self._get_tag_collection_section()
        if section is None:
            # Create the tag collections section if it doesn't exist
            content = self.edit_session.get_content()
            position = len(content)
            self.edit_session.insert(position, f"\n\n{self.TAG_COLLECTION_HEADER}\n\n")
            section = self._get_tag_collection_section()
        
        # Format the tag collection
        tags_text = ", ".join(tags)
        collection_text = f"{collection_name}: {tags_text}"
        
        # Check if the collection already exists
        existing_collections = self._load_tag_collections()
        if collection_name in existing_collections:
            # Find and update the existing collection
            for list_block in section.get_lists():
                for item in list_block.list_items():
                    if item.text.startswith(f"{collection_name}:"):
                        item_range = item.text_range
                        self.edit_session.replace(item_range[0], item_range[1], collection_text)
                        self._tag_collections[collection_name] = tags
                        return True
        
        # Add the new collection
        section_range = section.text_range
        position = section_range[1]  # End of the section
        
        # Check if there are existing collections
        has_existing_collections = False
        for list_block in section.get_lists():
            has_existing_collections = True
            break
        
        if has_existing_collections:
            self.edit_session.insert(position, f"- {collection_text}\n")
        else:
            self.edit_session.insert(position, f"\n- {collection_text}\n")
        
        # Update the cache
        self._tag_collections[collection_name] = tags
        
        return True
    
    def list_tasks_by_tag_collection(self, collection_name: str) -> List[Dict[str, Union[str, List[str], bool]]]:
        """
        List all tasks associated with any tag in the specified collection.

        Args:
            collection_name: Name of the tag collection to use for filtering

        Returns:
            List of task dictionaries containing id, description, tags, and completion status
        """
        collections = self._load_tag_collections()
        if collection_name not in collections:
            return []
        
        tags = collections[collection_name]
        return self.list_tasks_by_tags(tags)
    
    def get_all_tasks(self) -> List[Dict[str, Union[str, List[str], bool]]]:
        """
        Get all tasks in the project.

        Returns:
            List of task dictionaries containing id, description, tags, and completion status
        """
        tasks = []
        task_section = self._get_task_section()
        
        if task_section is None:
            return tasks
        
        for list_block in task_section.get_lists():
            for item in list_block.list_items():
                if item.is_task:
                    task_id = self._extract_task_id(item.text)
                    if task_id:
                        # Extract description (everything before the ID)
                        text = item.text
                        id_part = f"[ID:{task_id}]"
                        description = text.split(id_part)[0].strip()
                        
                        # Extract tags
                        tags = self._extract_tags(text)
                        
                        tasks.append({
                            "id": task_id,
                            "description": description,
                            "tags": tags,
                            "completed": item.is_completed_task
                        })
        
        return tasks
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Union[str, List[str], bool]]]:
        """
        Get a specific task by ID.

        Args:
            task_id: ID of the task to retrieve

        Returns:
            Task dictionary containing id, description, tags, and completion status,
            or None if the task does not exist
        """
        result = self._find_task_item(task_id)
        if result is None:
            return None
        
        task_item, _ = result
        text = task_item.text
        
        # Extract description (everything before the ID)
        id_part = f"[ID:{task_id}]"
        description = text.split(id_part)[0].strip()
        
        # Extract tags
        tags = self._extract_tags(text)
        
        return {
            "id": task_id,
            "description": description,
            "tags": tags,
            "completed": task_item.is_completed_task
        }
    
    def flush(self) -> bool:
        """
        Save the current state of the project to its file.

        Returns:
            True if the project was saved successfully, False otherwise
        """
        try:
            # Ensure the parent directory exists
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the content to the file
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.edit_session.get_content())
            
            return True
        except Exception:
            return False
