"""Command module for 'active' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


def setup_active_parser(subparsers: Any) -> None:
    """Set up the parser for the 'active' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "active",
        help=_("Manage active tasks"),
        description=_("List active tasks or close tasks above a specified task.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "task_id",
        metavar="TASK_ID",
        nargs="?",
        help=_("Task ID to close tasks above (if not provided, lists all active tasks)")
    )


# The _ function is imported from i18n module
