"""Command module for 'tag' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


def setup_tag_parser(subparsers: Any) -> None:
    """Set up the parser for the 'tag' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "tag",
        help=_("Manage task tags"),
        description=_("Add, list, or replace tags for a task.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "task_id",
        metavar="TASK_ID",
        nargs="?",
        help=_("Task ID to manage tags for (defaults to current active task)")
    )
    
    parser.add_argument(
        "--tag", "-t",
        action="append",
        metavar="TAG",
        help=_("Tag to add to the task (can be specified multiple times)")
    )
    
    parser.add_argument(
        "--replace",
        action="store_true",
        help=_("Replace existing tags instead of adding to them")
    )
    
    parser.add_argument(
        "--group", "-g",
        metavar="GROUP",
        help=_("Tag group to add tags to or list tags from")
    )
    
    parser.add_argument(
        "--ordered", "-o",
        action="store_true",
        help=_("Mark the tag group as ordered (default is unordered)")
    )


# The _ function is imported from i18n module
