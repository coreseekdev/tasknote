"""Factory for creating command objects from CLI arguments."""

import argparse
import sys
from typing import Any, Dict, List, Optional, TextIO, Type

from tasknotes.cmds.base_cmd import BaseCmd, create_string_input


class CommandFactory:
    """Factory for creating command objects from CLI arguments."""
    
    def __init__(self):
        """Initialize the command factory."""
        self.cmd_registry: Dict[str, Type[BaseCmd]] = {}
    
    def register_cmd(self, cmd_name: str, cmd_class: Type[BaseCmd]) -> None:
        """Register a command class for a command name.
        
        Args:
            cmd_name: The command name
            cmd_class: The command class
        """
        self.cmd_registry[cmd_name] = cmd_class
    
    def create_from_args(
        self,
        command: str,
        args: argparse.Namespace,
        stdin: Optional[TextIO] = None,
        stdout: Optional[TextIO] = None,
        stderr: Optional[TextIO] = None
    ) -> Optional[BaseCmd]:
        """Create a command instance from CLI arguments.
        
        Args:
            command: The command name
            args: The parsed arguments from argparse
            stdin: Input stream (defaults to sys.stdin)
            stdout: Output stream (defaults to sys.stdout)
            stderr: Error stream (defaults to sys.stderr)
            
        Returns:
            Optional[BaseCmd]: The created command instance, or None if the command is not registered
        """
        cmd_class = self.cmd_registry.get(command)
        if cmd_class is None:
            return None
        
        # Convert args to dictionary
        args_dict = vars(args)
        
        # Handle special cases for stdin
        stdin = self._prepare_stdin(command, args_dict, stdin)
        
        return cmd_class(command, args_dict, stdin=stdin, stdout=stdout, stderr=stderr)
    
    def _prepare_stdin(
        self,
        command: str,
        args_dict: Dict[str, Any],
        stdin: Optional[TextIO]
    ) -> TextIO:
        """Prepare stdin for the command based on arguments.
        
        This handles special cases like multiple -m flags or -f - for reading from stdin.
        
        Args:
            command: The command name
            args_dict: The command arguments as a dictionary
            stdin: The default stdin to use
            
        Returns:
            TextIO: The prepared stdin
        """
        # Default to system stdin if not provided
        stdin = stdin or sys.stdin
        
        # Handle note command with multiple -m flags
        if command == "note" and "message" in args_dict and args_dict["message"]:
            messages = args_dict["message"]
            if isinstance(messages, list) and len(messages) > 0:
                return create_string_input(messages)
        
        # Handle file input from stdin
        if "file" in args_dict and args_dict["file"] == "-":
            # Using stdin as file input, so we keep it as is
            return stdin
        
        return stdin


# Create a singleton instance
cmd_factory = CommandFactory()
