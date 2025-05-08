"""Tests for the core TaskNotes functionality."""

import os
import tempfile
import shutil
from pathlib import Path
from unittest import TestCase, main
from typing import Dict, Any, Optional

from tasknotes.core import TaskManager
from tasknotes.config import Config
from tasknotes.models import Task


class TestTaskManager(TestCase):
    """Test cases for TaskManager class."""
    
    def setUp(self) -> None:
        """Set up test environment."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.config = Config(config_path=self.test_dir)
        self.task_manager = TaskManager(config=self.config)
    
    def tearDown(self) -> None:
        """Clean up test environment."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_add_task(self) -> None:
        """Test adding a new task."""
        task = self.task_manager.add_task(
            title="Test Task",
            description="This is a test task"
        )
        
        # Verify task was created with correct attributes
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.description, "This is a test task")
        self.assertEqual(task.status, "open")
        
        # Verify task was saved to file
        task_path = Path(self.config.tasks_dir) / f"{task.id}.md"
        self.assertTrue(task_path.exists())
        
        # Verify task is in the index
        index = self.task_manager._load_index()
        self.assertIn(task.id, index["tasks"])
    
    def test_get_task(self) -> None:
        """Test retrieving a task."""
        # Add a task first
        original_task = self.task_manager.add_task(
            title="Test Task",
            description="This is a test task"
        )
        
        # Retrieve the task
        retrieved_task = self.task_manager.get_task(original_task.id)
        
        # Verify task attributes
        self.assertEqual(retrieved_task.id, original_task.id)
        self.assertEqual(retrieved_task.title, original_task.title)
        self.assertEqual(retrieved_task.description, original_task.description)
        self.assertEqual(retrieved_task.status, original_task.status)
    
    def test_list_tasks(self) -> None:
        """Test listing tasks."""
        # Add some tasks
        task1 = self.task_manager.add_task(title="Task 1")
        task2 = self.task_manager.add_task(title="Task 2")
        
        # Update task2 status
        self.task_manager.update_task(task2.id, status="closed")
        
        # List all tasks
        all_tasks = self.task_manager.list_tasks()
        self.assertEqual(len(all_tasks), 2)
        
        # List open tasks
        open_tasks = self.task_manager.list_tasks(status="open")
        self.assertEqual(len(open_tasks), 1)
        self.assertEqual(open_tasks[0].title, "Task 1")
        
        # List closed tasks
        closed_tasks = self.task_manager.list_tasks(status="closed")
        self.assertEqual(len(closed_tasks), 1)
        self.assertEqual(closed_tasks[0].title, "Task 2")
    
    def test_update_task(self) -> None:
        """Test updating a task."""
        # Add a task
        task = self.task_manager.add_task(title="Original Title")
        
        # Update the task
        updated_task = self.task_manager.update_task(
            task.id,
            title="Updated Title",
            status="in-progress",
            description="New description"
        )
        
        # Verify updates
        self.assertEqual(updated_task.title, "Updated Title")
        self.assertEqual(updated_task.status, "in-progress")
        self.assertEqual(updated_task.description, "New description")
        
        # Verify updated_at was set
        self.assertIsNotNone(updated_task.updated_at)
        
        # Retrieve the task again to ensure updates were saved
        retrieved_task = self.task_manager.get_task(task.id)
        self.assertEqual(retrieved_task.title, "Updated Title")
    
    def test_delete_task(self) -> None:
        """Test deleting a task."""
        # Add a task
        task = self.task_manager.add_task(title="Task to Delete")
        
        # Verify task exists
        task_path = Path(self.config.tasks_dir) / f"{task.id}.md"
        self.assertTrue(task_path.exists())
        
        # Delete the task
        self.task_manager.delete_task(task.id)
        
        # Verify task file was deleted
        self.assertFalse(task_path.exists())
        
        # Verify task was removed from index
        index = self.task_manager._load_index()
        self.assertNotIn(task.id, index["tasks"])
        
        # Verify get_task raises an error
        with self.assertRaises(ValueError):
            self.task_manager.get_task(task.id)


if __name__ == "__main__":
    main()
