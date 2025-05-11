"""Command module for 'archive' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


def setup_archive_parser(subparsers: Any) -> None:
    """Set up the parser for the 'archive' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "archive",
        help=_("Archive a task"),
        description=_("Archive a task without changing associated note files.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "task_id",
        metavar="TASK_ID",
        help=_("Task ID to archive")
    )
    
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help=_("Automatically confirm archiving incomplete tasks")
    )


# The _ function is imported from i18n module
