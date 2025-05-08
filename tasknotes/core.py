"""Core functionality for TaskNotes."""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, cast

from tasknotes.models import Task
from tasknotes.config import Config


class TaskManager:
    """Manages task operations including creation, retrieval, and storage."""
    
    def __init__(self, config: Optional[Config] = None) -> None:
        """Initialize the TaskManager with optional configuration."""
        self.config = config or Config()
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure that the storage directory and files exist."""
        # Create tasks directory if it doesn't exist
        os.makedirs(self.config.tasks_dir, exist_ok=True)
        
        # Create index file if it doesn't exist
        if not os.path.exists(self.config.index_file):
            with open(self.config.index_file, "w", encoding="utf-8") as f:
                json.dump({"tasks": {}}, f)
    
    def _load_index(self) -> Dict[str, Any]:
        """Load the task index from file."""
        try:
            with open(self.config.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # If the file is corrupted or doesn't exist, create a new index
            return {"tasks": {}}
    
    def _save_index(self, index: Dict[str, Any]) -> None:
        """Save the task index to file."""
        with open(self.config.index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)
    
    def _get_task_path(self, task_id: str) -> Path:
        """Get the file path for a task."""
        return Path(self.config.tasks_dir) / f"{task_id}.md"
    
    def _parse_task_markdown(self, task_id: str, content: str) -> Task:
        """Parse a task from its markdown content."""
        # This is a simple implementation. In a real-world scenario,
        # we would use myst-parser to properly parse the markdown.
        lines = content.strip().split("\n")
        
        # Extract YAML frontmatter if present
        metadata: Dict[str, Any] = {}
        description = ""
        
        if content.startswith("---"):
            frontmatter_end = content.find("---", 3)
            if frontmatter_end != -1:
                frontmatter = content[3:frontmatter_end].strip()
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip()] = value.strip()
                
                description = content[frontmatter_end + 3:].strip()
        else:
            # No frontmatter, treat first line as title and rest as description
            if lines:
                title = lines[0].lstrip("#").strip()
                description = "\n".join(lines[1:]).strip()
                metadata["title"] = title
        
        # Load task data from index for additional metadata
        index = self._load_index()
        task_data = index["tasks"].get(task_id, {})
        
        # Create task object
        return Task(
            id=task_id,
            title=metadata.get("title", task_data.get("title", "Untitled Task")),
            status=metadata.get("status", task_data.get("status", "open")),
            description=description or task_data.get("description"),
            created_at=datetime.fromisoformat(task_data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(task_data.get("updated_at")) if task_data.get("updated_at") else None,
            tags=metadata.get("tags", task_data.get("tags", [])),
            metadata=metadata,
        )
    
    def _generate_markdown(self, task: Task) -> str:
        """Generate markdown content for a task."""
        # Create YAML frontmatter
        frontmatter = [
            "---",
            f"title: {task.title}",
            f"status: {task.status}",
            f"created_at: {task.created_at.isoformat()}",
        ]
        
        if task.updated_at:
            frontmatter.append(f"updated_at: {task.updated_at.isoformat()}")
        
        if task.tags:
            tags_str = ", ".join(task.tags)
            frontmatter.append(f"tags: {tags_str}")
        
        # Add any additional metadata
        for key, value in task.metadata.items():
            if key not in ["title", "status", "created_at", "updated_at", "tags"]:
                frontmatter.append(f"{key}: {value}")
        
        frontmatter.append("---")
        
        # Add title and description
        content = [
            f"# {task.title}",
            "",
            task.description or "",
        ]
        
        return "\n".join(frontmatter + content)
    
    def add_task(self, title: str, description: Optional[str] = None) -> Task:
        """Add a new task."""
        task = Task(
            title=title,
            description=description,
            created_at=datetime.now(),
        )
        
        # Save task to index
        index = self._load_index()
        index["tasks"][task.id] = task.to_dict()
        self._save_index(index)
        
        # Save task to markdown file
        markdown_content = self._generate_markdown(task)
        with open(self._get_task_path(task.id), "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        return task
    
    def get_task(self, task_id: str) -> Task:
        """Get a task by its ID."""
        task_path = self._get_task_path(task_id)
        
        if not task_path.exists():
            raise ValueError(f"Task with ID {task_id} not found")
        
        with open(task_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return self._parse_task_markdown(task_id, content)
    
    def list_tasks(self, status: str = "all") -> List[Task]:
        """List all tasks, optionally filtered by status."""
        index = self._load_index()
        tasks = []
        
        for task_id, task_data in index["tasks"].items():
            # Skip tasks that don't match the status filter
            if status != "all" and task_data.get("status") != status:
                continue
                
            try:
                task = self.get_task(task_id)
                tasks.append(task)
            except Exception:
                # Skip tasks that can't be loaded
                continue
        
        # Sort tasks by creation date, newest first
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)
    
    def update_task(self, task_id: str, **kwargs: Any) -> Task:
        """Update a task."""
        task = self.get_task(task_id)
        task.update(**kwargs)
        
        # Update index
        index = self._load_index()
        index["tasks"][task_id] = task.to_dict()
        self._save_index(index)
        
        # Update markdown file
        markdown_content = self._generate_markdown(task)
        with open(self._get_task_path(task_id), "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        return task
    
    def delete_task(self, task_id: str) -> None:
        """Delete a task."""
        task_path = self._get_task_path(task_id)
        
        if not task_path.exists():
            raise ValueError(f"Task with ID {task_id} not found")
        
        # Remove from index
        index = self._load_index()
        if task_id in index["tasks"]:
            del index["tasks"][task_id]
            self._save_index(index)
        
        # Delete markdown file
        os.remove(task_path)
