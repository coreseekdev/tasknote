"""Command queue package for TaskNotes.

This package provides the infrastructure for handling command queues,
which are used for executing cascading operations like marking tasks as complete.
"""

from tasknotes.cmds.base_cmd import BaseCmd, CmdResult
from tasknotes.cmds.cmd_service import CmdService

__all__ = ["BaseCmd", "CmdResult", "CmdService"]
