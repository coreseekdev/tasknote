"""Command result formatters for the CLI."""

import json
import sys
from typing import Any, Dict

from tasknotes.cmds.base_cmd import CmdResult


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
            console.print(f"Repository path: [blue]{result.data.get('path', '')}[/blue]")
    else:
        # Standard output without colors
        print(result.message)
        if not result.data.get("already_initialized", False):
            print(f"Repository path: {result.data.get('path', '')}")


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
