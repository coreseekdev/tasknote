"""Command module for 'add' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


def setup_add_parser(subparsers: Any) -> None:
    """Set up the parser for the 'add' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "add",
        help=_("Add a new task"),
        description=_("Add a new task to the current active task.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "description",
        help=_("Task description")
    )
    
    parser.add_argument(
        "--parent",
        metavar="TASK_ID",
        help=_("Parent task ID to add this task to")
    )
    
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help=_("Automatically confirm conversion if target is not a file-based task")
    )
    
    parser.add_argument(
        "--tag", "-t",
        action="append",
        metavar="TAG",
        help=_("Tag to add to the task (can be specified multiple times)")
    )
    
    parser.add_argument(
        "--file", "-f",
        metavar="FILE",
        help=_("Read tasks from file, one per line. Use '-' for stdin")
    )


# The _ function is imported from i18n module
