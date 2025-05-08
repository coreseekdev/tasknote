"""Command-line interface for TaskNotes."""

import os
import sys
from typing import List, Optional, Dict, Any

import click
from rich.console import Console

from tasknotes.core import TaskManager
from tasknotes.core import Config

console = Console()


@click.group()
@click.version_option()
def cli() -> None:
    """TaskNotes - A task management tool using markdown."""
    pass


@cli.command()
@click.option(
    "--status", "-s", 
    type=click.Choice(["all", "open", "closed", "in-progress"]), 
    default="all",
    help="Filter tasks by status"
)
def list(status: str) -> None:
    """List tasks with optional status filtering."""
    try:
        task_manager = TaskManager()
        tasks = task_manager.list_tasks(status=status)
        
        if not tasks:
            console.print(f"No {status} tasks found.")
            return
            
        console.print(f"[bold green]{len(tasks)} {status} tasks found:[/bold green]")
        for i, task in enumerate(tasks, 1):
            status_color = {
                "open": "yellow",
                "closed": "green",
                "in-progress": "blue"
            }.get(task.status, "white")
            
            console.print(
                f"[bold]{i}.[/bold] "
                f"[bold {status_color}]{task.title}[/bold {status_color}] "
                f"({task.status}) - {task.created_at.strftime('%Y-%m-%d')}"
            )
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument("title")
@click.option("--description", "-d", help="Task description")
def add(title: str, description: Optional[str] = None) -> None:
    """Add a new task."""
    try:
        task_manager = TaskManager()
        task = task_manager.add_task(title=title, description=description)
        console.print(f"[bold green]Task added:[/bold green] {task.title}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument("task_id")
@click.option(
    "--status", "-s",
    type=click.Choice(["open", "closed", "in-progress"]),
    help="Update task status"
)
@click.option("--title", "-t", help="Update task title")
@click.option("--description", "-d", help="Update task description")
def update(
    task_id: str, 
    status: Optional[str] = None, 
    title: Optional[str] = None, 
    description: Optional[str] = None
) -> None:
    """Update an existing task."""
    try:
        task_manager = TaskManager()
        
        updates: Dict[str, Any] = {}
        if status:
            updates["status"] = status
        if title:
            updates["title"] = title
        if description:
            updates["description"] = description
            
        if not updates:
            console.print("[yellow]No updates provided.[/yellow]")
            return
            
        task = task_manager.update_task(task_id=task_id, **updates)
        console.print(f"[bold green]Task updated:[/bold green] {task.title}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument("task_id")
def show(task_id: str) -> None:
    """Show details of a specific task."""
    try:
        task_manager = TaskManager()
        task = task_manager.get_task(task_id=task_id)
        
        status_color = {
            "open": "yellow",
            "closed": "green",
            "in-progress": "blue"
        }.get(task.status, "white")
        
        console.print(f"[bold]Task ID:[/bold] {task.id}")
        console.print(f"[bold]Title:[/bold] [bold {status_color}]{task.title}[/bold {status_color}]")
        console.print(f"[bold]Status:[/bold] {task.status}")
        console.print(f"[bold]Created:[/bold] {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if task.updated_at:
            console.print(f"[bold]Updated:[/bold] {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
        if task.description:
            console.print("\n[bold]Description:[/bold]")
            console.print(task.description)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument("task_id")
@click.option("--force", "-f", is_flag=True, help="Force deletion without confirmation")
def delete(task_id: str, force: bool = False) -> None:
    """Delete a task."""
    try:
        task_manager = TaskManager()
        task = task_manager.get_task(task_id=task_id)
        
        if not force:
            if not click.confirm(f"Are you sure you want to delete task '{task.title}'?"):
                console.print("[yellow]Deletion cancelled.[/yellow]")
                return
                
        task_manager.delete_task(task_id=task_id)
        console.print(f"[bold green]Task deleted:[/bold green] {task.title}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
