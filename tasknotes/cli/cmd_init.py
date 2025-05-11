"""Command module for 'init' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


def setup_init_parser(subparsers: Any) -> None:
    """Set up the parser for the 'init' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "init",
        help=_("Initialize a TaskNote repository"),
        description=_("Initialize a new TaskNote repository in the current directory.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "--git",
        action="store_true",
        help=_("Use git backend for storing tasks")
    )


# The _ function is imported from i18n module
