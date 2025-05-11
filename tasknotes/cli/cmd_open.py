"""Command module for 'open' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


def setup_open_parser(subparsers: Any) -> None:
    """Set up the parser for the 'open' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "open",
        help=_("Open a task as active"),
        description=_("Set a task as the active task.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "task_id",
        metavar="TASK_ID",
        help=_("Task ID to open as active")
    )


# The _ function is imported from i18n module
