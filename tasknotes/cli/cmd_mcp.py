"""Command module for 'mcp' command."""

import argparse
from typing import Any

from tasknotes.cli.i18n import _


def setup_mcp_parser(subparsers: Any) -> None:
    """Set up the parser for the 'mcp' command.
    
    Args:
        subparsers: The subparsers object from the main parser
    """
    parser = subparsers.add_parser(
        "mcp",
        help=_("Start MCP server"),
        description=_("Start a Machine Communication Protocol server for LLM API access.")
    )
    
    # Add command-specific arguments
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help=_("Server port (default: 8080)")
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help=_("Server host (default: 127.0.0.1)")
    )
    
    parser.add_argument(
        "--auth",
        metavar="TOKEN",
        help=_("Authentication token for API requests")
    )


# The _ function is imported from i18n module
