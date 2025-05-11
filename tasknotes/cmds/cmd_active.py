"""Implementation of the 'active' command."""

from typing import Any, Dict, List, Optional

from tasknotes.cmds.base_cmd import BaseCmd, CmdResult
from tasknotes.core.task_env import TaskNoteEnv


class ActiveCmd(BaseCmd):
    """Command to manage active tasks."""
    
    def _execute_impl(self, cmd_service: 'CmdService', task_env: TaskNoteEnv) -> CmdResult:
        """Execute the active command.
        
        Args:
            cmd_service: The command service to use for executing additional commands
            task_env: The task environment providing access to task data and services
            
        Returns:
            CmdResult: The result of the command execution
        """
        # In a real implementation, this would list active tasks from the repository
        # For now, we just return a success result with mock active tasks
        
        # Create mock active tasks
        active_tasks = [
            {"id": "TASK-001", "title": "Implement CLI parsing", "status": "active", "tags": ["important", "urgent"]}
        ]
        
        return CmdResult(
            success=True,
            message=f"Found {len(active_tasks)} active tasks",
            data={
                "active_tasks": active_tasks
            }
        )
