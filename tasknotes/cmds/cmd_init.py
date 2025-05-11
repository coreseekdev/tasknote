"""Implementation of the 'init' command."""

import os
from typing import Any, Dict

from tasknotes.cmds.base_cmd import BaseCmd, CmdResult
from tasknotes.core.task_env import TaskNoteEnv


class InitCmd(BaseCmd):
    """Command to initialize a TaskNote repository."""
    
    def _execute_impl(self, cmd_service: 'CmdService', task_env: TaskNoteEnv) -> CmdResult:
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
        
        # First explicitly check if already initialized
        # This provides a clearer semantic distinction between already initialized and new initialization
        if task_env.is_tasknote_init():
            # Get the current mode (GIT or LOCAL) for better reporting
            current_mode = "GIT" if task_env.is_git_repo() and task_env.has_tasknote_branch() else "LOCAL"
            return CmdResult(
                success=True,
                message=f"TaskNote repository already initialized in {current_mode} mode",
                data={
                    "git": current_mode == "GIT",
                    "mode": current_mode,
                    "already_initialized": True,
                    "path": str(task_env.repo_path)
                }
            )
        
        # Initialize the repository only if not already initialized
        success, error_msg = task_env.tasknote_init(mode=mode)
        
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
            # Use the error message returned from tasknote_init
            return CmdResult(
                success=False,
                message=f"Failed to initialize TaskNote repository: {error_msg}",
                data={
                    "git": use_git,
                    "error": error_msg
                },
                exit_code=1
            )
