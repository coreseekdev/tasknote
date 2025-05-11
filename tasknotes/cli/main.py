"""Main entry point for TaskNotes CLI."""

import argparse
import json
import os
import sys
from typing import Dict, Any, List, Optional, Callable

# Check if Rich should be disabled via environment variable
RICH_DISABLED = os.environ.get("TASKNOTE_NO_RICH", "").lower() in ("1", "true", "yes")

# Try to import Rich for enhanced output, but make it optional
if not RICH_DISABLED:
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        RICH_AVAILABLE = True
    except ImportError:
        RICH_AVAILABLE = False
else:
    RICH_AVAILABLE = False

from tasknotes.cli.i18n import _
from tasknotes.cmds.base_cmd import BaseCmd
from tasknotes.cmds.cmd_service import CmdService
from tasknotes.cmds.cmd_factory import cmd_factory, register_all_commands
from tasknotes.core.task_env import TaskNoteEnv, find_file_service

# Create a console for output (rich if available, otherwise standard)
if RICH_AVAILABLE:
    console = Console()
else:
    # Create a simple console wrapper with similar interface
    class SimpleConsole:
        def print(self, *args, file=None, **kwargs):
            # Strip any rich formatting markers
            text = str(args[0])
            # Simple regex to remove rich formatting tags like [green] or [bold red]
            import re
            text = re.sub(r'\[([^\]]+)\]', '', text)
            print(text, file=file)
    
    console = SimpleConsole()

# Dictionary to store command-specific formatters
formatters = {}


def register_formatter(command: str, formatter_func: Callable):
    """Register a formatter function for a specific command.
    
    Args:
        command: The command name
        formatter_func: The formatter function that takes a CmdResult and formats it
    """
    formatters[command] = formatter_func


def format_and_display_result(result):
    """Format and display the command result based on its type.
    
    This function dispatches to command-specific formatters if available,
    otherwise falls back to a default formatter.
    
    Args:
        result: The CmdResult object to format and display
    """
    if not result.success:
        # For failed commands, display an error message
        if RICH_AVAILABLE:
            error_text = Text(f"Error: {result.message}", style="bold red")
            console.print(error_text, file=sys.stderr)
        else:
            print(f"Error: {result.message}", file=sys.stderr)
        return
    
    # Get the command name
    command = result.command
    
    # Dispatch to command-specific formatter if available
    if command in formatters:
        formatters[command](result, console, RICH_AVAILABLE)
    else:
        # Default formatter for commands without a specific formatter
        default_formatter(result, console, RICH_AVAILABLE)


def default_formatter(result, console, rich_available):
    """Default formatter for command results.
    
    Args:
        result: The CmdResult object to format
        console: The console to print to
        rich_available: Whether Rich is available for enhanced output
    """
    if rich_available:
        console.print(f"[green]{result.message}[/green]")
        
        # Print data as JSON if present
        if result.data:
            console.print(json.dumps(result.data, indent=2))
    else:
        # Simple output without Rich formatting
        print(result.message)
        
        # Print data as JSON if present
        if result.data:
            print(json.dumps(result.data, indent=2))


# Import command modules and their formatters
from tasknotes.cli.cmd_init import setup_init_parser, format_init_result
from tasknotes.cli.cmd_list import setup_list_parser, format_list_result
from tasknotes.cli.cmd_search import setup_search_parser, format_search_result

# Import other command modules
from tasknotes.cli.cmd_add import setup_add_parser
from tasknotes.cli.cmd_note import setup_note_parser
from tasknotes.cli.cmd_edit import setup_edit_parser
from tasknotes.cli.cmd_archive import setup_archive_parser
from tasknotes.cli.cmd_remove import setup_remove_parser
from tasknotes.cli.cmd_open import setup_open_parser
from tasknotes.cli.cmd_active import setup_active_parser
from tasknotes.cli.cmd_close import setup_close_parser
from tasknotes.cli.cmd_done import setup_done_parser
from tasknotes.cli.cmd_tag import setup_tag_parser
from tasknotes.cli.cmd_help import setup_help_parser
from tasknotes.cli.cmd_mcp import setup_mcp_parser

# Register formatters for specific commands
register_formatter("init", format_init_result)
register_formatter("list", format_list_result)
register_formatter("search", format_search_result)


def is_debug_mode() -> bool:
    """Check if debug mode is enabled via environment variable.
    
    Returns:
        bool: True if debug mode is enabled, False otherwise
    """
    return os.environ.get("TASKNOTE_CLI_DEBUG", "") != ""


def not_implemented_error() -> None:
    """Raise NotImplementedError when not in debug mode."""
    raise NotImplementedError(
        "This functionality is not yet implemented. "
        "Set TASKNOTE_CLI_DEBUG environment variable to see command parsing output."
    )


def setup_parsers() -> argparse.ArgumentParser:
    """Set up the main parser and all subparsers.
    
    Returns:
        argparse.ArgumentParser: The configured argument parser
    """
    # Create the main parser
    parser = argparse.ArgumentParser(
        prog="tasknote",
        description=_("TaskNote - A task management tool using markdown."),
        epilog=_("Set TASKNOTE_CLI_DEBUG environment variable to see command parsing output."),
        add_help=True,
    )
    
    # Add version information
    parser.add_argument(
        "--version", 
        action="version", 
        version="%(prog)s 1.0.0"
    )
    
    # Create subparsers
    subparsers = parser.add_subparsers(
        title=_("commands"),
        dest="command",
        description=_("valid commands"),
        help=_("command help"),
        required=True
    )
    
    # Set up each command's parser
    setup_init_parser(subparsers)
    setup_add_parser(subparsers)
    setup_note_parser(subparsers)
    setup_edit_parser(subparsers)
    setup_list_parser(subparsers)
    setup_archive_parser(subparsers)
    setup_remove_parser(subparsers)
    setup_open_parser(subparsers)
    setup_active_parser(subparsers)
    setup_close_parser(subparsers)
    setup_done_parser(subparsers)
    setup_tag_parser(subparsers)
    setup_search_parser(subparsers)
    setup_help_parser(subparsers)
    setup_mcp_parser(subparsers)
    
    return parser


# The _ function is imported from i18n module


def register_commands() -> None:
    """Register command implementations."""
    # Use the register_all_commands function to register all available commands
    register_all_commands()


def main() -> None:
    """Main entry point for the CLI."""
    # Register command implementations
    register_commands()
    
    # Parse command line arguments
    parser = setup_parsers()
    args = parser.parse_args()
    
    # Get the command name
    command = args.command
    
    # Create a TaskNoteEnv for the current directory
    cwd = os.getcwd()
    task_env = TaskNoteEnv(cwd)
    
    # Create a command service with the task environment
    cmd_service = CmdService(task_env)
    
    # Create a command from the arguments
    cmd = cmd_factory.create_from_args(command, args)
    
    if cmd is None:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        sys.exit(1)
    
    if is_debug_mode():
        # In debug mode, just print the command and exit
        print(json.dumps(cmd.to_json(), indent=2))
    else:
        # In normal mode, execute the command
        # Add the command to the service
        cmd_service.add_cmd(cmd)
        
        # Execute the command
        results = cmd_service.execute_all()
        
        # Format and display the results
        for result in results:
            # Format output based on command type
            format_and_display_result(result)
            
            # Exit with error code if command failed
            if not result.success:
                sys.exit(result.exit_code or 1)

if __name__ == "__main__":
    main()
