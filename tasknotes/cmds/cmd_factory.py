"""Factory for creating command objects from CLI arguments."""

import argparse
import sys
from typing import Any, Dict, List, Optional, TextIO, Type

from tasknotes.cmds.base_cmd import BaseCmd, create_string_input
from tasknotes.cmds.cmd_init import InitCmd


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

# Import and register all command implementations
def register_all_commands():
    """Register all command implementations."""
    from tasknotes.cmds.cmd_init import InitCmd
    cmd_factory.register_cmd("init", InitCmd)
    
    # Import and register other commands as they are implemented
    try:
        from tasknotes.cmds.cmd_add import AddCmd
        cmd_factory.register_cmd("add", AddCmd)
    except ImportError:
        pass
    
    try:
        from tasknotes.cmds.cmd_note import NoteCmd
        cmd_factory.register_cmd("note", NoteCmd)
    except ImportError:
        pass
    
    try:
        from tasknotes.cmds.cmd_edit import EditCmd
        cmd_factory.register_cmd("edit", EditCmd)
    except ImportError:
        pass
    
    try:
        from tasknotes.cmds.cmd_list import ListCmd
        cmd_factory.register_cmd("list", ListCmd)
    except ImportError:
        pass
    
    try:
        from tasknotes.cmds.cmd_archive import ArchiveCmd
        cmd_factory.register_cmd("archive", ArchiveCmd)
    except ImportError:
        pass
    
    try:
        from tasknotes.cmds.cmd_remove import RemoveCmd
        cmd_factory.register_cmd("remove", RemoveCmd)
    except ImportError:
        pass
    
    try:
        from tasknotes.cmds.cmd_open import OpenCmd
        cmd_factory.register_cmd("open", OpenCmd)
    except ImportError:
        pass
    
    try:
        from tasknotes.cmds.cmd_active import ActiveCmd
        cmd_factory.register_cmd("active", ActiveCmd)
    except ImportError:
        pass
    
    try:
        from tasknotes.cmds.cmd_close import CloseCmd
        cmd_factory.register_cmd("close", CloseCmd)
    except ImportError:
        pass
    
    try:
        from tasknotes.cmds.cmd_done import DoneCmd
        cmd_factory.register_cmd("done", DoneCmd)
    except ImportError:
        pass
    
    try:
        from tasknotes.cmds.cmd_tag import TagCmd
        cmd_factory.register_cmd("tag", TagCmd)
    except ImportError:
        pass
    
    try:
        from tasknotes.cmds.cmd_search import SearchCmd
        cmd_factory.register_cmd("search", SearchCmd)
    except ImportError:
        pass
    
    try:
        from tasknotes.cmds.cmd_help import HelpCmd
        cmd_factory.register_cmd("help", HelpCmd)
    except ImportError:
        pass
    
    try:
        from tasknotes.cmds.cmd_mcp import McpCmd
        cmd_factory.register_cmd("mcp", McpCmd)
    except ImportError:
        pass

# Register the init command by default
cmd_factory.register_cmd("init", InitCmd)
