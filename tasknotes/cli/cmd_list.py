"""Command module for 'list' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _
from tasknotes.cmds.base_cmd import CmdResult


def setup_list_parser(subparsers: Any) -> None:
    """Set up the parser for the 'list' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "list",
        help=_("List tasks"),
        description=_("List tasks with optional filtering.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "task_ids",
        metavar="TASK_ID",
        nargs="*",
        help=_("Task IDs or 'active' keyword to list tasks (defaults to current active task)")
    )
    
    # Note: The 'active' keyword is handled as a special case in the task_ids argument
    # We'll check for it in the implementation
    
    parser.add_argument(
        "--tag", "-t",
        metavar="TAG",
        help=_("Filter tasks by tag")
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help=_("Include archived tasks in the results")
    )
    
    # Handle the tag_group case
    # This is a bit tricky as it overlaps with task_ids, but we'll handle it in the implementation


def format_list_result(result: CmdResult, console: Any, rich_available: bool) -> None:
    """Format the result of the list command.
    
    Args:
        result: The CmdResult object to format
        console: The console to print to
        rich_available: Whether Rich is available for enhanced output
    """
    if rich_available:
        # Rich table output
        from rich.table import Table
        
        table = Table(title=result.message)
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Status", style="magenta")
        table.add_column("Tags", style="yellow")
        
        for task in result.data.get("tasks", []):
            table.add_row(
                task.get("id", ""),
                task.get("title", ""),
                task.get("status", ""),
                ", ".join(task.get("tags", []))
            )
        
        console.print(table)
    else:
        # Standard table output using plain text
        print(result.message)
        print(f"{'ID':<10} {'Title':<30} {'Status':<10} {'Tags':<20}")
        print("-" * 70)
        
        for task in result.data.get("tasks", []):
            print(
                f"{task.get('id', ''):<10} "
                f"{task.get('title', ''):<30} "
                f"{task.get('status', ''):<10} "
                f"{', '.join(task.get('tags', [])):<20}"
            )


# The _ function is imported from i18n module
