"""Git integration for TaskNotes."""

import os
import subprocess
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path


class GitIntegration:
    """Provides integration with Git for TaskNotes."""
    
    @staticmethod
    def is_git_repo(path: Optional[str] = None) -> bool:
        """Check if the current directory is a git repository."""
        try:
            cmd = ["git", "rev-parse", "--is-inside-work-tree"]
            if path:
                cmd.extend(["-C", path])
                
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            return result.returncode == 0 and result.stdout.strip() == "true"
        except Exception:
            return False
    
    @staticmethod
    def get_repo_root(path: Optional[str] = None) -> Optional[str]:
        """Get the root directory of the git repository."""
        if not GitIntegration.is_git_repo(path):
            return None
            
        try:
            cmd = ["git", "rev-parse", "--show-toplevel"]
            if path:
                cmd.extend(["-C", path])
                
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    @staticmethod
    def setup_git_alias() -> bool:
        """Set up the 'git task' alias."""
        try:
            # Check if the alias already exists
            result = subprocess.run(
                ["git", "config", "--global", "--get", "alias.task"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Alias already exists
                return True
                
            # Set up the alias
            subprocess.run(
                ["git", "config", "--global", "alias.task", "!tasknotes"],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def get_current_branch(path: Optional[str] = None) -> Optional[str]:
        """Get the name of the current git branch."""
        if not GitIntegration.is_git_repo(path):
            return None
            
        try:
            cmd = ["git", "branch", "--show-current"]
            if path:
                cmd.extend(["-C", path])
                
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    @staticmethod
    def get_repo_tasks_dir(path: Optional[str] = None) -> Optional[Path]:
        """Get the tasks directory for the current repository."""
        repo_root = GitIntegration.get_repo_root(path)
        if not repo_root:
            return None
            
        # Use .tasks directory in the repository root
        tasks_dir = Path(repo_root) / ".tasks"
        os.makedirs(tasks_dir, exist_ok=True)
        
        return tasks_dir
    
    @staticmethod
    def is_task_tracked(task_path: str) -> bool:
        """Check if a task file is tracked by git."""
        try:
            result = subprocess.run(
                ["git", "ls-files", "--error-unmatch", task_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            return result.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def add_task_to_git(task_path: str) -> bool:
        """Add a task file to git."""
        try:
            subprocess.run(
                ["git", "add", task_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def get_task_history(task_path: str) -> List[Dict[str, Any]]:
        """Get the commit history for a task file."""
        if not GitIntegration.is_task_tracked(task_path):
            return []
            
        try:
            result = subprocess.run(
                [
                    "git", "log", "--pretty=format:%H|%an|%ae|%ad|%s", 
                    "--date=iso", task_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            history = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                    
                parts = line.split("|")
                if len(parts) == 5:
                    history.append({
                        "commit": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "date": parts[3],
                        "message": parts[4]
                    })
            
            return history
        except subprocess.CalledProcessError:
            return []
