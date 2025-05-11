"""Command module for 'search' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _
from tasknotes.cmds.base_cmd import CmdResult


def setup_search_parser(subparsers: Any) -> None:
    """Set up the parser for the 'search' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "search",
        help=_("Search for tasks"),
        description=_("Search for tasks and notes matching the query.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "query",
        help=_("Search query")
    )
    
    parser.add_argument(
        "--tag", "-t",
        metavar="TAG",
        help=_("Filter results by tag")
    )
    
    parser.add_argument(
        "--in",
        dest="in_task",
        metavar="TASK_ID",
        help=_("Search only within the specified task and its subtasks")
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help=_("Include archived tasks in the search results")
    )


def format_search_result(result: CmdResult, console: Any, rich_available: bool) -> None:
    """Format the result of the search command.
    
    Args:
        result: The CmdResult object to format
        console: The console to print to
        rich_available: Whether Rich is available for enhanced output
    """
    if rich_available:
        # Rich formatting with tables
        from rich.table import Table
        
        console.print(f"[green]{result.message}[/green]")
        
        # Show tasks in a table
        if result.data.get("tasks"):
            task_table = Table(title="Matching Tasks")
            task_table.add_column("ID", style="cyan")
            task_table.add_column("Title", style="green")
            task_table.add_column("Status", style="magenta")
            
            for task in result.data.get("tasks", []):
                task_table.add_row(
                    task.get("id", ""),
                    task.get("title", ""),
                    task.get("status", "")
                )
            
            console.print(task_table)
        
        # Show notes in a separate table
        if result.data.get("notes"):
            note_table = Table(title="Matching Notes")
            note_table.add_column("Task ID", style="cyan")
            note_table.add_column("Category", style="magenta")
            note_table.add_column("Content", style="green")
            
            for note in result.data.get("notes", []):
                note_table.add_row(
                    note.get("task_id", ""),
                    note.get("category", ""),
                    note.get("content", "")
                )
            
            console.print(note_table)
    else:
        # Standard output with plain text tables
        print(result.message)
        
        # Show tasks
        if result.data.get("tasks"):
            print("\nMatching Tasks:")
            print(f"{'ID':<10} {'Title':<30} {'Status':<10}")
            print("-" * 50)
            
            for task in result.data.get("tasks", []):
                print(
                    f"{task.get('id', ''):<10} "
                    f"{task.get('title', ''):<30} "
                    f"{task.get('status', ''):<10}"
                )
        
        # Show notes
        if result.data.get("notes"):
            print("\nMatching Notes:")
            print(f"{'Task ID':<10} {'Category':<15} {'Content':<40}")
            print("-" * 65)
            
            for note in result.data.get("notes", []):
                print(
                    f"{note.get('task_id', ''):<10} "
                    f"{note.get('category', ''):<15} "
                    f"{note.get('content', ''):<40}"
                )


# The _ function is imported from i18n module
