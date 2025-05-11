"""Command module for 'list' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


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


# The _ function is imported from i18n module
