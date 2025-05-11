"""Command service for managing command queues."""

import json
import os
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Type, Union, TYPE_CHECKING

# Import TaskNoteEnv for type checking
if TYPE_CHECKING:
    from tasknotes.core.task_env import TaskNoteEnv

from tasknotes.cmds.base_cmd import BaseCmd, CmdResult


class CmdService:
    """Service for managing command queues and executing commands."""
    
    def __init__(self, task_env: Optional['TaskNoteEnv'] = None):
        """Initialize the command service.
        
        Args:
            task_env: The task environment providing access to task data and services
        """
        self.task_env = task_env
        self.cmd_queue: Deque[BaseCmd] = deque()
        self.cmd_registry: Dict[str, Type[BaseCmd]] = {}
        self.executed_cmds: List[BaseCmd] = []
        self.results: List[CmdResult] = []
        
        # Create task_env if not provided
        if self.task_env is None:
            self._create_default_task_env()
    
    def register_cmd(self, cmd_name: str, cmd_class: Type[BaseCmd]) -> None:
        """Register a command class for a command name.
        
        Args:
            cmd_name: The command name
            cmd_class: The command class
        """
        self.cmd_registry[cmd_name] = cmd_class
    
    def create_cmd(self, command: str, args: Dict[str, Any], **kwargs) -> Optional[BaseCmd]:
        """Create a command instance from a command name and arguments.
        
        Args:
            command: The command name
            args: The command arguments
            **kwargs: Additional arguments to pass to the command constructor
            
        Returns:
            Optional[BaseCmd]: The created command instance, or None if the command is not registered
        """
        cmd_class = self.cmd_registry.get(command)
        if cmd_class is None:
            return None
        
        return cmd_class(command, args, **kwargs)
    
    def add_cmd(self, cmd: BaseCmd) -> None:
        """Add a command to the queue.
        
        Args:
            cmd: The command to add
        """
        self.cmd_queue.append(cmd)
    
    def execute_all(self) -> List[CmdResult]:
        """Execute all commands in the queue.
        
        Returns:
            List[CmdResult]: The results of all executed commands
        """
        results = []
        
        while self.cmd_queue:
            cmd = self.cmd_queue.popleft()
            result = cmd.execute(self, self.task_env)
            self.executed_cmds.append(cmd)
            self.results.append(result)
            results.append(result)
        
        return results
    
    def execute_next(self) -> Optional[CmdResult]:
        """Execute the next command in the queue.
        
        Returns:
            Optional[CmdResult]: The result of the executed command, or None if the queue is empty
        """
        if not self.cmd_queue:
            return None
        
        cmd = self.cmd_queue.popleft()
        result = cmd.execute(self, self.task_env)
        self.executed_cmds.append(cmd)
        self.results.append(result)
        
        return result
    
    def to_json(self) -> Dict[str, Any]:
        """Convert the command service state to a JSON-serializable dictionary.
        
        Returns:
            Dict[str, Any]: A JSON-serializable representation of the command service state
        """
        return {
            "queue": [cmd.to_json() for cmd in self.cmd_queue],
            "executed": [cmd.to_json() for cmd in self.executed_cmds],
            "results": [
                {
                    "success": result.success,
                    "message": result.message,
                    "data": result.data,
                    "exit_code": result.exit_code
                }
                for result in self.results
            ]
        }
    
    def _create_default_task_env(self) -> None:
        """Create a default TaskNoteEnv instance for the current directory."""
        try:
            from tasknotes.core.task_env import TaskNoteEnv
            # Use the current working directory as the repository path
            cwd = os.getcwd()
            self.task_env = TaskNoteEnv(cwd)
        except ImportError:
            # If TaskNoteEnv can't be imported, leave task_env as None
            pass
    
    def __str__(self) -> str:
        """String representation of the command service.
        
        Returns:
            str: A string representation of the command service
        """
        return json.dumps(self.to_json(), indent=2)
