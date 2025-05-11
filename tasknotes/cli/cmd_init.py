"""Command module for 'init' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _
from tasknotes.cmds.base_cmd import CmdResult


def setup_init_parser(subparsers: Any) -> None:
    """Set up the parser for the 'init' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "init",
        help=_("Initialize a TaskNote repository"),
        description=_("Initialize a new TaskNote repository in the current directory.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "--git",
        action="store_true",
        help=_("Use git backend for storing tasks")
    )


def format_init_result(result: CmdResult, console: Any, rich_available: bool) -> None:
    """Format the result of the init command.
    
    Args:
        result: The CmdResult object to format
        console: The console to print to
        rich_available: Whether Rich is available for enhanced output
    """
    if rich_available:
        # Rich formatting with colors
        if result.data.get("already_initialized", False):
            console.print(f"[yellow]{result.message}[/yellow]")
        else:
            console.print(f"[green]{result.message}[/green]")
    else:
        # Standard output without colors
        print(result.message)
        if not result.data.get("already_initialized", False):
            print(f"Repository path: {result.data.get('path', '')}")


# The _ function is imported from i18n module
