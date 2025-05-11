"""Command module for 'close' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


def setup_close_parser(subparsers: Any) -> None:
    """Set up the parser for the 'close' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "close",
        help=_("Close active tasks"),
        description=_("Close the most recent active task or all tasks above a specified task.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "task_id",
        metavar="TASK_ID",
        nargs="?",
        help=_("Task ID to close tasks above (if not provided, closes the most recent active task)")
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help=_("Close all active tasks")
    )


# The _ function is imported from i18n module
