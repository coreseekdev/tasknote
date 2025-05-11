"""Main entry point for TaskNotes CLI."""

import argparse
import json
import os
import sys
from typing import Dict, Any, List, Optional

from tasknotes.cli.i18n import _
from tasknotes.cmds.base_cmd import BaseCmd
from tasknotes.cmds.cmd_service import CmdService
from tasknotes.cmds.cmd_factory import cmd_factory
from tasknotes.core.task_env import TaskNoteEnv, find_file_service

# Import command implementations
from tasknotes.cmds.cmd_init import InitCmd

# Import all command modules
from tasknotes.cli.cmd_init import setup_init_parser
from tasknotes.cli.cmd_add import setup_add_parser
from tasknotes.cli.cmd_note import setup_note_parser
from tasknotes.cli.cmd_edit import setup_edit_parser
from tasknotes.cli.cmd_list import setup_list_parser
from tasknotes.cli.cmd_archive import setup_archive_parser
from tasknotes.cli.cmd_remove import setup_remove_parser
from tasknotes.cli.cmd_open import setup_open_parser
from tasknotes.cli.cmd_active import setup_active_parser
from tasknotes.cli.cmd_close import setup_close_parser
from tasknotes.cli.cmd_done import setup_done_parser
from tasknotes.cli.cmd_tag import setup_tag_parser
from tasknotes.cli.cmd_search import setup_search_parser
from tasknotes.cli.cmd_help import setup_help_parser
from tasknotes.cli.cmd_mcp import setup_mcp_parser


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
    """Register command implementations with the command factory."""
    # Register command implementations
    cmd_factory.register_cmd("init", InitCmd)
    # TODO: Register other command implementations


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
        
        # Check if any command failed
        for result in results:
            if not result.success:
                print(f"Error: {result.message}", file=sys.stderr)
                sys.exit(result.exit_code or 1)

if __name__ == "__main__":
    main()
