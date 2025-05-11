"""Base command class for TaskNotes command queue system."""

import abc
import io
import json
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TextIO, Union, TYPE_CHECKING

# Import TaskNoteEnv for type checking
if TYPE_CHECKING:
    from tasknotes.core.task_env import TaskNoteEnv


@dataclass
class CmdResult:
    """Result of a command execution.
    
    This class contains the result of executing a command, including whether it was
    successful, any message to display to the user, and structured data for further
    processing or formatting.
    """
    
    success: bool = True
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    exit_code: int = 0
    command: str = ""
    command_args: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> Dict[str, Any]:
        """Convert the result to a JSON-serializable dictionary.
        
        Returns:
            Dict[str, Any]: A JSON-serializable representation of the result
        """
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "exit_code": self.exit_code,
            "command": self.command,
            "command_args": self.command_args
        }
    
    def __str__(self) -> str:
        """String representation of the command result.
        
        Returns:
            str: A string representation of the command result
        """
        return json.dumps(self.to_json(), indent=2)


class BaseCmd(abc.ABC):
    """Base class for all commands in the command queue system."""
    
    def __init__(
        self,
        command: str,
        args: Dict[str, Any],
        stdin: Optional[TextIO] = None,
        stdout: Optional[TextIO] = None,
        stderr: Optional[TextIO] = None
    ):
        """Initialize a command.
        
        Args:
            command: The command name
            args: The command arguments
            stdin: Input stream (defaults to sys.stdin)
            stdout: Output stream (defaults to sys.stdout)
            stderr: Error stream (defaults to sys.stderr)
        """
        self.command = command
        self.args = args
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
    
    @abc.abstractmethod
    def _execute_impl(self, cmd_service: 'CmdService', task_env: 'TaskNoteEnv') -> CmdResult:
        """Implementation of the command execution.
        
        This method should be implemented by subclasses to perform the actual command execution.
        
        Args:
            cmd_service: The command service to use for executing additional commands
            task_env: The task environment providing access to task data and services
            
        Returns:
            CmdResult: The result of the command execution
        """
        pass
    
    def execute(self, cmd_service: 'CmdService', task_env: 'TaskNoteEnv') -> CmdResult:
        """Execute the command and populate the result with command information.
        
        This method calls the _execute_impl method and ensures that the result
        contains the command name and arguments.
        
        Args:
            cmd_service: The command service to use for executing additional commands
            task_env: The task environment providing access to task data and services
            
        Returns:
            CmdResult: The result of the command execution with command information
        """
        result = self._execute_impl(cmd_service, task_env)
        
        # Populate command information in the result
        result.command = self.command
        result.command_args = self.args.copy()
        
        return result
    
    def to_json(self) -> Dict[str, Any]:
        """Convert the command to a JSON-serializable dictionary.
        
        Returns:
            Dict[str, Any]: A JSON-serializable representation of the command
        """
        # Create a basic representation
        result = {
            "command": self.command,
            "args": self.args,
        }
        
        # Handle stdin specially - if it's a StringIO, include the content
        if self.stdin is sys.stdin:
            result["stdin"] = "<stdin>"
        elif isinstance(self.stdin, io.StringIO):
            # Get the current position
            pos = self.stdin.tell()
            # Rewind to the beginning
            self.stdin.seek(0)
            # Read the content
            content = self.stdin.read()
            # Restore the position
            self.stdin.seek(pos)
            # Add the content to the result
            result["stdin"] = content
        else:
            result["stdin"] = "<custom>"
        
        # Handle stdout and stderr
        result["stdout"] = "<stdout>" if self.stdout is sys.stdout else "<custom>"
        result["stderr"] = "<stderr>" if self.stderr is sys.stderr else "<custom>"
        
        return result
    
    def __str__(self) -> str:
        """String representation of the command result.
        
        Returns:
            str: A string representation of the command result
        """
        return json.dumps(self.to_json(), indent=2)


def create_string_input(content: Union[str, List[str]]) -> TextIO:
    """Create a string input stream from a string or list of strings.
    
    Args:
        content: The content to use as input. Can be a string or a list of strings.
        
    Returns:
        TextIO: A text input stream containing the content
    """
    if isinstance(content, list):
        content = "\n".join(content)
    
    return io.StringIO(content)