"""Implementation of the 'init' command."""

import os
from typing import Any, Dict

from tasknotes.cmds.base_cmd import BaseCmd, CmdResult
from tasknotes.core.task_env import TaskNoteEnv


class InitCmd(BaseCmd):
    """Command to initialize a TaskNote repository."""
    
    def execute(self, cmd_service: 'CmdService', task_env: TaskNoteEnv) -> CmdResult:
        """Execute the init command.
        
        Args:
            cmd_service: The command service to use for executing additional commands
            task_env: The task environment providing access to task data and services
            
        Returns:
            CmdResult: The result of the command execution
        """
        # Determine the initialization mode based on the git flag
        use_git = self.args.get("git", False)
        mode = "GIT" if use_git else "LOCAL"
        
        # Check if already initialized
        if task_env.is_tasknote_init():
            return CmdResult(
                success=True,
                message=f"TaskNote repository already initialized",
                data={
                    "git": use_git,
                    "already_initialized": True
                }
            )
        
        # Initialize the repository
        try:
            success = task_env.tasknote_init(mode=mode)
            
            if success:
                return CmdResult(
                    success=True,
                    message=f"Initialized TaskNote repository with {'git' if use_git else 'local'} backend",
                    data={
                        "git": use_git,
                        "mode": mode,
                        "path": str(task_env.repo_path)
                    }
                )
            else:
                return CmdResult(
                    success=False,
                    message=f"Failed to initialize TaskNote repository with {'git' if use_git else 'local'} backend",
                    data={"git": use_git},
                    exit_code=1
                )
        except Exception as e:
            return CmdResult(
                success=False,
                message=f"Error initializing TaskNote repository: {str(e)}",
                data={"git": use_git, "error": str(e)},
                exit_code=1
            )
