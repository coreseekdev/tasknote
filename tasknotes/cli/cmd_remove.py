"""Command module for 'remove' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


def setup_remove_parser(subparsers: Any) -> None:
    """Set up the parser for the 'remove' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "remove",
        help=_("Remove a task"),
        description=_("Remove a task and its associated notes.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "task_id",
        metavar="TASK_ID",
        help=_("Task ID to remove")
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help=_("Force removal even if task has notes or subtasks")
    )
    
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help=_("Automatically confirm removal without prompting")
    )


# The _ function is imported from i18n module
