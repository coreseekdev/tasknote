"""Command module for 'help' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


def setup_help_parser(subparsers: Any) -> None:
    """Set up the parser for the 'help' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "help",
        help=_("Show help information"),
        description=_("Show help information for TaskNote commands.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "command",
        nargs="?",
        help=_("Command to show help for")
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help=_("Show detailed help for all commands")
    )
    
    parser.add_argument(
        "--format",
        choices=["text", "markdown", "man"],
        default="text",
        help=_("Output format (default: text)")
    )


# The _ function is imported from i18n module
