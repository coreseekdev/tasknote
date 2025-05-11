"""Implementation of the 'list' command."""

from typing import Any, Dict, List, Optional

from tasknotes.cmds.base_cmd import BaseCmd, CmdResult
from tasknotes.core.task_env import TaskNoteEnv


class ListCmd(BaseCmd):
    """Command to list tasks with optional filtering."""
    
    def execute(self, cmd_service: 'CmdService', task_env: TaskNoteEnv) -> CmdResult:
        """Execute the list command.
        
        Args:
            cmd_service: The command service to use for executing additional commands
            task_env: The task environment providing access to task data and services
            
        Returns:
            CmdResult: The result of the command execution
        """
        # Get command arguments
        tags = self.args.get("tag", [])
        status = None
        
        # Check if we're listing active tasks
        if "_" in self.args and self.args["_"] and self.args["_"][0] == "active":
            status = "active"
        
        # In a real implementation, this would list tasks from the repository
        # For now, we just return a success result with mock task data
        
        # Create mock task list
        tasks = [
            {"id": "TASK-001", "title": "Implement CLI parsing", "status": "active", "tags": ["important", "urgent"]},
            {"id": "TASK-002", "title": "Write documentation", "status": "open", "tags": ["documentation"]},
            {"id": "TASK-003", "title": "Fix bugs", "status": "open", "tags": ["bug", "important"]}
        ]
        
        # Apply filters
        if status:
            tasks = [task for task in tasks if task["status"] == status]
        
        if tags:
            filtered_tasks = []
            for task in tasks:
                if any(tag in task["tags"] for tag in tags):
                    filtered_tasks.append(task)
            tasks = filtered_tasks
        
        return CmdResult(
            success=True,
            message=f"Found {len(tasks)} tasks",
            data={
                "tasks": tasks,
                "filters": {
                    "tags": tags,
                    "status": status
                }
            }
        )
