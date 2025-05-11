"""Command module for 'edit' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


def setup_edit_parser(subparsers: Any) -> None:
    """Set up the parser for the 'edit' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "edit",
        help=_("Edit a task"),
        description=_("Open the task in the default editor.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "task_id",
        metavar="TASK_ID",
        help=_("Task ID to edit")
    )


# The _ function is imported from i18n module
