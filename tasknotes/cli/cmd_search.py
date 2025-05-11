"""Command module for 'search' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


def setup_search_parser(subparsers: Any) -> None:
    """Set up the parser for the 'search' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "search",
        help=_("Search for tasks"),
        description=_("Search for tasks and notes matching the query.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "query",
        help=_("Search query")
    )
    
    parser.add_argument(
        "--tag", "-t",
        metavar="TAG",
        help=_("Filter results by tag")
    )
    
    parser.add_argument(
        "--in",
        dest="in_task",
        metavar="TASK_ID",
        help=_("Search only within the specified task and its subtasks")
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help=_("Include archived tasks in the search results")
    )


# The _ function is imported from i18n module
