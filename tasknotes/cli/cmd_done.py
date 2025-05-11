"""Command module for 'done' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


def setup_done_parser(subparsers: Any) -> None:
    """Set up the parser for the 'done' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "done",
        help=_("Mark a task as done"),
        description=_("Mark a task as completed.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "task_id",
        metavar="TASK_ID",
        nargs="?",
        help=_("Task ID to mark as done (defaults to current active task)")
    )


# The _ function is imported from i18n module
