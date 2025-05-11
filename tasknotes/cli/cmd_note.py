"""Command module for 'note' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


def setup_note_parser(subparsers: Any) -> None:
    """Set up the parser for the 'note' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "note",
        help=_("Add notes to a task"),
        description=_("Add or edit notes for a specific task.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "--task",
        metavar="TASK_ID",
        help=_("Task ID to add notes to (defaults to current active task)")
    )
    
    parser.add_argument(
        "--category", "-c",
        metavar="CATEGORY",
        default="notes",
        help=_("Note category (defaults to 'notes')")
    )
    
    parser.add_argument(
        "--message", "-m",
        action="append",
        metavar="MESSAGE",
        help=_("Note content (can be specified multiple times for multi-line notes)")
    )
    
    parser.add_argument(
        "--file", "-f",
        metavar="FILE",
        help=_("Read note content from file")
    )


# The _ function is imported from i18n module
